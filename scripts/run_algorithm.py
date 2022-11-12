# !/usr/bin/env python3
# Copyright 2010-2021 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Creates a shift scheduling problem and solves it."""

import operator
from datetime import datetime

from absl import flags
from google.protobuf import text_format
from ortools.sat.python import cp_model

from apps.accounts.models import Employee
from apps.organizations.models import Workplace
from apps.schedules.models import Shift, ShiftType

from scripts.helpers import flatten, get_month_by_weeks, get_letter_for_weekday, floor_to_multiple, ceil_to_multiple
from scripts.context import Context, EmployeeInfo

FLAGS = flags.FLAGS
flags.DEFINE_string('output_proto', 'cp_model.proto', 'Output file to write the cp_model proto to.')
flags.DEFINE_string('params', 'max_time_in_seconds:60.0', 'Sat solver parameters.')


def negated_bounded_span(works, start, length):
    """Filters an isolated sub-sequence of variables assigned to True.

  Extract the span of Boolean variables [start, start + length), negate them,
  and if there is variables to the left/right of this span, surround the span by
  them in non negated form.

  Args:
    works: a list of variables to extract the span from.
    start: the start to the span.
    length: the length of the span.

  Returns:
    a list of variables which conjunction will be false if the sub-list is
    assigned to True, and correctly bounded by variables assigned to False,
    or by the start or end of works.
  """
    sequence = []
    # Left border (start of works, or works[start - 1])
    if start > 0:
        sequence.append(works[start - 1])
    for i in range(length):
        sequence.append(works[start + i].Not())
    # Right border (end of works or works[start + length])
    if start + length < len(works):
        sequence.append(works[start + length])
    return sequence


def add_soft_sequence_constraint(model, works, hard_min, soft_min, min_cost,
                                 soft_max, hard_max, max_cost, prefix):
    """Sequence constraint on true variables with soft and hard bounds.

  This constraint look at every maximal contiguous sequence of variables
  assigned to true. If forbids sequence of length < hard_min or > hard_max.
  Then it creates penalty terms if the length is < soft_min or > soft_max.

  Args:
    model: the sequence constraint is built on this model.
    works: a list of Boolean variables.
    hard_min: any sequence of true variables must have a length of at least
      hard_min.
    soft_min: any sequence should have a length of at least soft_min, or a
      linear penalty on the delta will be added to the objective.
    min_cost: the coefficient of the linear penalty if the length is less than
      soft_min.
    soft_max: any sequence should have a length of at most soft_max, or a linear
      penalty on the delta will be added to the objective.
    hard_max: any sequence of true variables must have a length of at most
      hard_max.
    max_cost: the coefficient of the linear penalty if the length is more than
      soft_max.
    prefix: a base name for penalty literals.

  Returns:
    a tuple (variables_list, coefficient_list) containing the different
    penalties created by the sequence constraint.
  """
    cost_literals = []
    cost_coefficients = []

    # Forbid sequences that are too short.
    for length in range(1, hard_min):
        for start in range(len(works) - length + 1):
            model.AddBoolOr(negated_bounded_span(works, start, length))

    # Penalize sequences that are below the soft limit.
    if min_cost > 0:
        for length in range(hard_min, soft_min):
            for start in range(len(works) - length + 1):
                span = negated_bounded_span(works, start, length)
                name = ': under_span(start=%i, length=%i)' % (start, length)
                lit = model.NewBoolVar(prefix + name)
                span.append(lit)
                model.AddBoolOr(span)
                cost_literals.append(lit)
                # We filter exactly the sequence with a short length.
                # The penalty is proportional to the delta with soft_min.
                cost_coefficients.append(min_cost * (soft_min - length))

    # Penalize sequences that are above the soft limit.
    if max_cost > 0:
        for length in range(soft_max + 1, hard_max + 1):
            for start in range(len(works) - length + 1):
                span = negated_bounded_span(works, start, length)
                name = ': over_span(start=%i, length=%i)' % (start, length)
                lit = model.NewBoolVar(prefix + name)
                span.append(lit)
                model.AddBoolOr(span)
                cost_literals.append(lit)
                # Cost paid is max_cost * excess length.
                cost_coefficients.append(max_cost * (length - soft_max))

    # Just forbid any sequence of true variables with length hard_max + 1
    for start in range(len(works) - hard_max):
        model.AddBoolOr(
            [works[i].Not() for i in range(start, start + hard_max + 1)])
    return cost_literals, cost_coefficients


def add_weekly_soft_sum_constraint(model, works, hard_min, soft_min, min_cost,
                                   soft_max, hard_max, max_cost, prefix):
    """Sum constraint with soft and hard bounds.

  This constraint counts the variables assigned to true from works.
  If forbids sum < hard_min or > hard_max.
  Then it creates penalty terms if the sum is < soft_min or > soft_max.

  Args:
    model: the sequence constraint is built on this model.
    works: a list of Boolean variables.
    hard_min: any sequence of true variables must have a sum of at least
      hard_min.
    soft_min: any sequence should have a sum of at least soft_min, or a linear
      penalty on the delta will be added to the objective.
    min_cost: the coefficient of the linear penalty if the sum is less than
      soft_min.
    soft_max: any sequence should have a sum of at most soft_max, or a linear
      penalty on the delta will be added to the objective.
    hard_max: any sequence of true variables must have a sum of at most
      hard_max.
    max_cost: the coefficient of the linear penalty if the sum is more than
      soft_max.
    prefix: a base name for penalty variables.

  Returns:
    a tuple (variables_list, coefficient_list) containing the different
    penalties created by the sequence constraint.
  """
    cost_variables = []
    cost_coefficients = []
    sum_var = model.NewIntVar(hard_min, hard_max, '')
    # This adds the hard constraints on the sum.
    model.Add(sum_var == sum(works))

    # Penalize sums below the soft_min target.
    if soft_min > hard_min and min_cost > 0:
        delta = model.NewIntVar(-len(works), len(works), '')
        model.Add(delta == soft_min - sum_var)
        # TODO(user): Compare efficiency with only excess >= soft_min - sum_var.
        excess = model.NewIntVar(0, 7, prefix + ': under_sum')
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(min_cost)

    # Penalize sums above the soft_max target.
    if soft_max < hard_max and max_cost > 0:
        delta = model.NewIntVar(-7, 7, '')
        model.Add(delta == sum_var - soft_max)
        excess = model.NewIntVar(0, 7, prefix + ': over_sum')
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(max_cost)

    return cost_variables, cost_coefficients


def add_monthly_soft_sum_constraint(model, works, hard_min, soft_min, min_cost,
                                    soft_max, hard_max, max_cost, prefix):
    """Sum constraint with soft and hard bounds.

  This constraint counts the variables assigned to true from works.
  If forbids sum < hard_min or > hard_max.
  Then it creates penalty terms if the sum is < soft_min or > soft_max.

  Args:
    model: the sequence constraint is built on this model.
    works: a list of Boolean variables.
    hard_min: any sequence of true variables must have a sum of at least
      hard_min.
    soft_min: any sequence should have a sum of at least soft_min, or a linear
      penalty on the delta will be added to the objective.
    min_cost: the coefficient of the linear penalty if the sum is less than
      soft_min.
    soft_max: any sequence should have a sum of at most soft_max, or a linear
      penalty on the delta will be added to the objective.
    hard_max: any sequence of true variables must have a sum of at most
      hard_max.
    max_cost: the coefficient of the linear penalty if the sum is more than
      soft_max.
    prefix: a base name for penalty variables.

  Returns:
    a tuple (variables_list, coefficient_list) containing the different
    penalties created by the sequence constraint.
  """
    cost_variables = []
    cost_coefficients = []
    sum_var = model.NewIntVar(hard_min, hard_max, '')
    # This adds the hard constraints on the sum.
    model.Add(sum_var == sum(works))

    # Penalize sums below the soft_min target.
    if soft_min > hard_min and min_cost > 0:
        delta = model.NewIntVar(-len(works), len(works), '')
        model.Add(delta == soft_min - sum_var)
        # TODO(user): Compare efficiency with only excess >= soft_min - sum_var.
        excess = model.NewIntVar(0, num_days, prefix + ': under_sum')
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(min_cost)

    # Penalize sums above the soft_max target.
    if soft_max < hard_max and max_cost > 0:
        delta = model.NewIntVar(-num_days, num_days, '')
        model.Add(delta == sum_var - soft_max)
        excess = model.NewIntVar(0, num_days, prefix + ': over_sum')
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(max_cost)

    return cost_variables, cost_coefficients


def solve_shift_scheduling(emp_for_workplaces, emp_preferences, emp_absences, schedule_dict, employees: list[Employee], shift_types: list[ShiftType], year: int,
                           month: int, params, output_proto):

    # Dictionaries with:
    work_time = dict()          # with work time assigned for each employee (key is emp.pk)
    num_emp_absences = dict()   # with number of absent days for each employee (key is emp.pk)

    # TODO: check if below filtering can be done while creating emp_info

    for e in employees:
        if e.pk not in emp_preferences:
            emp_preferences[e.pk] = []
        if e.pk not in emp_absences:
            emp_absences[e.pk] = []
        work_time[e.pk] = 0
        num_emp_absences[e] = 0

    emp_info = [EmployeeInfo(e,
                             [wp for wp in emp_for_workplaces if e in emp_for_workplaces[wp]],
                             emp_preferences[e.pk],
                             emp_absences[e.pk])
                for e in employees]

    for e in emp_info:
        print(e)

    ctx = Context(emp_info, shift_types, year, month)

    for ei in ctx.employees:
        num_emp_absences[ei.get()] = sum(1 for x in ei.get_absent_days_in_month(month))

    # Sanitize employee list by absences
    ctx.employees = [ei for ei in ctx.employees if num_days > num_emp_absences[ei.get()]]

    # Shift constraints on continuous sequence :
    #     (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
    shift_constraints = [
        # One or two consecutive days of rest, this is a hard constraint.
        (0, 1, 1, 0, 2, 2, 0),
    ]

    # Weekly sum constraints on shifts days:
    #     (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
    weekly_sum_constraints = [
        # Constraints on rests per week.
        (0, 1, 2, 7, 2, 4, 4)
    ]

    # Overnight shift constraints
    # TODO: add constraints for combinations between different night shift types
    shift_constraints.extend(ctx.overnight_shifts[0])
    weekly_sum_constraints.extend(ctx.overnight_shifts[1])

    # Penalized transitions:
    #     (previous_shift, next_shift, penalty (0 means forbidden))
    penalized_transitions = ctx.illegal_transitions

    # Penalty for exceeding the cover constraint per shift type.
    excess_cover_penalties = tuple(30 for x in range(len(ctx.shift_types) - 1))

    model = cp_model.CpModel()

    print("\nJob time   : %3i\nWork time  : %3i\nJT ratio   : %.3f\nOT ratio   : %.3f\n" %
          (ctx.total_job_time, ctx.total_work_time, ctx.job_time_multiplier, ctx.overtime_multiplier))

    work = {}
    for ei in ctx.employees:
        for s in ctx.shift_types:
            for d in range(1, num_days + 1):
                work[ei.employee.pk, s.id, d] = model.NewBoolVar('work%i_%i_%i' % (ei.employee.pk, s.id, d))

    # Linear terms of the objective in a minimization context.
    obj_int_vars = []
    obj_int_coeffs = []
    obj_bool_vars = []
    obj_bool_coeffs = []

    # Exactly one shift per day.
    for ei in ctx.employees:
        for d in range(1, num_days + 1):
            model.AddExactlyOne(work[ei.employee.pk, s.id, d] for s in ctx.shift_types)
            for s in ctx.shift_types[1:]:
                if s.shift_type.workplace.id not in ei.workplaces:  # filter shifts by workplaces
                    model.Add(work[ei.employee.pk, s.id, d] == 0)

    # Fixed assignments.
    for e, s, d in ctx.fixed_assignments:
        model.Add(work[e, s, d] == 1)

    # Employee requests
    for e, s, d, w in ctx.requests:
        obj_bool_vars.append(work[e, s, d])
        obj_bool_coeffs.append(w)

    # Shift constraints
    for ct in shift_constraints:
        shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for ei in ctx.employees:
            works = [work[ei.get().pk, shift, d] for d in range(1, num_days + 1)]

            if shift == 0:
                absences = ei.get_absent_days_in_month(month)
                for ab in absences:
                    del works[ab]

            variables, coeffs = add_soft_sequence_constraint(
                model, works, hard_min, soft_min, min_cost, soft_max, hard_max,
                max_cost,
                'shift_constraint(employee %i, shift %i)' % (ei.get().pk, shift))
            obj_bool_vars.extend(variables)
            obj_bool_coeffs.extend(coeffs)

    # Calculate work time constraints
    for ei in ctx.employees:
        works = [work[ei.get().pk, s.id, d] for s in ctx.shift_types[1:] for d in range(1, num_days + 1)]
        hard_min = floor_to_multiple(ei.get().job_time * ctx.job_time_multiplier, 8)
        soft_min = ei.get().job_time
        min_cost = 50
        soft_max = ei.get().job_time
        hard_max = 160
        max_cost = 50

        if ctx.job_time_multiplier < 1:
            hard_min = floor_to_multiple(ei.get().job_time * ctx.job_time_multiplier, 8) - 8
            soft_min = floor_to_multiple(ei.get().job_time * ctx.job_time_multiplier, 8)
            soft_max = ceil_to_multiple(ei.get().job_time * ctx.job_time_multiplier, 8)
            hard_max = ei.get().job_time + 8
        if ctx.job_time_multiplier >= 1:
            hard_min = ei.get().job_time - 8
            soft_min = floor_to_multiple(ei.get().job_time * ctx.overtime_multiplier, 8)
            soft_max = ceil_to_multiple(ei.get().job_time * ctx.overtime_multiplier, 8)
            hard_max = soft_max + 8
            if ei.get().job_time == 160:
                soft_min = soft_max
                min_cost += 25

        soft_min = min(152, soft_min) if ei.get().job_time != 160 else min(160, soft_min)
        soft_max = min(160, soft_max)
        hard_max = min(160, hard_max)

        print("emp %2i, jt %3i, hard_min %3i, soft_min %3i, soft_max %3i, hard_max %3i, overtime: %2i" %
              (ei.get().pk, ei.get().job_time, hard_min, soft_min, soft_max, hard_max, soft_max - ei.get().job_time))
        variables, coeffs = add_monthly_soft_sum_constraint(
            model, works, hard_min // 8, soft_min // 8, min_cost, soft_max // 8,
            hard_max // 8, max_cost,
            'work_time_constraint(employee %i, job_time %i)' %
            (ei.get().pk, ei.get().job_time))
        obj_int_vars.extend(variables)
        obj_int_coeffs.extend(coeffs)

    # Weekly sum constraints
    # BUG: when dealing with 6 week months, the algorithm fails because of this constraint
    for ct in weekly_sum_constraints:
        for ei in ctx.employees:
            for w, week in enumerate(ctx.month_by_weeks):
                if len(week) < 3:  # TODO: this is temporary fix...
                    continue
                shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct

                # Account for absences
                if shift == 0:
                    num_absences = sum(x in ei.get_absent_days_in_month(month) for x in week)

                    if num_absences:
                        print("[weekly constraints] week %i emp %i num_absences %i" % (w, ei.get().pk, num_absences))
                        if num_absences == 7:
                            continue
                        elif num_absences > soft_max:
                            hard_max = min(num_absences + 1, 7)
                            soft_max = min(num_absences, 7)

                works = [work[ei.get().pk, shift, d[0]] for d in week]
                variables, coeffs = add_weekly_soft_sum_constraint(
                    model, works, hard_min, soft_min, min_cost, soft_max,
                    hard_max, max_cost,
                    'weekly_sum_constraint(employee %i, shift %i, week %i)' %
                    (ei.get().pk, shift, w))
                obj_int_vars.extend(variables)
                obj_int_coeffs.extend(coeffs)

    # Penalized transitions
    for previous_shift, next_shift, cost in penalized_transitions:
        for ei in ctx.employees:
            for d in range(1, num_days):
                transition = [work[ei.get().pk, previous_shift, d].Not(), work[ei.get().pk, next_shift, d + 1].Not()]
                if cost == 0:
                    model.AddBoolOr(transition)
                else:
                    trans_var = model.NewBoolVar('transition (employee=%i, day=%i)' % (ei.get().pk, d))
                    transition.append(trans_var)
                    model.AddBoolOr(transition)
                    obj_bool_vars.append(trans_var)
                    obj_bool_coeffs.append(cost)

    # Cover constraints
    for s in ctx.shift_types[1:]:
        for w, week in enumerate(ctx.month_by_weeks):
            for d in week:
                works = [work[ei.get().pk, s.id, d[0]] for ei in ctx.employees]
                # Ignore Off shift.
                demand = ctx.weekly_cover_demands[d[1]][s.id - 1]
                worked = model.NewIntVar(demand, len(ctx.employees), '')
                model.Add(worked == sum(works))
                over_penalty = excess_cover_penalties[s.id - 1]
                if over_penalty > 0:
                    name = 'excess_demand(shift=%i, week=%i, day=%i)' % (s.id, w, d[0])
                    excess = model.NewIntVar(0, len(ctx.employees) - demand, name)
                    model.Add(excess == worked - demand)
                    obj_int_vars.append(excess)
                    obj_int_coeffs.append(over_penalty)

    # Objective
    model.Minimize(
        sum(obj_bool_vars[i] * obj_bool_coeffs[i]
            for i in range(len(obj_bool_vars))) +
        sum(obj_int_vars[i] * obj_int_coeffs[i]
            for i in range(len(obj_int_vars))))

    if output_proto:
        print('Writing proto to %s' % output_proto)
        with open(output_proto, 'w') as text_file:
            text_file.write(str(model))

    print("\nSolving model:")

    # Solve the model.
    solver = cp_model.CpSolver()
    if params:
        text_format.Parse(params, solver.parameters)
    solution_printer = cp_model.ObjectiveSolutionPrinter()
    status = solver.Solve(model, solution_printer)

    def update_working_hours():
        for d in range(1, num_days + 1):
            for s in ctx.shift_types:
                for ei in ctx.employees:
                    if solver.BooleanValue(work[ei.get().pk, s.id, d]):
                        if s.get().name == "-":
                            continue
                        work_time[ei.get().pk] += s.get_duration_in_hours()

    excess_shifts = []

    # Delete excess shifts according to assigned working hours
    def delete_excess_shifts():
        s_excess_shifts = dict()
        job_times = sorted(set(ei.get().job_time for ei in ctx.employees), reverse=True)

        for s, d, v in excess_shifts:
            candidates = [[ei.get(), s, d] for ei in ctx.employees if solver.BooleanValue(work[ei.get().pk, s, d])]
            s_excess_shifts[(s, d, v)] = [[c[0].job_time for c in candidates].count(jt) for jt in job_times]

        excess_full_timers = {k: v for k, v in s_excess_shifts.items() if sum(v) == v[0]}
        excess_rest = {k: v for k, v in s_excess_shifts.items() if sum(v) != v[0]}

        sorted_excess_rest = dict(sorted(excess_rest.items(), key=operator.itemgetter(1), reverse=True))

        sorted_excess_shifts = excess_full_timers | sorted_excess_rest

        print("\nPrepared excess shifts:\n", sorted_excess_shifts)

        for s, d, v in sorted_excess_shifts:
            candidates = [[ei.get(), s, d] for ei in ctx.employees if solver.BooleanValue(work[ei.get().pk, s, d])]
            candidates = sorted(sorted(candidates, key=lambda x: x[0].job_time, reverse=True), key=lambda x: work_time[x[0].pk] - x[0].job_time)

            for c in candidates:
                print("employee %d job time %d work time %d diff %d" %
                      (c[0].pk, c[0].job_time, work_time[c[0].pk], work_time[c[0].pk] - c[0].job_time))

            # Step 1
            # See if there are employees who fulfilled their job time
            full_timers = list(filter(lambda x: work_time[x[0].pk] > x[0].job_time, candidates))

            if full_timers != candidates:
                if len(full_timers) > 0:
                    for ft in full_timers:
                        candidates.remove(ft)

                # Delete their excess shifts
                while len(full_timers) > 0:
                    em, sh, da = full_timers.pop(0)
                    print('[EXCESS FULL TIMER] Deleted shift: \'%s\' for employee %d with job time of %d and work time %d on day %d'
                          % (ctx.get_shift_info_by_id(sh).get().name, em.pk, em.job_time, work_time[em.pk], da))
                    work[em.pk, sh, da] = 0
                    work[em.pk, 0, da] = 1
                    v -= 1
                    work_time[em.pk] -= ctx.get_shift_info_by_id(sh).get_duration_in_hours()

            # TODO: sprawdzać czy są pracownicy z pełnym etatem o diffie 0
            #  jeśli tak: z większym priorytetem usuwać ludzi o mniejszym etacie nawet przy ujemnym diffie!!

            # Step 2
            # Sort employees by their work time and remove shifts evenly

            candidates.pop(0)
            # winner = candidates.pop(0)
            # print(f'Candidate with the lowest work time: {winner}, {work_time[winner[0].pk]}')  # pop candidate with the lowest work time

            while len(candidates) > 0:  # delete all the other candidates
                em, sh, da = candidates.pop(0)
                print('Deleted shift: \'%s\' for employee %d with job time of %d and work time %d on day %d'
                      % (ctx.get_shift_info_by_id(sh).get().name, em.pk, em.job_time, work_time[em.pk], da))
                work[em.pk, sh, da] = 0
                work[em.pk, 0, da] = 1  # add free shift in place of deleted shift
                v -= 1
                work_time[em.pk] -= ctx.get_shift_info_by_id(sh).get_duration_in_hours()

            if v < 0:
                raise ValueError(f'All of {s} shifts for day:{d} have been deleted. This should not ever happen.')
            elif v > 0:
                raise ValueError(f'There is still {v} excess demand for shift{ctx.get_shift_info_by_id(s).name} on day{d}.\nList of excess shifts:{candidates}')

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        update_working_hours()

        print('\nPenalties:')
        for i, var in enumerate(obj_bool_vars):
            if solver.BooleanValue(var):
                penalty = obj_bool_coeffs[i]
                if penalty > 0:
                    print('  %s violated, penalty=%i' % (var.Name(), penalty))
                else:
                    print('  %s fulfilled, gain=%i' % (var.Name(), -penalty))

        for i, var in enumerate(obj_int_vars):
            if solver.Value(var) > 0:
                print('  %s violated by %i, linear penalty=%i' %
                      (var.Name(), solver.Value(var), obj_int_coeffs[i]))
                if var.Name().startswith('excess_demand'):  # TODO: DO SOMETHING TO AVOID THIS ABOMINABLE CRINGEFEST
                    s = int(var.Name()[var.Name().find('t=') + 2:].split(',')[0])
                    d = int(var.Name()[var.Name().find('y=') + 2:].split(')')[0])
                    v = solver.Value(var)
                    excess_shifts.append((s, d, v))

        delete_excess_shifts()

        header = '\n' + ' ' * 13
        for w, week in enumerate(ctx.month_by_weeks):
            for d in week:
                header += get_letter_for_weekday(d[1]) + ' '
            header += '  '
        print(header)

        for ei in ctx.employees:
            sched = ''
            for d in range(1, num_days + 1):
                if d % 7 == 0:
                    sched += '  '
                for s in ctx.shift_types:
                    if solver.BooleanValue(work[ei.get().pk, s.id, d]):
                        sched += s.get().name[0] + ' '
            print('employee %i: %s | JT: %3i | WT: %3i | RATIO: %.1f' %
                  (ei.get().pk, sched, ei.get().job_time, work_time[ei.get().pk],
                   work_time[ei.get().pk] / ei.get().job_time))

        print('\n%sTOTALS | JT: %3i | WT: %3i | JT RATIO: %.3f \n%s | OT RATIO: %.3f' %
              (' ' * 75, ctx.total_work_time, ctx.total_job_time, ctx.job_time_multiplier, ' ' * 101, ctx.overtime_multiplier))

    # We only return a list of shift objects
    def output_inflate():
        output_shifts = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for ei in ctx.employees:
                for d in range(1, num_days + 1):
                    for s in ctx.shift_types[1:]:
                        if solver.BooleanValue(work[ei.get().pk, s.id, d]):
                            output_shifts.append(
                                Shift(date=datetime(year, month, d).date(),
                                      schedule=schedule_dict[s.get().workplace.id],
                                      employee=ei.get(),
                                      shift_type=s.get()))
        return output_shifts

    print('Statistics:')
    print('  - status           : %s' % solver.StatusName(status))
    print('  - conflicts        : %i' % solver.NumConflicts())
    print('  - branches         : %i' % solver.NumBranches())
    print('  - wall time (sec.) : %f' % solver.WallTime())

    return output_inflate()


def main_algorithm(schedule_dict, emp, shift_types, year, month, emp_for_workplaces, emp_preferences, emp_absences):
    workplace = Workplace.objects.all().first()

    active_days = '1111111'

    # Calendar data
    global num_days
    num_days = get_month_by_weeks(year, month)[-1][-1][0]

    shift_free = ShiftType(hour_start=datetime.time(datetime.strptime('00:00', '%H:%M')),
                           hour_end=datetime.time(datetime.strptime('00:00', '%H:%M')),
                           name='-', workplace=workplace, active_days=active_days,
                           is_used=True, is_archive=False)
    shift_types.insert(0, shift_free)

    # Only consider employees with set job time
    emp = [e for e in emp if e.job_time != 0]

    # Sort employees by their job time
    emp = sorted(emp, key=lambda e: e.job_time, reverse=True)

    # TODO: Only consider absences for considered month (filter data from backend)

    data = solve_shift_scheduling(emp_for_workplaces,
                                  emp_preferences,
                                  emp_absences,
                                  schedule_dict,
                                  emp,  # employee list
                                  shift_types,  # shift type list
                                  year, month,  # date
                                  params='max_time_in_seconds:60.0', output_proto=None)
    return data
