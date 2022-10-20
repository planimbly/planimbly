# To run main_test_algorithm use: python manage.py runscript run_algorithm --script-args test

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

import calendar
from datetime import datetime, timedelta

import operator

from absl import app, flags
from google.protobuf import text_format
from ortools.sat.python import cp_model

from apps.accounts.models import Employee
from apps.organizations.models import Workplace
from apps.schedules.models import Shift, ShiftType, Schedule

FLAGS = flags.FLAGS
flags.DEFINE_string('output_proto', 'cp_model.proto',
                    'Output file to write the cp_model proto to.')
flags.DEFINE_string('params', 'max_time_in_seconds:30.0',
                    'Sat solver parameters.')


def negated_bounded_span(works, start, length):
    """Filters an isolated sub-sequence of variables assined to True.

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

    # print("Sum_works:", sum(works))
    # print("sum_var:", sum_var)
    # print("Compare:", sum_var == sum(works))

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

    # print("Sum_works:", sum(works))
    # print("sum_var:", sum_var)
    # print("Compare:", sum_var == sum(works))

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


def get_month_by_weeks(year: int, month: int):
    """Returns list of lists containing days of given month

    Sublists contain days of given week (the last element of every sublist is either a sunday or the last day of the month)

    Days are stored in a tuple:
    day - (day, weekday)
    """
    cal = calendar.Calendar()
    x = cal.monthdays2calendar(year, month)
    x = [list(filter(lambda item: item[0] != 0, week)) for week in x]
    return x


def flatten(t: list):
    return [item for sublist in t for item in sublist]


# NOTE: * kiedyś może trzeba będzie poeksperymentować z karami za nocki, lub damy ustawić to użytkownikowi
#       * na razie to działa poprawnie tylko w przypadku gdy jest tylko jedna nocna zmiana
# TODO: przerobić funkcję do weekly constraintów żeby mogła przyjmować sumę shiftów
def find_overnight_shifts(shifts: list[ShiftType]):
    """Determines which shifts are happening overnight
    Returns a tuple of given structure for each overnight shift constraint:
    (shift, hard_min, soft_min, min_penalty,
            soft_max, hard_max, max_penalty)
    """
    sc = []
    wsc = []
    for i in range(1, len(shifts)):
        start = shifts[i].hour_start.hour
        end = shifts[i].hour_end.hour
        if end < start:
            print(f"Found overnight shift: {shifts[i].name}")
            # between 2 and 3 consecutive days of night shifts, 1 and 4 are possible but penalized.
            sc.append((i, 1, 2, 20, 3, 4, 5))
            # At least 1 night shift per week (penalized). At most 4 (hard).
            wsc.append((i, 0, 1, 3, 4, 4, 0))
    return sc, wsc


# TODO: opracować ustawianie kar za nieoptymalne (???) przejścia
def find_illegal_transitions(shifts: list[ShiftType]):
    """Finds illegal transitions between shift types
    Returns a list of tuples of given structure:
    (i, j, p)
    i - index of shift that is transitioning to 'j'
    j - index of shift that 'i' transitions to
    p - penalty of transition between shift 'i' to shift 'j'
    """
    it = []
    for i in range(1, len(shifts)):
        i_start = datetime.strptime("1970-01-01" + shifts[i].hour_start.strftime('%H:%M'), "%Y-%m-%d%H:%M")
        i_delta = datetime.strptime(shifts[i].hour_end.strftime('%H:%M'), "%H:%M") - datetime.strptime(
            shifts[i].hour_start.strftime('%H:%M'), "%H:%M")
        min = i_delta.seconds // 60
        # print(f"{shifts[i].name} working time: {h}")
        i_end = i_start + timedelta(minutes=min)  # do all of above in case of overnight shifts
        for j in range(1, len(shifts)):
            if i == j:
                continue
            j_start = datetime.strptime("1970-01-02" + shifts[j].hour_start.strftime('%H:%M'), "%Y-%m-%d%H:%M")
            dt = j_start - i_end
            dt = int(dt.total_seconds() // 60)
            # print(f"dt between {shifts[i].name} and {shifts[j].name} is {dt}")
            # print(f"{i_end} to {j_start}")
            if dt < (11 * 60):  # break between i and j is below 11 hours
                print(f"Found illegal transition: {shifts[i].name} to {shifts[j].name}")
                it.append((i, j, 0))
    return it


# TODO: zmienić wszystkie jednostki czasu pracy z godzin na minuty (np. w przypadku połówek godzin)
def get_shift_work_time(shift_type: ShiftType):
    work_time = datetime.strptime(shift_type.hour_end.strftime('%H:%M'), "%H:%M") - datetime.strptime(shift_type.hour_start.strftime('%H:%M'), "%H:%M")
    return work_time.seconds // 60


def solve_shift_scheduling(emp_for_workplaces, schedule_dict, employees: list[Employee], shift_types: list[ShiftType], year: int,
                           month: int, params, output_proto):
    """Solves the shift scheduling problem."""


    # Shift data

    num_shifts = len(shift_types)

    # TODO: zrobić z employees listę 2D, która oprócz ID będzie zawierała manualnie przypisane zmiany i preferencje pracownika
    # Fixed assignment: (employee, shift, day).
    # This fixes the first 2 days of the schedule.
    fixed_assignments = []
    """ [
        (0, 0, 0),
        (1, 0, 0),
        (2, 1, 0),
        (3, 1, 0),
        (4, 2, 0),
        (5, 2, 0),
        (6, 2, 3),
        (7, 3, 0),
        (0, 1, 1),
        (1, 1, 1),
        (2, 2, 1),
        (3, 2, 1),
        (4, 2, 1),
        (5, 0, 1),
        (6, 0, 1),
        (7, 3, 1),
    ]"""

    # TODO: zrobić z employees listę 2D, która oprócz ID będzie zawierała manualnie przypisane zmiany i preferencje pracownika
    # Request: (employee, shift, day, weight)
    # A negative weight indicates that the employee desire this assignment.
    requests = [
        # Employee 3 does not want to work on the first Saturday (negative weight
        # for the Off shift).
        # (3, 0, 5, -2),
        # Employee 4 wants a night shift on the second Thursday (negative weight).
        # (4, 3, 10, -2),
        # Employee 2 does not want a night shift on the first Friday (positive
        # weight).
        # (2, 3, 4, 4)
    ]

    # Shift constraints on continuous sequence :
    #     (shift, hard_min, soft_min, min_penalty,
    #             soft_max, hard_max, max_penalty)
    shift_constraints = [
        # One or two consecutive days of rest, this is a hard constraint.
        (0, 1, 1, 0, 2, 2, 0),
        # between 2 and 3 consecutive days of night shifts, 1 and 4 are
        # possible but penalized.
        # (5, 1, 2, 20, 3, 4, 5),
    ]

    # Weekly sum constraints on shifts days:
    #     (shift, hard_min, soft_min, min_penalty,
    #             soft_max, hard_max, max_penalty)
    weekly_sum_constraints = [
        # Constraints on rests per week.
        (0, 1, 2, 7, 2, 3, 4)
        # At least 1 night shift per week (penalized). At most 4 (hard).
        # (5, 0, 1, 3, 4, 4, 0),
    ]

    # Monthly sum constraints on shifts days:
    #     (shift, hard_min, soft_min, min_penalty,
    #             soft_max, hard_max, max_penalty)
    monthly_sum_constraints = [
        (0, 12, 15, 28, 16, 18, 4)
    ]

    # overnight shift constraints
    _os = find_overnight_shifts(shift_types)
    shift_constraints.extend(_os[0])
    weekly_sum_constraints.extend(_os[1])

    # Penalized transitions:
    #     (previous_shift, next_shift, penalty (0 means forbidden))
    penalized_transitions = [
        # Afternoon to night has a penalty of 4.
        # (3, 5, 4),
        # (4, 5, 4),
        # Night to morning is forbidden.
        # (5, 1, 0),
        # (5, 2, 0),
    ]

    penalized_transitions = find_illegal_transitions(shift_types)

    # TODO: zamienić 1 na parametr daily cover demand który będzie w klasie shift_type
    weekly_cover_demands = [tuple(1 for x in range(len(shift_types)-1)) for _ in range(7)]

    num_month_weekdays = []

    for d in range(len(weekly_cover_demands)):
        num_month_weekdays.append(sum([x[1] == d for x in flatten(list_month)]))

    total_hours = int()

    for d in range(len(weekly_cover_demands)):
        for s in range(len(weekly_cover_demands[d])):  # s for num_month_weekdays, s+1 for shift_types
            if shift_types[s+1].name == "-":
                continue
            else:
                total_hours += num_month_weekdays[d] * get_shift_work_time(shift_types[s+1]) // 60

    total_job_time = sum(e.job_time for e in employees)
    job_time_multiplier = total_hours / total_job_time

    for e in employees:
        print("employee %d job time: %d" % (e.pk, e.job_time))
    print("total hours: %d" % total_hours)
    print("total job time: %d" % total_job_time)
    print("job time multiplier: %f" % job_time_multiplier)

    # Penalty for exceeding the cover constraint per shift type.
    excess_cover_penalties = tuple(20 for x in range(len(shift_types)-1))

    model = cp_model.CpModel()

    work = {}
    for e in employees:
        for s in range(num_shifts):
            for d in range(1, num_days + 1):
                work[e.pk, s, d] = model.NewBoolVar('work%i_%i_%i' % (e.pk, s, d))

    # Linear terms of the objective in a minimization context.
    obj_int_vars = []
    obj_int_coeffs = []
    obj_bool_vars = []
    obj_bool_coeffs = []

    # Exactly one shift per day.
    for e in employees:
        for d in range(1, num_days + 1):
            model.AddExactlyOne(work[e.pk, s, d] for s in range(num_shifts))
            for s in range(num_shifts):
                if s != 0 and e not in emp_for_workplaces[shift_types[s].workplace.id]:  # filter shifts by workplaces
                    model.Add(work[e.pk, s, d] == 0)

    # Fixed assignments.
    for e, s, d in fixed_assignments:
        model.Add(work[e.pk, s, d] == 1)

    # Employee requests
    for e, s, d, w in requests:
        obj_bool_vars.append(work[e.pk, s, d])
        obj_bool_coeffs.append(w)

    # Shift constraints
    for ct in shift_constraints:
        shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for e in employees:
            works = [work[e.pk, shift, d] for d in range(1, num_days + 1)]
            variables, coeffs = add_soft_sequence_constraint(
                model, works, hard_min, soft_min, min_cost, soft_max, hard_max,
                max_cost,
                'shift_constraint(employee %i, shift %i)' % (e.pk, shift))
            obj_bool_vars.extend(variables)
            obj_bool_coeffs.extend(coeffs)

    # [WIP] Monthly sum constraints
    # This is supposed to maintain balance between employees desired work time
    # for ct in monthly_sum_constraints:
    #     shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
    for e in employees:
        if e.job_time == 160:
            print("SIEMA 160")
            shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = 0, 6, 7, 100, 8, 9, 100
        elif e.job_time == 80:
            print("SIEMA 80")
            shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = 0, 12, 15, 100, 16, 18, 4
        elif e.job_time == 120:
            print("SIEMA 120")
            shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = 0, 10, 12, 100, 14, 16, 4

        works = [work[e.pk, shift, d] for d in range(1, num_days + 1)]
        variables, coeffs = add_monthly_soft_sum_constraint(
            model, works, hard_min, soft_min, min_cost, soft_max,
            hard_max, max_cost,
            'monthly_sum_constraint(employee %i, job_time %i)' %
            (e.pk, e.job_time))
        obj_int_vars.extend(variables)
        obj_int_coeffs.extend(coeffs)

    # Weekly sum constraints
    # BUG: when dealing with 6 week months, the algorithm fails because of this constraint
    for ct in weekly_sum_constraints:
        shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for e in employees:
            for w, week in enumerate(list_month):
                if len(week) < 3:  # temporary fix..
                    continue
                works = [work[e.pk, shift, d[0]] for d in week]
                variables, coeffs = add_weekly_soft_sum_constraint(
                    model, works, hard_min, soft_min, min_cost, soft_max,
                    hard_max, max_cost,
                    'weekly_sum_constraint(employee %i, shift %i, week %i)' %
                    (e.pk, shift, w))
                obj_int_vars.extend(variables)
                obj_int_coeffs.extend(coeffs)

    # Penalized transitions
    for previous_shift, next_shift, cost in penalized_transitions:
        for e in employees:
            for d in range(1, num_days):
                transition = [
                    work[e.pk, previous_shift, d].Not(), work[e.pk, next_shift,
                                                              d + 1].Not()
                ]
                if cost == 0:
                    model.AddBoolOr(transition)
                else:
                    trans_var = model.NewBoolVar(
                        'transition (employee=%i, day=%i)' % (e.pk, d))
                    transition.append(trans_var)
                    model.AddBoolOr(transition)
                    obj_bool_vars.append(trans_var)
                    obj_bool_coeffs.append(cost)

    # Cover constraints
    for s in range(1, num_shifts):
        for w, week in enumerate(list_month):
            for d in week:
                works = [work[e.pk, s, d[0]] for e in employees]
                # Ignore Off shift.
                demand = weekly_cover_demands[d[1]][s - 1]
                worked = model.NewIntVar(demand, len(employees), '')
                model.Add(worked == sum(works))
                over_penalty = excess_cover_penalties[s - 1]
                if over_penalty > 0:
                    name = 'excess_demand(shift=%i, week=%i, day=%i)' % (s, w, d[0])
                    excess = model.NewIntVar(0, len(employees) - demand, name)
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

    # Solve the model.
    solver = cp_model.CpSolver()
    if params:
        text_format.Parse(params, solver.parameters)
    solution_printer = cp_model.ObjectiveSolutionPrinter()
    status = solver.Solve(model, solution_printer)

    def update_working_hours():
        for e in employees:
            for d in range(1, num_days + 1):
                for s in range(num_shifts):
                    if solver.BooleanValue(work[e.pk, s, d]):
                        shift_type = shift_types[s]
                        if shift_type.name == "-":
                            continue
                        work_time[e.pk] += get_shift_work_time(shift_type)

        # print(work_time)

    excess_shifts = []

    """ # TODO: pomyśleć nad strategią usuwania nadmiarowych shiftów przy implementacji etatowości
    Na razie konflikty shiftowe rozwiązujemy usuwając shift dla pracownika, który ma najwięcej godzin.
    """
    # najpierw zderzajacych sie full timerow obslugujemy
    def delete_excess_shifts():
        s_excess_shifts = dict()
        job_times = sorted(set(e.job_time for e in employees), reverse = True)

        for s, d, v in excess_shifts:
            candidates = [[e, s, d] for e in employees if solver.BooleanValue(work[e.pk, s, d])]
            s_excess_shifts[(s, d, v)] = [[c[0].job_time for c in candidates].count(jt) for jt in job_times]

        excess_full_timers = {k: v for k, v in s_excess_shifts.items() if sum(v) == v[0]}
        excess_rest = {k: v for k, v in s_excess_shifts.items() if sum(v) != v[0]}

        sorted_excess_rest = dict(sorted(excess_rest.items(), key=operator.itemgetter(1), reverse=True))

        sorted_excess_shifts = excess_full_timers | sorted_excess_rest


        for s, d, v in excess_shifts:
            # print(f"{v} excess shift(s): \'{shift_types[s].name}\' on day {d}")
            candidates = [[e, s, d] for e in employees if solver.BooleanValue(work[e.pk, s, d])]

            candidates.sort(key=lambda x: work_time[x[0].pk] // 60 - x[0].job_time)
            for c in candidates:
                print("employee %d job time %d work time %d diff %d" % (c[0].pk, c[0].job_time, work_time[c[0].pk] // 60, work_time[c[0].pk] // 60 - c[0].job_time))

            # Step 1
            # See if there are employees who fulfilled their job time
            full_timers = list(filter(lambda x: work_time[x[0].pk] // 60 >= x[0].job_time, candidates))

            if full_timers != candidates:
                if len(full_timers) > 0:
                    for ft in full_timers:
                        candidates.remove(ft)

                # Delete their shifts
                while len(full_timers) > 0:
                    em, sh, da = full_timers.pop(0)
                    print(f'[FULL TIMER] Deleted shift: \'{shift_types[sh].name}\' for employee {em.pk} with job time of {em.job_time} and work time {work_time[em.pk] // 60} on day {da}')
                    work[em.pk, sh, da] = 0
                    work[em.pk, 0, da] = 1  # add free shift in place of deleted shift
                    v -= 1
                    work_time[em.pk] -= get_shift_work_time(shift_types[sh])

            # Step 2
            # Sort employees by their work time and remove shifts evenly
            candidates.sort(key=lambda x: work_time[x[0].pk])

            candidates.pop(0)
            # winner = candidates.pop(0)
            # print(f'Candidate with the lowest work time: {winner}, {work_time[winner[0].pk]}')  # pop candidate with the lowest work time

            while len(candidates) > 0:  # delete all the other candidates
                em, sh, da = candidates.pop(0)
                print(f'Deleted shift: \'{shift_types[sh].name}\' for employee {em.pk} with job time of {em.job_time} and work time {work_time[em.pk] // 60} on day {da}')
                work[em.pk, sh, da] = 0
                work[em.pk, 0, da] = 1  # add free shift in place of deleted shift
                v -= 1
                work_time[em.pk] -= get_shift_work_time(shift_types[sh])

            if v < 0:
                raise ValueError(f'All of {s} shifts for day:{d} have been deleted. This should not ever happen.')
            elif v > 0:
                raise ValueError(f'There are still {v} excess shifts for shift{shift_types[s].name} on day{d}.\nList of excess shifts:{candidates}')

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        update_working_hours()

        print('Penalties:')
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
                    s = int(var.Name()[var.Name().find('t=')+2:].split(',')[0])
                    d = int(var.Name()[var.Name().find('y=')+2:].split(')')[0])
                    v = solver.Value(var)
                    excess_shifts.append((s, d, v))

        delete_excess_shifts()

        print()
        header = '             '
        for w, week in enumerate(list_month):
            for d in week:
                header += get_letter_for_weekday(d[1]) + " "
        print(header)
        for e in employees:
            sched = ''
            for d in range(1, num_days + 1):
                for s in range(num_shifts):
                    if solver.BooleanValue(work[e.pk, s, d]):
                        sched += shift_types[s].name[0] + ' '
            print('employee %i: %s' % (e.pk, sched))
        print()

    # We only return a list of shift objects
    def output_inflate(shift_types, schedule_dict):
        output_shifts = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for e in employees:
                for d in range(1, num_days + 1):
                    for s in range(num_shifts):
                        if solver.BooleanValue(work[e.pk, s, d]):
                            shift_day = datetime(year, month, d)
                            shift_type = shift_types[s]
                            if shift_type.name == "-":
                                continue

                            output_shifts.append(
                                Shift(date=shift_day.date(),
                                      schedule=schedule_dict[shift_type.workplace.id],
                                      employee=e,
                                      shift_type=shift_type))
        return output_shifts

    print()
    print('Statistics')
    print('  - status          : %s' % solver.StatusName(status))
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())

    print('  - employees work time:')
    for e in employees:
        print(f"    * employee {e.pk} (job time {e.job_time}): {work_time[e.pk] // 60} hrs")
    # for w in work_time:
    #     print(f"    * employee {w} (job time {employees[w].job_time}): {work_time[w] // 60} hrs")

    return output_inflate(shift_types, schedule_dict)


def get_letter_for_weekday(day: int):
    match day:
        case 0:
            return 'M'
        case 1 | 3:
            return 'T'
        case 2:
            return 'W'
        case 4:
            return 'F'
        case 5 | 6:
            return 'S'
        case _:
            return None


def main_algorithm(schedule_dict, emp, shift_types, year, month, emp_for_workplaces):

    workplace = Workplace.objects.all().first()

    active_days = '1111111'
    # Calendar data
    global list_month, num_days
    list_month = get_month_by_weeks(year, month)
    # num_weeks = len(list_month)
    num_days = list_month[-1][-1][0]
    # num_sundays = sum([x[1] == 6 for x in flatten(list_month)])

    shift_free = ShiftType(hour_start='00:00', hour_end='00:00', name='-', workplace=workplace, active_days=active_days,
                           is_used=True, is_archive=False)
    shift_types.insert(0, shift_free)

    # Dictionary with work time assigned for each employee (key is emp.pk)
    global work_time
    work_time = dict()

    # Only consider employees with set job time
    emp = [e for e in emp if e.job_time != 0]

    # Sort employees by their job time
    emp = sorted(emp, key=lambda e: e.job_time)

    for e in emp:
        work_time[e.pk] = 0

    data = solve_shift_scheduling(emp_for_workplaces,
                                  schedule_dict,
                                  emp,  # employee list
                                  shift_types,  # shift type list
                                  year, month,  # date
                                  params='max_time_in_seconds:23.0', output_proto=None)
    return data


def main_test_algorithm():
    year = 2022
    month = 6
    emp = Employee.objects.all()
    workplace = Workplace.objects.all().first()
    workplace2 = Workplace.objects.all().last()
    # schedule = Schedule.objects.all().first()
    active_days = '1111111'
    schedule_dict = {}
    schedule_dict.update({workplace.id: Schedule(year=year, month=month, workplace=workplace)})
    schedule_dict.update({workplace2.id: Schedule(year=year, month=month, workplace=workplace2)})
    shift_free = ShiftType(hour_start='00:00', hour_end='00:00', name='-', workplace=workplace, active_days=active_days,
                           is_used=True, is_archive=False)
    shift_m1 = ShiftType(hour_start='06:00', hour_end='14:00', name='M', workplace=workplace, active_days=active_days,
                         is_used=True, is_archive=False)
    shift_a1 = ShiftType(hour_start='14:00', hour_end='22:00', name='A', workplace=workplace, active_days=active_days,
                         is_used=True, is_archive=False)
    shift_m2 = ShiftType(hour_start='06:00', hour_end='14:00', name='m', workplace=workplace2, active_days=active_days,
                         is_used=True, is_archive=False)
    shift_a2 = ShiftType(hour_start='14:00', hour_end='22:00', name='a', workplace=workplace2, active_days=active_days,
                         is_used=True, is_archive=False)
    shift_n = ShiftType(hour_start='22:00', hour_end='06:00', name='N', workplace=workplace, active_days=active_days,
                        is_used=True, is_archive=False)
    shift_types = [shift_free, shift_m1, shift_m2, shift_a1, shift_a2, shift_n]

    global work_time    # dict z aktualnie przypisanymi godzinami (kluczem jest pk pracownika)
    work_time = {}

    for e in emp:
        work_time[e.pk] = 0

    global emp_workplaces
    emp_workplaces = {}

    for e in emp:
        emp_workplaces[e.pk] = [workplace]

    emp_workplaces[18].append(workplace2)
    emp_workplaces[40].append(workplace2)
    emp_workplaces[37].append(workplace2)
    emp_workplaces[19].append(workplace2)
    emp_workplaces[20].append(workplace2)

    data = solve_shift_scheduling(schedule_dict,
                                  emp,  # employee list
                                  shift_types,  # shift type list
                                  2022, 6,  # date
                                  params='max_time_in_seconds:30.0', output_proto=None)
    return data


def run(*args):
    if 'test' in args:
        app.run(main_test_algorithm())
    else:
        app.run(main_algorithm())
