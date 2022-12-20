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
import sys
from datetime import datetime as dt

from absl import flags
from google.protobuf import text_format
from loguru import logger
from ortools.sat.python import cp_model

from apps.accounts.models import Employee
from apps.organizations.models import Workplace
from apps.schedules.models import Shift, ShiftType
from scripts.context import Context, EmployeeInfo
from scripts.helpers import get_month_by_weeks, get_letter_for_weekday, flatten, floor_to_multiple, ceil_to_multiple

global num_days

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
        model.AddBoolOr([works[i].Not() for i in range(start, start + hard_max + 1)])

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


def solve_shift_scheduling(emp_for_workplaces, emp_preferences, emp_absences, emp_assignments, schedule_dict,
                           employees: list[Employee], shift_types: list[ShiftType], work_for_workplace_closing,
                           year: int, month: int, job_time, params, output_proto):
    """Main algorithm function. It solves the whole problem.

    Steps:
        1. XXX
        2. XXX
        3. XXX

    Args:
        emp_for_workplaces: dictionary with employees assigned to workplace (workplace id: list of employees from workplace)
        emp_preferences: dictionary with preference objects assigned to employees (employee id: list of his/her preferences)
        emp_absences: dictionary with absence objects assigned to employees (employee id: list of his/her absences)
        emp_assignments: dictionary with assignments objects assigned to employees (employee id: list of his/her absences)
        schedule_dict: # TODO explain what schedule_dict is
        employees: list of employees objects forwarded from backend and filtered in main algorithm function
        shift_types: list of shifts (objects) considered while creating schedule
        work_for_workplace_closing: dictionary with workplace closing dates (workplace id: list of WorkplaceClosing objects)
        year: we create schedule for particular year...
        month: ...and month (date)
        job_time: number of hours for full-time job
        params: parameters for CP-Sat solver
        output_proto: output for CP-Sat solver (?)

      Returns:
        list of shifts objects (date, employee, shift)
      """

    # Dictionaries with:
    work_time = dict()
    """
        Key: emp.pk\n
        Value: work time assigned to each employee
    """
    num_emp_absences = dict()
    """
            Key: emp.pk\n
            Value: number of absent days for each employee
    """

    # TODO: check if below filtering can be done while creating emp_info

    # Handling situation, when there is no "something" for an employee + preparing lists for further action
    for e in employees:
        if e.pk not in emp_preferences:
            emp_preferences[e.pk] = []
        if e.pk not in emp_absences:
            emp_absences[e.pk] = []
        if e.pk not in emp_assignments:
            emp_assignments[e.pk] = []
        work_time[e.pk] = 0
        num_emp_absences[e] = 0

    emp_info = [EmployeeInfo(e,
                             [wp for wp in emp_for_workplaces if e in emp_for_workplaces[wp]],
                             emp_preferences[e.pk],
                             emp_absences[e.pk],
                             emp_assignments[e.pk],
                             job_time)
                for e in employees]
    """
        List of EmployeeInfo objects
    """

    # Sorting employees in emp_info by their planned job time
    # TODO: move this sorting to backend
    emp_info = sorted(emp_info, key=lambda e: e.job_time, reverse=True)

    ctx = Context(emp_info, shift_types, year, month, job_time, work_for_workplace_closing)

    for ei in ctx.employees:
        num_emp_absences[ei.get()] = sum(1 for _ in ei.get_absent_days_in_month(month, year))

    # Sanitize employee list by absences
    ctx.employees = [ei for ei in ctx.employees if num_days > num_emp_absences[ei.get()]]

    # Shift constraints on continuous sequence :
    #     (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
    shift_constraints = [
        # One or two consecutive days of rest, this is a hard constraint.
        (0, 1, 1, 0, 3, 3, 0),
    ]

    # Weekly sum constraints on shifts days:
    #     (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
    weekly_sum_constraints = [
        # Constraints on rests per week.
        (0, 1, 2, 7, 2, 5, 4)
    ]

    # Overnight shift constraints
    # TODO: add constraints for combinations between different night shift types
    shift_constraints.extend(ctx.overnight_shifts[0])
    weekly_sum_constraints.extend(ctx.overnight_shifts[1])

    # Penalized transitions:
    #     (previous_shift, next_shift, penalty (0 means forbidden))
    penalized_transitions = ctx.illegal_transitions

    model = cp_model.CpModel()

    tab = ' ' * 7
    logger.info("Total job time  : {:4d}\n{}Max work time   : {:4d}\n{}Total work time : {:4d}\n{}JT ratio        : {:.3f}\n{}OT ratio        : {:.3f}".format(
        ctx.total_job_time, tab, ctx.max_work_time, tab, ctx.total_work_time, tab, ctx.job_time_multiplier, tab, ctx.overtime_multiplier))

    logger.info("Job time: {}".format(ctx.job_time))

    # Prepare list of allowed shift types for employees
    for ei in ctx.employees:
        allowed_shift_types = dict()

        allowed_shift_types[ctx.shift_types[0].get()] = [d for d in range(1, num_days + 1)]
        # Firstly, check for positive indefinite assignments
        for pia in ei.positive_indefinite_assignments:
            allowed_shift_types[pia] = [d for d in range(1, num_days + 1)]
            logger.success("[ASSIGNMENTS] Assigned shift {:d} to emp {:d} [positive indefinite assignment]".format(pia.id, ei.get().pk))

        # Assign all shifts to employee if there are no positive indefinite assignments
        if len(allowed_shift_types.keys()) == 1:
            # Only allow shifts in workplaces assigned to employee
            logger.success("Assigned all shifts to emp {:d}".format(ei.get().pk))
            for s in ctx.shift_types[1:]:
                if s.get().workplace.id in ei.workplaces:
                    allowed_shift_types[s.get()] = [d for d in range(1, num_days + 1)]
                else:
                    logger.success("[WORKPLACE] Removed shift {} from employee {:d} [not in workplace {}]".format(
                        s.get().name, ei.get().pk, s.get().workplace.name))

        # Now we handle negative indefinite assignments
        for nia in ei.negative_indefinite_assignments:
            allowed_shift_types.pop(nia, None)
            logger.success("[ASSIGNMENTS] Removed shift {:d} from employee {:d} [negative indefinite assignment]".format(
                nia.id, ei.get().pk))

        # Allow shifts from term assignments
        for ta in ei.term_assignments:
            if ta[1] is False:  # if assignment is positive
                if ta[0] not in allowed_shift_types.keys():
                    allowed_shift_types[ta[0]] = []
                    logger.warning("[ASSIGNMENTS] Assigned shift {:d} to employee {:d} on day {:d} [positive term assignment]".format(
                        ta[0].id, ei.get().pk, ta[2].day))
                allowed_shift_types[ta[0]].append(ta[2].day)  # TODO: check if makes problems
                logger.success("[ASSIGNMENTS] Assigned shift {:d} to employee {:d} on day {:d} [positive term assignment]".format(
                    ta[0].id, ei.get().pk, ta[2].day))

                for ast in allowed_shift_types:
                    if ast.id != ta[0].id:
                        for d in allowed_shift_types[ast]:
                            if d == ta[2].day:
                                allowed_shift_types[ast].remove(d)

        for x in allowed_shift_types:
            allowed_shift_types[x] = set(allowed_shift_types[x])
            allowed_shift_types[x] = list(allowed_shift_types[x])

        # Handle workplace closings
        for ast in allowed_shift_types.keys():
            if ast.id == 0:
                continue
            allowed_shift_types[ast] = [d for d in allowed_shift_types[ast] if d not in ctx.get_shift_info_by_id(ast.id).get_closing_days_in_month(month, year)]

        for x in allowed_shift_types:
            allowed_shift_types[x] = set(allowed_shift_types[x])
        ei.allowed_shift_types = allowed_shift_types

        logger.debug("EMP: {} Allowed ST: {}".format(ei.get().pk, ei.allowed_shift_types))

    # Create model variables
    work = {}
    for ei in ctx.employees:
        for s in ei.allowed_shift_types.keys():
            for d in ei.allowed_shift_types[s]:
                work[ei.get().pk, s.id, d] = model.NewBoolVar('work%i_%i_%i' % (ei.get().pk, s.id, d))

    # Linear terms of the objective in a minimization context.
    obj_int_vars = []
    obj_int_coeffs = []
    obj_bool_vars = []
    obj_bool_coeffs = []

    # Add shifts to model, we're handling positive term assignments here too
    for ei in ctx.employees:
        term_assignments = {}  # Key: day, Value: Shift_type object
        for d in range(1, num_days + 1):
            term_assignments[d] = -1

        # Check for positive term assignments
        for ta in ei.term_assignments:
            if ta[1] is False:
                term_assignments[ta[2].day] = ta[0]

        # Add exactly one shift per day
        for d in range(1, num_days + 1):
            if term_assignments[d] == -1:
                # No assignments for this day, allow all shifts
                model.AddExactlyOne(work[ei.get().pk, s.id, d] for s in ei.allowed_shift_types.keys() if (ei.get().pk, s.id, d) in work.keys())
            else:
                # Allow only assigned shift for this day
                # TODO: check later if it makes sense? we check it earlier! it should never occur!
                if term_assignments[d] not in ei.allowed_shift_types.keys():
                    logger.warning("[ASSIGNMENTS] Term assignment for shift {:d} \
                                    is overlapping with indefinite assignments for employee {:d}".format(term_assignments[d].id, ei.get().pk))
                    model.AddExactlyOne(work[ei.get().pk, 0, d])
                    continue

                model.AddExactlyOne(work[ei.get().pk, term_assignments[d].id, d])
                # TODO: decide whether it's worth increasing feasibility - maybe consult with client?
                # model.AddExactlyOne(work[ei.get().pk, s.id, d] for s in [term_assignments[d], ctx.get_shift_info_by_id(0).get()])  # Remember abt free shift!
                logger.success("[ASSIGNMENTS] added shift {:d} as term assignment for employee {:d}".format(term_assignments[d].id, ei.get().pk))

    # Deny shifts with negative term assignments
    for ei in ctx.employees:
        for ta in ei.term_assignments:
            if ta[1] is True:
                if (ei.get().pk, ta[0].id, ta[2].day) not in work.keys():
                    logger.warning("[ASSIGNMENTS] Negative term assignment on day {:d} for employee {} \
                                    overlapping with indefinite assignment/absence".format(ta[2].day, ei.get().pk))
                    continue
                model.Add(work[ei.get().pk, ta[0].id, ta[2].day] == 0)
                logger.success("[ASSIGNMENTS] Removed shift: {} day: {:d} employee: {:d} [negative term assignment]".format(ta[0].name, ta[2].day, ei.get().pk))

    # TODO: this will be used for generating schedule on top of existing schedule (in specific date range)
    # Fixed assignments.
    for e, s, d in ctx.fixed_assignments:
        if (e, s, d) not in work.keys():
            continue
        model.Add(work[e, s, d] == 1)

    # Employee requests (soft)
    for e, s, d, w in ctx.requests:
        if (e, s, d) not in work.keys():
            logger.warning("[REQUESTS] Shift on day {:d} for employee {} \
                overlapping with indefinite assignment/absence".format(d, e))
            continue
        obj_bool_vars.append(work[e, s, d])
        obj_bool_coeffs.append(w)

    # Shift constraints
    for ct in shift_constraints:
        shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for ei in ctx.employees:
            if shift not in [s.id for s in ei.allowed_shift_types.keys()]:
                continue

            absences = ei.get_absent_days_in_month(month, year)

            works = [work[ei.get().pk, shift, d] for d in ei.allowed_shift_types[ctx.get_shift_info_by_id(shift).get()] if d not in absences]

            variables, coeffs = add_soft_sequence_constraint(
                model, works, hard_min, soft_min, min_cost, soft_max, hard_max,
                max_cost, 'shift_constraint(employee %i, shift %i)' % (ei.get().pk, shift))
            obj_bool_vars.extend(variables)
            obj_bool_coeffs.extend(coeffs)

    # Calculate work time constraints
    # Phase 1: Estimation
    for ei in ctx.employees:
        hard_min = 0
        soft_min = 0
        min_cost = 75
        soft_max = 0
        hard_max = 0
        max_cost = 25

        if ctx.job_time_multiplier < 1:
            hard_min = min(ei.max_work_time, floor_to_multiple(ei.job_time * ctx.job_time_multiplier, 8) - 8)
            soft_min = min(ei.max_work_time, floor_to_multiple(ei.job_time * ctx.job_time_multiplier, 8))
            soft_max = min(ei.max_work_time, ceil_to_multiple(ei.job_time * ctx.job_time_multiplier, 8))
            hard_max = min(ei.max_work_time, ei.job_time + 8)
        elif ctx.job_time_multiplier >= 1:
            hard_min = min(ei.max_work_time, ei.job_time - 8)
            soft_min = min(ei.max_work_time, floor_to_multiple(ei.job_time * ctx.overtime_multiplier, 8))
            soft_max = min(ei.max_work_time, ceil_to_multiple(ei.job_time * ctx.overtime_multiplier, 8))
            hard_max = min(ei.max_work_time, soft_max + 8)
            if ei.job_time == ctx.job_time:
                hard_min = soft_min = soft_max = hard_max = min(ei.max_work_time, ctx.job_time)
                min_cost = 0
                max_cost = 0

        # Why?
        if ei.job_time < ctx.job_time:
            soft_min = min(ctx.job_time - 8, soft_min)

        if not ctx.overtime_for_full_timers:
            soft_max = min(ei.max_work_time, min(ctx.job_time, soft_max))
            hard_max = min(ei.max_work_time, min(ctx.job_time, hard_max))
        else:
            # We probably don't need to do accurate estimates here for now, though it might spare us some computing power
            # soft_max = min(ei.max_work_time, min(soft_max,
            #                ctx.job_time + floor_to_multiple(ctx.overtime_above_full_time // len(ctx.employees), 8)))
            # hard_max = min(ei.max_work_time, min(hard_max,
            #                ctx.job_time + ceil_to_multiple(ctx.overtime_above_full_time // len(ctx.employees), 8)))
            hard_min = min(ctx.job_time, ei.max_work_time - 8)
            soft_min = min(ei.max_work_time, max(floor_to_multiple(ctx.total_work_time / len(ctx.employees), 8), ctx.job_time))
            soft_max = min(ei.max_work_time, max(ceil_to_multiple(ctx.total_work_time / len(ctx.employees), 8), ctx.job_time))
            hard_max = ei.max_work_time

        ei.work_time_constraint = [hard_min, soft_min, min_cost, soft_max, hard_max, max_cost]

    # Phase 2: Corrections and adding constraints
    # Check if the scenario is feasible
    if ctx.total_work_time < ctx.max_work_time:
        # Check if we have underestimated work time
        work_time_diff = sum(x.work_time_constraint[4] for x in ctx.employees) - ctx.total_work_time
        logger.info("Worktime diff: {}".format(work_time_diff))
        if work_time_diff < 0:
            hard_max = int
            # Yes, we did.. :(
            if ctx.overtime_for_full_timers:  # This block of code should never be hit!
                logger.critical("There were some unknown problems calculating work time...")
                # Increase hard_max for everyone
                corr: int = ceil_to_multiple(work_time_diff / len(ctx.employees), 8)
                for ei in ctx.employees:
                    hard_max = ei.work_time_constraint[4]
                    hard_max = min(hard_max + corr, ei.max_work_time)
                    ei.work_time_constraint[4] = hard_max
            else:
                # Increase hard_max only for people who haven't reached full time
                # These "correction" calculations need to be more complex, we need to consider max_work_time etc.
                corr: int = ceil_to_multiple(work_time_diff / len([ei for ei in ctx.employees if ei.work_time_constraint[4] < ctx.job_time]), 8)
                i = 0
                for ei in ctx.employees:
                    if i >= len([ei for ei in ctx.employees if ei.work_time_constraint[4] < ctx.job_time]):
                        ctx.overtime_for_full_timers = True
                        break
                    corr = ceil_to_multiple(work_time_diff / len([ei for ei in ctx.employees if ei.work_time_constraint[4] < ctx.job_time]) - i, 8)

                    hard_max = ei.work_time_constraint[4]
                    if hard_max >= ei.max_work_time or hard_max >= ctx.job_time:
                        i += 1

                for ei in sorted(ctx.employees, key=lambda e: e.work_time_constraint[4], reverse=True):
                    if not ctx.overtime_for_full_timers:
                        hard_max = ei.work_time_constraint[4]
                        if hard_max >= ctx.job_time:
                            i += 1
                            corr = ceil_to_multiple(work_time_diff / len([ei for ei in ctx.employees if ei.work_time_constraint[4] < ctx.job_time]) - i, 8)
                            continue
                        # Clamp work time to job time
                        if hard_max + corr > ctx.job_time:
                            hard_max = min(ctx.job_time, ei.max_work_time)
                            ei.work_time_constraint[4] = hard_max
                        else:
                            hard_max = min(hard_max + corr, ei.max_work_time)
                            ei.work_time_constraint[4] = hard_max
                    else:
                        # hard_min, soft_min, soft_max, hard_max
                        if ei.job_time == ctx.job_time:
                            ei.work_time_constraint[0] = min(ctx.job_time, ei.max_work_time - 8)
                        else:
                            ei.work_time_constraint[0] = min(ctx.job_time - 8, ei.max_work_time - 8)
                        ei.work_time_constraint[1] = min(ei.max_work_time, max(floor_to_multiple(ctx.total_work_time / len(ctx.employees), 8), ctx.job_time))
                        ei.work_time_constraint[3] = min(ei.max_work_time, max(ceil_to_multiple(ctx.total_work_time / len(ctx.employees), 8), ctx.job_time))
                        ei.work_time_constraint[4] = ei.max_work_time
            work_time_diff = sum(x.work_time_constraint[4] for x in ctx.employees) - ctx.total_work_time
            if sum(x.work_time_constraint[0] for x in ctx.employees) > ctx.total_work_time:
                logger.critical("Overestimated hard_min constraints!")
            logger.info("Worktime diff after corrections: {}".format(work_time_diff))

        # Add work time constraints to the model
        for ei in ctx.employees:
            works = [work[ei.get().pk, s.id, d] for s in ei.allowed_shift_types.keys() for d in ei.allowed_shift_types[s] if s.id != 0]
            hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ei.work_time_constraint
            logger.info("emp {:2d}, jt {:3d}h, hard_min {:3d}h, soft_min {:3d}h, soft_max {:3d}h, hard_max {:3d}h, overtime: {:3d}h, max_wt: {:3d}h".format(
                ei.get().pk, ei.job_time, hard_min, soft_min, soft_max, hard_max, hard_max - ei.job_time, ei.max_work_time))
            variables, coeffs = add_monthly_soft_sum_constraint(
                model, works, hard_min // 8, soft_min // 8, min_cost, soft_max // 8,
                hard_max // 8, max_cost, 'work_time_constraint(employee %i, job_time %i)' % (ei.get().pk, ei.job_time))
            obj_int_vars.extend(variables)
            obj_int_coeffs.extend(coeffs)
    else:
        logger.critical('Total allowed work time is not enough to fill the schedule for this month!!!')

    # Weekly sum constraints
    # BUG: when dealing with 6 week months, the algorithm fails because of this constraint
    for ct in weekly_sum_constraints:
        for ei in ctx.employees:
            for w, week in enumerate(ctx.month_by_billing_weeks):
                shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct

                if shift not in [s.id for s in ei.allowed_shift_types.keys()]:
                    continue

                if len(week) <= 3:  # TODO: this is a temporary fix...
                    continue

                works = [work[ei.get().pk, shift, d[0]] for d in week if (ei.get().pk, shift, d[0]) in work.keys()]

                # Account for absences
                if shift == 0:
                    num_absences = sum(x in ei.get_absent_days_in_month(month, year) for x in [d[0] for d in week])
                    if num_absences > 0:
                        if num_absences > soft_max:
                            hard_max = min(num_absences + 1, len(works))
                            soft_max = min(num_absences, len(works))
                            logger.info("[WEEKLY CONSTRAINT CORRECTION] week {:d} emp {:d} num_absences {:d}".format(w, ei.get().pk, num_absences))

                variables, coeffs = add_weekly_soft_sum_constraint(model, works, hard_min, soft_min, min_cost, soft_max,
                                                                   hard_max, max_cost, 'weekly_sum_constraint(employee %i, shift %i, week %i)' %
                                                                   (ei.get().pk, shift, w))
                obj_int_vars.extend(variables)
                obj_int_coeffs.extend(coeffs)

    # Weekend constraints
    for ei in ctx.employees:
        hard_max_hours = ei.work_time_constraint[4]
        min_free_shifts = 1

        # No overtime over job time
        if hard_max_hours == ei.calculate_job_time(ctx.job_time):
            match ei.get().job_time:
                case '1':
                    min_free_shifts = 1
                case '3/4':
                    min_free_shifts = 2
                case '1/2':
                    min_free_shifts = 3
        # Overtime, but not over full job time
        elif ei.calculate_job_time(ctx.job_time) < hard_max_hours <= ctx.job_time:
            if hard_max_hours == ctx.job_time:
                min_free_shifts = 1
            elif hard_max_hours >= ctx.job_time * 3 // 4:
                min_free_shifts = 2
            else:
                min_free_shifts = 3

        works_sunday = [work[ei.get().pk, 0, d[0]] for d in flatten(get_month_by_weeks(year, month)) if d[1] == 6 and (ei.get().pk, 0, d[0]) in work.keys()]
        # print(ei.get().pk, hard_max_hours, min_free_shifts, len(works_sunday))
        logger.info("Min number of free sundays for employee {:d}: {:d}".format(ei.get().pk, min_free_shifts))

        hard_min = model.NewIntVar(min_free_shifts, len(works_sunday), '')
        model.Add(sum(works_sunday) == hard_min)

    # Weekend transition constraints
    for d in [x for x in flatten(ctx.month_by_billing_weeks) if x[1] in [4, 5]]:
        if d[1] == 4 and d[0] + 3 <= num_days:
            # Night shift on Friday, free weekend -> shift on Monday should start at least at 11:00
            transitions = []
            forbidden_shifts = []
            midnight = dt.min
            for i in ctx.shift_types[1:]:
                hr_start = dt.combine(dt.min, i.get().hour_start)
                delta = hr_start - midnight
                delta = int(delta.total_seconds() // 60)
                if delta < (11 * 60):
                    forbidden_shifts.append(i.id)
            for os in ctx.overnight_shifts[0]:
                for ei in ctx.employees:
                    if (ei.get().pk, os[0], d[0]) not in work.keys():
                        continue
                    for fs in forbidden_shifts:
                        if (ei.get().pk, 0, d[0] + 1) not in work.keys() \
                            or (ei.get().pk, 0, d[0] + 2) not in work.keys() \
                                or (ei.get().pk, fs, d[0] + 3) not in work.keys():
                            continue

                        transitions.append([work[ei.get().pk, os[0], d[0]].Not(),
                                            work[ei.get().pk, 0, d[0] + 1].Not(),
                                            work[ei.get().pk, 0, d[0] + 2].Not(),
                                            work[ei.get().pk, fs, d[0] + 3].Not()])

                    for t in transitions:
                        model.AddBoolOr(t)

        elif d[1] == 5 and d[0] + 2 <= num_days:
            pass
            # Working on the weekend -> free Monday
            # for ei in ctx.employees:
            #     if (ei.get().pk, 0, d[0]) not in work.keys() \
            #         or (ei.get().pk, 0, d[0] + 1) not in work.keys() \
            #         or (ei.get().pk, 0, d[0] + 2) not in work.keys():
            #             continue
            #     transitions = []
            #     # for i in list(ei.allowed_shift_types.keys())[1:]:
            #     #     for j in list(ei.allowed_shift_types.keys())[1:]:
            #     #         transitions.append([work[ei.get().pk, i.id, d[0]].Not(),
            #     #                             work[ei.get().pk, j.id, d[0] + 1].Not(),
            #     #                             work[ei.get().pk, 0, d[0] + 2]])
            #     transitions = [[work[ei.get().pk, 0, d[0]].Not(), work[ei.get().pk, 0, d[0] + 1].Not()]]

            #     for t in transitions:
            #         model.AddBoolAnd(work[ei.get().pk, 0, d[0] + 2]).OnlyEnforceIf(t)

    # Minimum one free weekend per employee
    for ei in ctx.employees:
        works = [[work[ei.get().pk, 0, d[0]], work[ei.get().pk, 0, d[0] + 1]] for d in flatten(get_month_by_weeks(year, month))
                 if d[1] == 5 and ((ei.get().pk, 0, d[0]) in work.keys() and (ei.get().pk, 0, d[0] + 1) in work.keys())]

        for w in works:
            model.AddBoolAnd(w[0]).OnlyEnforceIf(w[1])

    # Penalized transitions
    for previous_shift, next_shift, cost in penalized_transitions:
        for ei in ctx.employees:
            for d in range(1, num_days):
                if (ei.get().pk, previous_shift, d) not in work.keys() \
                        or (ei.get().pk, next_shift, d + 1) not in work.keys():
                    continue

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
        for w, week in enumerate(ctx.month_by_billing_weeks):
            for d in week:
                if d[0] in s.get_closing_days_in_month(month, year):
                    continue
                works = [work[ei.get().pk, s.id, d[0]] for ei in
                         [e for e in ctx.employees] if (ei.get().pk, s.id, d[0]) in work.keys()]
                # Ignore Off shift.
                demand = s.get().demand
                worked = model.NewIntVar(demand, len(ctx.employees), '')
                model.Add(worked == sum(works))
                over_penalty = 100
                if over_penalty > 0:
                    name = 'excess_demand(shift=%i, week=%i, day=%i)' % (s.id, w, d[0])
                    excess = model.NewIntVar(0, len(ctx.employees) - demand, name)
                    model.Add(excess == worked - demand)
                    obj_int_vars.append(excess)
                    obj_int_coeffs.append(over_penalty)

    # Objective
    model.Minimize(sum(obj_bool_vars[i] * obj_bool_coeffs[i] for i in range(len(obj_bool_vars))) +
                   sum(obj_int_vars[i] * obj_int_coeffs[i] for i in range(len(obj_int_vars))))

    if output_proto:
        print('Writing proto to %s' % output_proto)
        with open(output_proto, 'w') as text_file:
            text_file.write(str(model))

    logger.info("Solving model:")

    # Solve the model.
    solver = cp_model.CpSolver()
    if params:
        text_format.Parse(params, solver.parameters)
    solution_printer = cp_model.ObjectiveSolutionPrinter()
    status = solver.Solve(model, solution_printer)

    def update_working_hours():
        for d in range(1, num_days + 1):
            for ei in ctx.employees:
                for s in ei.allowed_shift_types.keys():
                    if (ei.get().pk, s.id, d) not in work.keys() or s.id == 0:
                        continue
                    if solver.BooleanValue(work[ei.get().pk, s.id, d]):
                        work_time[ei.get().pk] += ctx.get_shift_info_by_id(s.id).get_duration_in_hours()

    excess_shifts = []

    # Delete excess shifts according to assigned working hours
    def delete_excess_shifts():
        s_excess_shifts = dict()
        job_times = sorted(set(ei.job_time for ei in ctx.employees), reverse=True)

        for s, d, v in excess_shifts:
            candidates = [[ei.get(), s, d] for ei in ctx.employees if solver.BooleanValue(work[ei.get().pk, s, d])]
            s_excess_shifts[(s, d, v)] = [[c[0].job_time for c in candidates].count(jt) for jt in job_times]

        excess_full_timers = {k: v for k, v in s_excess_shifts.items() if sum(v) == v[0]}
        excess_rest = {k: v for k, v in s_excess_shifts.items() if sum(v) != v[0]}

        sorted_excess_rest = dict(sorted(excess_rest.items(), key=operator.itemgetter(1), reverse=True))

        sorted_excess_shifts = excess_full_timers | sorted_excess_rest

        if sorted_excess_shifts:
            logger.info("Prepared excess shifts:", sorted_excess_shifts)

        for s, d, v in sorted_excess_shifts:
            candidates = [[ei, s, d] for ei in ctx.employees if solver.BooleanValue(work[ei.get().pk, s, d])]
            candidates = sorted(sorted(candidates, key=lambda x: x[0].job_time, reverse=True),
                                key=lambda x: work_time[x[0].get().pk] - x[0].job_time)

            for c in candidates:
                logger.info("employee {:d} job time {:d} work time {:d} diff {:d}".format(
                    c[0].get().pk, c[0].job_time, work_time[c[0].get().pk], work_time[c[0].get().pk] - c[0].job_time))

            # Step 1
            # See if there are employees who fulfilled their job time
            full_timers = list(filter(lambda x: work_time[x[0].get().pk] > x[0].job_time, candidates))

            if full_timers != candidates:
                if len(full_timers) > 0:
                    for ft in full_timers:
                        candidates.remove(ft)

                # Delete their excess shifts
                while len(full_timers) > 0:
                    em, sh, da = full_timers.pop(0)
                    logger.info("[EXCESS FULL TIMER] Deleted shift: '{}' for employee {:d} with job time of {:d} and work time {:d} on day {:d}".format(
                        ctx.get_shift_info_by_id(sh).get().name, em.get().pk, em.job_time, work_time[em.get().pk], da))
                    work[em.get().pk, sh, da] = 0
                    work[em.get().pk, 0, da] = 1
                    v -= 1
                    work_time[em.get().pk] -= ctx.get_shift_info_by_id(sh).get_duration_in_hours()

            # TODO: sprawdzać czy są pracownicy z pełnym etatem o diffie 0
            #  jeśli tak: z większym priorytetem usuwać ludzi o mniejszym etacie nawet przy ujemnym diffie!!

            # Step 2
            # Sort employees by their work time and remove shifts evenly

            candidates.pop(0)
            # winner = candidates.pop(0)
            # print(f'Candidate with the lowest work time: {winner}, {work_time[winner[0].pk]}')  # pop candidate with the lowest work time

            while len(candidates) > 0:  # delete all the other candidates
                em, sh, da = candidates.pop(0)
                logger.info("Deleted shift: '{}' for employee {:d} with job time of {:d} and work time {:d} on day {:d}".format(
                    ctx.get_shift_info_by_id(sh).get().name, em.get().pk, em.job_time, work_time[em.get().pk], da))
                work[em.get().pk, sh, da] = 0
                work[em.get().pk, 0, da] = 1  # add free shift in place of deleted shift
                v -= 1
                work_time[em.get().pk] -= ctx.get_shift_info_by_id(sh).get_duration_in_hours()

            if v < 0:
                raise ValueError("All of {} shifts for day: {:d} have been deleted. This should never happen.".format(s, d))
            elif v > 0:
                raise ValueError("There is still {} excess demand for shift {} on day {}.\nList of excess shifts: {}".format(
                        v, ctx.get_shift_info_by_id(s).get().name, d, candidates))

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        update_working_hours()

        logger.info("Penalties:")
        for i, var in enumerate(obj_bool_vars):
            if solver.BooleanValue(var):
                penalty = obj_bool_coeffs[i]
                if penalty > 0:
                    logger.info("  {} violated, penalty={:d}".format(var.Name(), penalty))
                else:
                    logger.info("  {} fulfilled, gain={:d}".format(var.Name(), -penalty))

        for i, var in enumerate(obj_int_vars):
            if solver.Value(var) > 0:
                logger.info("  {} violated by {:d}, linear penalty={:d}".format(var.Name(), solver.Value(var), obj_int_coeffs[i]))
                if var.Name().startswith('excess_demand'):  # TODO: DO SOMETHING TO AVOID THIS ABOMINABLE CRINGEFEST
                    s = int(var.Name()[var.Name().find('t=') + 2:].split(',')[0])
                    d = int(var.Name()[var.Name().find('y=') + 2:].split(')')[0])
                    v = solver.Value(var)
                    excess_shifts.append((s, d, v))

        delete_excess_shifts()

        print("\n")
        header = ' ' * 13
        header_days = ' ' * 13
        for w, week in enumerate(ctx.month_by_billing_weeks):
            for d in week:
                header += '%2s ' % get_letter_for_weekday(d[1])
                header_days += '%2i ' % d[0]
            header += '   '
            header_days += '   '
        logger.success(header)
        logger.success("{}".format(header_days))

        for ei in ctx.employees:
            sched = ''
            for w, week in enumerate(ctx.month_by_billing_weeks):
                for d in week:
                    for s in ei.allowed_shift_types.keys():
                        if (ei.get().pk, s.id, d[0]) not in work.keys():
                            continue
                        if solver.BooleanValue(work[ei.get().pk, s.id, d[0]]):
                            sched += '%2s ' % s.name[0]
                sched += '   '

            logger.success("employee {:2d}: {} | JT: {:4d} | WT: {:4d} | RATIO: {:.2f}".format(
                ei.get().pk, sched, ei.job_time, work_time[ei.get().pk], work_time[ei.get().pk] / ei.job_time))

        logger.success("\n{}TOTALS | JT: {:4d} | WT: {:4d} | JT RATIO: {:.3f} \n{} | OT RATIO: {:.3f}".format(
            ' ' * (17 + num_days * 3 + len(ctx.month_by_billing_weeks) * 3), ctx.total_work_time, ctx.total_job_time, ctx.job_time_multiplier,
            ' ' * 153, ctx.overtime_multiplier))

    # We only return a list of shift objects
    def output_inflate():
        output_shifts = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for ei in ctx.employees:
                for s in ei.allowed_shift_types.keys():
                    for d in ei.allowed_shift_types[s]:
                        if s.id == 0:
                            continue
                        if solver.BooleanValue(work[ei.get().pk, s.id, d]):
                            output_shifts.append(
                                Shift(date=dt(year, month, d).date(),
                                      schedule=schedule_dict[s.workplace.id],
                                      employee=ei.get(),
                                      shift_type=s))
        # else:
        #     for el in obj_int_vars:
        #         logger.trace(el)
        #     for el in obj_bool_vars:
        #         logger.trace(el)

        return output_shifts

    logger.info("Statistics:")
    logger.info("  - status           : {}".format(solver.StatusName(status)))
    logger.info("  - conflicts        : {:d}".format(solver.NumConflicts()))
    logger.info("  - branches         : {:d}".format(solver.NumBranches()))
    logger.info("  - wall time (sec.) : {:.3f}".format(solver.WallTime()))
    logger.info("")

    return output_inflate()
    # return {'data': output_inflate(), 'status': True if (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE) else False}


def main_algorithm(schedule_dict, emp, shift_types, year, month, emp_for_workplaces, emp_preferences, emp_absences,
                   emp_assignments, job_time, work_for_workplace_closing):

    # Starting logger
    logger.remove()

    try:
        logger.level("ADDED")
    except (Exception,):
        logger.level("ADDED", no=23, color="<blue><bold>", icon="\u2795")

    logger.add("./scripts/logs/log_{time}.log", level="TRACE")
    logger.add(sys.stdout, format="<level>{level} | {message}</level>", level="INFO")

    logger.success("Logging started...")

    # Calendar data
    global num_days
    num_days = get_month_by_weeks(year, month)[-1][-1][0]

    # Adding free shift to shift_types
    shift_free = ShiftType(hour_start=dt.time(dt.strptime('00:00', '%H:%M')),
                           hour_end=dt.time(dt.strptime('00:00', '%H:%M')),
                           name='-', workplace=Workplace.objects.all().first(), active_days='1111111',
                           shift_code="---",
                           is_used=True, is_archive=False)
    shift_free.pk = 0
    shift_types.insert(0, shift_free)

    # Only consider employees with set job time
    new_emp = list()
    for e in emp:
        if e.job_time in ['1', '1/2', '1/4', '3/4']:
            new_emp.append(e)
        else:
            logger.warning("Employee no. {} has invalid job time ({}) and won't be used in solving!".format(e.pk, e.job_time))

    if type(job_time) is not int or job_time == 0:
        logger.critical("Job time is not set!!!")

    data = solve_shift_scheduling(emp_for_workplaces,
                                  emp_preferences,
                                  emp_absences,
                                  emp_assignments,
                                  schedule_dict,
                                  new_emp,
                                  shift_types,
                                  work_for_workplace_closing,
                                  year, month,
                                  job_time,
                                  params='max_time_in_seconds:120.0', output_proto=None)

    logger.remove()

    return data
