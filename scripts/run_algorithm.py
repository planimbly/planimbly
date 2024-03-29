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
from datetime import datetime as dt, timedelta

from absl import flags
from google.protobuf import text_format
from loguru import logger
from ortools.sat.python import cp_model

from apps.accounts.models import Employee
from apps.organizations.models import Workplace
from apps.schedules.models import Shift, ShiftType
from scripts.context import Context, EmployeeInfo
from scripts.helpers import get_month_by_weeks, get_letters_for_weekday, flatten, floor_to_multiple, ceil_to_multiple, SolutionsLoggerPrinter

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
                           shifts_before, year: int, month: int, job_time, params, output_proto):
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
        shifts_before: ...
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

    # Sanitize employee list by absences
    for ei in emp_info:
        ei.num_absent_days = sum(1 for _ in ei.get_absent_days_in_month(month, year))
    emp_info = [ei for ei in emp_info if num_days > ei.num_absent_days]

    ctx = Context(emp_info, shift_types, year, month, job_time, work_for_workplace_closing)

    for ei in ctx.employees:
        logger.log("ADDED", f"{ei}")

    for st in ctx.shift_types:
        logger.log("ADDED", f"{st}")

    for st in ctx.shift_types:
        logger.log("ADDED", f"[CLOSINGS] ST: {st.id:2d} | DAYS: {st.get_closing_days_in_month(month, year)}")

    # Shift constraints on continuous sequence :
    #     (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
    shift_constraints = [
        # One or two consecutive days of rest, this is a hard constraint.
        # (0, 1, 1, 0, 3, 3, 0),
    ]

    # Weekly sum constraints on shifts days:
    #     (shift, hard_min, soft_min, min_penalty, soft_max, hard_max, max_penalty)
    weekly_sum_constraints = [
        # Constraints on rests per week.
        (0, 1, 2, 7, 2, 7, 4)
    ]

    # Overnight shift constraints
    # TODO: add constraints for combinations between different night shift types
    shift_constraints.extend(ctx.overnight_shifts[0])
    weekly_sum_constraints.extend(ctx.overnight_shifts[1])

    # Penalized transitions:
    #     (previous_shift, next_shift, penalty (0 means forbidden))
    penalized_transitions = ctx.illegal_transitions

    model = cp_model.CpModel()

    # Prepare list of allowed shift types for employees
    for ei in ctx.employees:
        allowed_shift_types = dict()

        for s in ctx.shift_types:
            allowed_shift_types[s.get()] = []

        allowed_shift_types[ctx.shift_types[0].get()] = [d for d in range(1, num_days + 1)]

        # Firstly, check for positive indefinite assignments
        for pia in ei.positive_indefinite_assignments:
            allowed_shift_types[pia] = [d for d in range(1, num_days + 1)]
            logger.log("ADDED", f"[ASSIGNMENTS] | [POSITIVE INDEF. ASSIGNMENT] | ASSIGNED | SHIFT: {pia.id} EMP: {ei.get().pk:2d}")

        # Assign all shifts to employee if there are no positive indefinite assignments
        if len(ei.positive_indefinite_assignments) == 0:
            # Only allow shifts in workplaces assigned to employee
            logger.log("ADDED", f"[ASSIGNMENTS] | ASSIGNED ALL SHIFTS | EMP: {ei.get().pk:2d}")

            for s in ctx.shift_types[1:]:
                if s.get().workplace.id in ei.workplaces:
                    allowed_shift_types[s.get()] = [d for d in range(1, num_days + 1)]
                else:
                    logger.log("ADDED", f"[WORKPLACE] | [NOT IN WORKPLACE {s.get().workplace.name}] | REMOVED | SHIFT: {s.get().name} | EMP: {ei.get().pk:2d}")

        # Now we handle negative indefinite assignments
        for nia in ei.negative_indefinite_assignments:
            allowed_shift_types[nia] = []
            logger.log("ADDED", f"[ASSIGNMENTS] | [NEGATIVE INDEF. ASSIGNMENT] | REMOVED | SHIFT: {nia.id} EMP: {ei.get().pk:2d}")

        # Allow shifts from term assignments
        for ta in ei.term_assignments:
            if ta[1] is False:  # if assignment is positive
                allowed_shift_types[ta[0]].append(ta[2].day)

                for ast in allowed_shift_types:
                    if ast.id == 0:
                        continue
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

    for ei in ctx.employees:
        for ast in ei.allowed_shift_types:
            logger.debug(f"EMP: {ei.get().pk:2d} | ST: {ast.pk} | ALLOWED DAYS: {[d for d in ei.allowed_shift_types[ast]]}")

    # Create model variables
    work = {}
    forbidden_work = []

    for ei in ctx.employees:
        for s in ctx.shift_types:
            for d in range(-6, num_days + 1):
                work[ei.get().pk, s.id, d] = model.NewBoolVar(f"work{ei.get().pk}_{s.id}_{d}")
                if d not in ei.allowed_shift_types[s.get()] and d > 0:
                    forbidden_work.append((ei.get().pk, s.id, d))
        # for s in ei.allowed_shift_types.keys():
        #     for d in ei.allowed_shift_types[s]:
        #         work[ei.get().pk, s.id, d] = model.NewBoolVar("work{:d}_{:d}_{:d}".format(ei.get().pk, s.id, d))

    worked_month_before = []
    friday_before = saturday_before = 999
    # Add shifts to the model if employee has worked in last week of previous month
    if shifts_before:
        for i, sb in enumerate(shifts_before):
            if len(shifts_before.keys()) < 1:
                break
            d_shifts = shifts_before[sb]
            if sb.weekday() == 4:
                friday_before = -6 + i
            elif sb.weekday() == 5:
                saturday_before = -6 + i
            for s in d_shifts:
                work[s.employee.pk, s.shift_type.id, -6 + i] = model.NewBoolVar(f"work{s.employee.pk}_{s.shift_type.id}_{-6 + i}")
                model.AddExactlyOne(work[s.employee.pk, s.shift_type.id, -6 + i])
                worked_month_before.append((s.employee.pk, s.shift_type.id, -6 + i))

    # Add free shift to the model if employee hasn't worked month before
    for ei in ctx.employees:
        for d in range(-6, 1):
            worked = False
            for st in ctx.shift_types[1:]:
                if (ei.get().pk, st.get().id, d) in worked_month_before:
                    worked = True
                    break
            if not worked:
                model.AddExactlyOne(work[ei.get().pk, 0, d])
                worked_month_before.append((ei.get().pk, 0, d))

    worked_month_before = sorted(sorted(worked_month_before, key=lambda x: x[2]), key=lambda x: x[0])

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
                if ta[2].day in ei.allowed_shift_types[ta[0]]:
                    term_assignments[ta[2].day] = ta[0]

        # Add exactly one shift per day
        for d in range(1, num_days + 1):
            if term_assignments[d] == -1:
                # No assignments for this day, allow all shifts
                model.AddExactlyOne(work[ei.get().pk, s.id, d] for s in ei.allowed_shift_types.keys() if (ei.get().pk, s.id, d) not in forbidden_work)
            else:
                # Allow only assigned shift for this day
                if (ei.get().pk, term_assignments[d].id, d) in forbidden_work:
                    model.AddExactlyOne(work[ei.get().pk, s.id, d] for s in ei.allowed_shift_types.keys() if (ei.get().pk, s.id, d) not in forbidden_work)
                    continue

                # model.AddExactlyOne(work[ei.get().pk, term_assignments[d].id, d])
                # TODO: decide whether it's worth increasing feasibility - maybe consult with client?
                model.AddExactlyOne(work[ei.get().pk, s, d] for s in [term_assignments[d].id, 0])
                logger.log("ADDED", f"[ASSIGNMENTS] | [POSITIVE TERM ASSIGNMENT] | SHIFT: {term_assignments[d].id} | EMP: {ei.get().pk:2d} | DAY: {d:2d}")

    # Deny shifts with negative term assignments
    for ei in ctx.employees:
        for ta in ei.term_assignments:
            if ta[1] is True:
                if (ei.get().pk, ta[0].id, ta[2].day) in forbidden_work:
                    logger.warning(f"[ASSIGNMENTS] | [NEGATIVE TERM ASSIGNMENT] | SHIFT: {ta[0].id} | EMP: {ei.get().pk:2d} | DAY: {ta[2].day:2d}"
                                   f" - conflicting with indef. assignment/absence")
                    continue
                model.Add(work[ei.get().pk, ta[0].id, ta[2].day] == 0)
                logger.log("ADDED", f"[ASSIGNMENTS] | [NEGATIVE TERM ASSIGNMENT] | REMOVED | SHIFT: {ta[0].name} | EMP: {ei.get().pk:2d} | DAY: {ta[2].day:2d}")

    # TODO: this will be used for generating schedule on top of existing schedule (in specific date range)
    # Fixed assignments.
    for e, s, d in ctx.fixed_assignments:
        if (e, s, d) in forbidden_work:
            continue
        logger.log("ADDED", f"[ABSENCE] EMP: {e:2d} | SHIFT: {s:2d} | DAY: {d:2d}")
        model.Add(work[e, s, d] == 1)

    # Employee requests (soft)
    for e, s, d, w in ctx.requests:
        if (e, s, d) in forbidden_work:
            logger.warning(f"[REQUEST] EMP: {e:2d} | SHIFT: {s} | DAY: {d:2d} - conflicting with indef. assignment/absence")
            continue
        logger.log("ADDED", f"[REQUEST] EMP: {e:2d} | SHIFT: {s} | DAY: {d:2d} | WEIGHT: {w}")
        obj_bool_vars.append(work[e, s, d])
        obj_bool_coeffs.append(w)

    # Shift constraints
    for ct in shift_constraints:
        shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for ei in ctx.employees:
            if len(ei.allowed_shift_types[ctx.get_shift_info_by_id(shift).get()]) == 0:
                continue

            absences = ei.get_absent_days_in_month(month, year)

            works = [work[ei.get().pk, shift, d] for d in ei.allowed_shift_types[ctx.get_shift_info_by_id(shift).get()] if d not in absences]

            pre_works = [work[ei.get().pk, shift, d] for d in range(-6, 1) if (ei.get().pk, shift, d) not in forbidden_work]
            pre_works.extend(works)

            works = pre_works

            variables, coeffs = add_soft_sequence_constraint(
                model, works, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost,
                f"shift_constraint(employee {ei.get().pk}, shift {shift})")
            obj_bool_vars.extend(variables)
            obj_bool_coeffs.extend(coeffs)

    logger.log("MODEL", f"Job time for month : {ctx.job_time:4d}")
    logger.log("MODEL", f"FT job time        : {ctx.ft_job_time:4d}")
    logger.log("MODEL", f"REST job time      : {ctx.rest_job_time:4d}")
    logger.log("MODEL", f"Total job time     : {ctx.total_job_time:4d}")
    logger.log("MODEL", "")
    logger.log("MODEL", f"Max work time      : {ctx.max_work_time:4d}")
    logger.log("MODEL", f"Total work time    : {ctx.total_work_time:4d}")
    logger.log("MODEL", "")
    logger.log("MODEL", f"JT ratio           : {ctx.job_time_multiplier:.3f}")
    logger.log("MODEL", f"OT ratio           : {ctx.overtime_multiplier:.3f}")

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
            if ctx.ft_job_time < ctx.total_work_time and ctx.rest_job_time > 0:  # case 4
                if ei in ctx.get_full_time_employees():  # we give full-timers full job time
                    hard_min = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8))
                    soft_min = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8))
                    soft_max = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8))
                    hard_max = min(ei.max_work_time, ei.job_time)
                    min_cost = max_cost = 0
                else:
                    hard_min = 0  # min(ei.max_work_time, floor_to_multiple(ei.job_time * ctx.overtime_multiplier, 8) - 8)
                    soft_min = min(ei.max_work_time, floor_to_multiple(ei.job_time * ctx.overtime_multiplier, 8))
                    soft_max = min(ei.max_work_time, ceil_to_multiple(ei.job_time * ctx.overtime_multiplier, 8))
                    hard_max = min(ei.max_work_time, ceil_to_multiple(ei.job_time * ctx.overtime_multiplier, 8))
                    # hard_max = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8))
            else:  # case 5 and 6
                if ei in ctx.get_full_time_employees():  # we give full-timers full job time
                    hard_min = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8),
                                   floor_to_multiple(ctx.total_work_time // len(ctx.get_full_time_employees()), 8))
                    soft_min = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8),
                                   floor_to_multiple(ctx.total_work_time // len(ctx.get_full_time_employees()), 8))
                    soft_max = min(ei.max_work_time, ei.job_time, ceil_to_multiple(ei.job_time, 8))
                    hard_max = min(ei.max_work_time, ei.job_time)
                else:
                    hard_min = 0
                    soft_min = 0
                    soft_max = 0
                    hard_max = 8
                    min_cost = 0
                    max_cost = 250
                    # hard_max = min(ei.max_work_time, floor_to_multiple(ei.job_time, 8))

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
        logger.info(f"Worktime diff: {work_time_diff}")
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
                logger.error(f"Overestimated hard_mins by {sum(x.work_time_constraint[0] for x in ctx.employees) - ctx.total_work_time}h")

            logger.info(f"Worktime diff after corrections: {work_time_diff}")

        # Add work time constraints to the model
        for ei in ctx.employees:
            works = [work[ei.get().pk, s.id, d] for s in ei.allowed_shift_types.keys() for d in ei.allowed_shift_types[s] if s.id != 0]
            hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ei.work_time_constraint
            logger.log("ADDED", f"EMP {ei.get().pk:2d} | JT {ei.job_time:3d} | hard_min {hard_min:3d} | soft_min {soft_min:3d} | soft_max {soft_max:3d} | "
                                f"hard_max {hard_max:3d} | overtime {hard_max - ei.job_time:3d} | max_wt {ei.max_work_time:3d}")
            variables, coeffs = add_monthly_soft_sum_constraint(
                model, works, hard_min // 8, soft_min // 8, min_cost, soft_max // 8,
                hard_max // 8, max_cost, f"work_time_constraint(employee {ei.get().pk}, job_time {ei.job_time})")
            obj_int_vars.extend(variables)
            obj_int_coeffs.extend(coeffs)
    else:
        logger.critical("Total allowed work time is not enough to fill the schedule for this month!")

    # Weekly sum constraints
    # BUG: when dealing with 6 week months, the algorithm fails because of this constraint
    for ct in weekly_sum_constraints:
        for ei in ctx.employees:
            for w, week in enumerate(ctx.month_by_billing_weeks):
                shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct

                if len(ei.allowed_shift_types[ctx.get_shift_info_by_id(shift).get()]) == 0:
                    continue

                if len(week) <= 3:  # TODO: this is a temporary fix...
                    continue

                works = [work[ei.get().pk, shift, d[0]] for d in week if (ei.get().pk, shift, d[0]) not in forbidden_work]

                # Account for absences
                if shift == 0:
                    num_absences = sum(x in ei.get_absent_days_in_month(month, year) for x in [d[0] for d in week])
                    if num_absences > 0:
                        if num_absences > soft_max:
                            hard_max = min(num_absences + 1, len(works))
                            soft_max = min(num_absences, len(works))
                            logger.debug(f"[WEEKLY CONSTRAINT CORRECTION] WEEK: {w} | EMP: {ei.get().pk:2d} NUM ABSENCES: {num_absences:3d}")

                variables, coeffs = add_weekly_soft_sum_constraint(model, works, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost,
                                                                   f"weekly_sum_constraint(employee {ei.get().pk}, shift {shift}, week {w})")
                obj_int_vars.extend(variables)
                obj_int_coeffs.extend(coeffs)

    # Weekend constraints
    for ei in ctx.employees:
        hard_max_hours = ei.work_time_constraint[4]
        min_free_shifts = 1

        # No overtime over job time
        if hard_max_hours == ei.calculate_job_time(ctx.job_time):
            match ei.get().job_time:
                case "1":
                    min_free_shifts = 1
                case "3/4":
                    min_free_shifts = 2
                case "1/2":
                    min_free_shifts = 3

        # Overtime, but not over full job time
        elif ei.calculate_job_time(ctx.job_time) < hard_max_hours <= ctx.job_time:
            if hard_max_hours == ctx.job_time:
                min_free_shifts = 1
            elif ctx.job_time // 2 < hard_max_hours < ctx.job_time * 3 // 4:
                min_free_shifts = 2
            elif hard_max_hours <= ctx.job_time // 2:
                min_free_shifts = 3

        works_sunday = [work[ei.get().pk, 0, d[0]] for d in flatten(get_month_by_weeks(year, month))
                        if d[1] == 6 and (ei.get().pk, 0, d[0]) not in forbidden_work]

        logger.debug(f"[R_A] | [MIN FREE SUNDAYS] EMP: {ei.get().pk:2d} | NUM: {min_free_shifts}")

        hard_min = model.NewIntVar(min_free_shifts, len(works_sunday), '')
        model.Add(sum(works_sunday) == hard_min)

    # Weekend transition constraints
    for d in flatten([[(friday_before, 4), (saturday_before, 5)], [x for x in flatten(ctx.month_by_billing_weeks) if x[1] in [4, 5]]]):
        if d[1] == 4 and 0 < d[0] + 3 <= num_days:
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
                    if (ei.get().pk, os[0], d[0]) in forbidden_work:
                        continue
                    for fs in forbidden_shifts:
                        if (ei.get().pk, 0, d[0] + 1) in forbidden_work \
                            or (ei.get().pk, 0, d[0] + 2) in forbidden_work \
                                or (ei.get().pk, fs, d[0] + 3) in forbidden_work:
                            continue

                        transitions.append([work[ei.get().pk, os[0], d[0]].Not(),
                                            work[ei.get().pk, 0, d[0] + 1].Not(),
                                            work[ei.get().pk, 0, d[0] + 2].Not(),
                                            work[ei.get().pk, fs, d[0] + 3].Not()])

                    for t in transitions:
                        model.AddBoolOr(t)

        elif d[1] == 5 and 0 < d[0] + 2 <= num_days:
            # Working on the weekend -> 24hrs of rest
            transitions = []
            illegal_transitions = []
            for i in ctx.shift_types[1:]:
                hr_end = dt.combine(dt.min, i.get().hour_end)
                if i.id in [x[0] for x in ctx.overnight_shifts[0]]:
                    hr_end = hr_end + timedelta(days=1)
                for j in ctx.shift_types[1:]:
                    hr_start = dt.combine(dt.min + timedelta(days=1), j.get().hour_start)
                    delta = hr_start - hr_end
                    delta = int(delta.total_seconds() // 60)
                    if delta < (24 * 60):
                        illegal_transitions.append((i.id, j.id))

            for ei in ctx.employees:
                if (ei.get().pk, 0, d[0]) in forbidden_work \
                        or (ei.get().pk, 0, d[0] + 1) in forbidden_work \
                        or (ei.get().pk, 0, d[0] + 2) in forbidden_work:
                    continue
                transitions = []
                for i in list(ei.allowed_shift_types.keys())[1:]:
                    for j in list(ei.allowed_shift_types.keys())[1:]:
                        if d[0] not in ei.allowed_shift_types[i] \
                           or d[0] + 1 not in ei.allowed_shift_types[j]:
                            continue
                        t = [work[ei.get().pk, i.id, d[0]], work[ei.get().pk, j.id, d[0] + 1]]
                        for it in illegal_transitions:
                            if j.id == it[0] and (ei.get().pk, it[1], d[0] + 2) not in forbidden_work:
                                transitions.append([work[ei.get().pk, i.id, d[0]].Not(),
                                                    work[ei.get().pk, j.id, d[0] + 1].Not(),
                                                    work[ei.get().pk, it[1], d[0] + 2].Not()])

                for t in transitions:
                    model.AddBoolOr(t)

    # Minimum one free weekend per employee
    for ei in ctx.employees:
        works = [[work[ei.get().pk, 0, d[0]], work[ei.get().pk, 0, d[0] + 1]] for d in flatten(get_month_by_weeks(year, month))
                 if d[1] == 5 and ((ei.get().pk, 0, d[0]) not in forbidden_work and (ei.get().pk, 0, d[0] + 1) not in forbidden_work) and d[0] + 1 <= num_days]

        for w in works:
            model.AddBoolAnd(w[0]).OnlyEnforceIf(w[1])

    # Penalized transitions
    for previous_shift, next_shift, cost in penalized_transitions:
        for ei in ctx.employees:
            for d in range(0, num_days):
                if (ei.get().pk, previous_shift, d) in forbidden_work or (ei.get().pk, next_shift, d + 1) in forbidden_work:
                    continue

                transition = [work[ei.get().pk, previous_shift, d].Not(), work[ei.get().pk, next_shift, d + 1].Not()]
                if cost == 0:
                    model.AddBoolOr(transition)
                else:
                    trans_var = model.NewBoolVar(f"transition(employee={ei.get().pk}, day={d})")
                    transition.append(trans_var)
                    model.AddBoolOr(transition)
                    obj_bool_vars.append(trans_var)
                    obj_bool_coeffs.append(cost)

    # Guarantee at least one (optimally two) days of rest within 7 days range
    for ei in ctx.employees:
        # Account for the last week of previous month
        wmb = [w for w in worked_month_before if w[0] == ei.get().pk]
        wmb = sorted(wmb, key=lambda x: x[2], reverse=True)
        wmb.pop()

        possible_free_shifts = [i for i in range(1, 8)]

        for w in wmb:
            if w[1] == 0:
                break
            else:
                possible_free_shifts.pop()
        # print(ei.get().pk, wmb, possible_free_shifts)
        works = [work[ei.get().pk, 0, d] for d in possible_free_shifts]

        model.AddBoolOr(works)

        # Current month
        works = [work[ei.get().pk, 0, day].Not() for day in range(1, num_days + 1)]

        variables, coeffs = add_soft_sequence_constraint(
                model, works, 1, 2, 5, 5, 6, 5, f"sequence_rest_constraint(employee {ei.get().pk:d}))")
        obj_bool_vars.extend(variables)
        obj_bool_coeffs.extend(coeffs)

    # Cover constraints
    for s in ctx.shift_types[1:]:
        for w, week in enumerate(ctx.month_by_billing_weeks):
            for d in week:
                if d[0] in s.get_closing_days_in_month(month, year):
                    continue
                works = [work[ei.get().pk, s.id, d[0]] for ei in
                         [e for e in ctx.employees] if (ei.get().pk, s.id, d[0]) not in forbidden_work]
                # Ignore Off shift.
                demand = s.get().demand
                worked = model.NewIntVar(demand, len(ctx.employees), '')
                model.Add(worked == sum(works))
                over_penalty = 100
                if over_penalty > 0:
                    name = f"excess_demand(shift={s.id}, week={w}, day={d[0]})"
                    excess = model.NewIntVar(0, len(ctx.employees) - demand, name)
                    model.Add(excess == worked - demand)
                    obj_int_vars.append(excess)
                    obj_int_coeffs.append(over_penalty)

    # Objective
    model.Minimize(sum(obj_bool_vars[i] * obj_bool_coeffs[i] for i in range(len(obj_bool_vars))) +
                   sum(obj_int_vars[i] * obj_int_coeffs[i] for i in range(len(obj_int_vars))))

    if output_proto:
        print(f"Writing proto to {output_proto}")
        with open(output_proto, "w") as text_file:
            text_file.write(str(model))

    logger.log("MODEL", "Solving model:")

    # Solve the model.
    solver = cp_model.CpSolver()
    if params:
        text_format.Parse(params, solver.parameters)
    solution_printer = SolutionsLoggerPrinter()
    status = solver.Solve(model, solution_printer)

    def update_working_hours():
        for d in range(1, num_days + 1):
            for ei in ctx.employees:
                for s in ei.allowed_shift_types.keys():
                    if (ei.get().pk, s.id, d) in forbidden_work or s.id == 0:
                        continue
                    if solver.BooleanValue(work[ei.get().pk, s.id, d]):
                        work_time[ei.get().pk] += ctx.get_shift_info_by_id(s.id).get_duration_in_hours()

    excess_shifts = []

    # Delete excess shifts according to assigned working hours
    def delete_excess_shifts():
        s_excess_shifts = dict()
        job_times = sorted(set(ei.job_time for ei in ctx.employees), reverse=True)

        for s, d, v in excess_shifts:
            candidates = list()
            for ei in ctx.employees:
                if (ei.get().pk, s, d) in forbidden_work:
                    continue
                if solver.BooleanValue(work[ei.get().pk, s, d]):
                    candidates.append([ei.get(), s, d])

            s_excess_shifts[(s, d, v)] = [[c[0].job_time for c in candidates].count(jt) for jt in job_times]

        excess_full_timers = {k: v for k, v in s_excess_shifts.items() if sum(v) == v[0]}
        excess_rest = {k: v for k, v in s_excess_shifts.items() if sum(v) != v[0]}

        sorted_excess_rest = dict(sorted(excess_rest.items(), key=operator.itemgetter(1), reverse=True))

        sorted_excess_shifts = excess_full_timers | sorted_excess_rest

        if sorted_excess_shifts:
            logger.info(f"Prepared excess shifts: {sorted_excess_shifts}")

        for s, d, v in sorted_excess_shifts:
            candidates = list()
            for ei in ctx.employees:
                if (ei.get().pk, s, d) in forbidden_work:
                    continue
                if solver.BooleanValue(work[ei.get().pk, s, d]):
                    candidates.append([ei, s, d])

            candidates = sorted(sorted(candidates, key=lambda x: x[0].job_time, reverse=True),
                                key=lambda x: work_time[x[0].get().pk] - x[0].job_time)

            for c in candidates:
                logger.info(f"employee {c[0].get().pk:2d} job time {c[0].job_time:3d} work time {work_time[c[0].get().pk]:3d} "
                            f"diff {work_time[c[0].get().pk] - c[0].job_time}")

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
                    logger.info(f"[EXCESS FULL TIMER] Deleted shift: '{ctx.get_shift_info_by_id(sh).get().name}' for employee {em.get().pk} "
                                f"with job time of {em.job_time} and work time {work_time[em.get().pk]} on day {da}")
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
                logger.info(f"Deleted shift: '{ctx.get_shift_info_by_id(sh).get().name}' for employee {em.get().pk} with job time of {em.job_time} "
                            f"and work time {work_time[em.get().pk]} on day {da}")
                work[em.get().pk, sh, da] = 0
                work[em.get().pk, 0, da] = 1  # add free shift in place of deleted shift
                v -= 1
                work_time[em.get().pk] -= ctx.get_shift_info_by_id(sh).get_duration_in_hours()

            if v < 0:
                raise ValueError(f"All of {s} shifts for day: {d} have been deleted. This should never happen.")
            elif v > 0:
                raise ValueError(f"There is still {v} excess demand for shift {ctx.get_shift_info_by_id(s).get().name} on day {d}."
                                 f"\nList of excess shifts: {candidates}")

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        update_working_hours()

        logger.log("MODEL", "Penalties:")
        for i, var in enumerate(obj_bool_vars):
            if solver.BooleanValue(var):
                penalty = obj_bool_coeffs[i]
                if penalty > 0:
                    logger.log("MODEL", f"  - {var.Name()} violated, penalty={penalty}")
                else:
                    logger.log("MODEL", f"  - {var.Name()} fulfilled, gain={-penalty}")

        for i, var in enumerate(obj_int_vars):
            if solver.Value(var) > 0:
                logger.log("MODEL", f"  - {var.Name()} violated by {solver.Value(var)}, linear penalty={obj_int_coeffs[i]}")
                if var.Name().startswith("excess_demand"):  # TODO: DO SOMETHING TO AVOID THIS ABOMINABLE CRINGEFEST
                    s = int(var.Name()[var.Name().find("t=") + 2:].split(",")[0])
                    d = int(var.Name()[var.Name().find("y=") + 2:].split(")")[0])
                    v = solver.Value(var)
                    excess_shifts.append((s, d, v))

        # delete_excess_shifts()

        header = ' ' * 13
        header_days = ' ' * 13
        for w, week in enumerate(ctx.month_by_billing_weeks):
            for d in week:
                header += f"{get_letters_for_weekday(d[1])} "
                header_days += f"{d[0]:2d} "
            header += "   "
            header_days += "   "

        logger.success("")
        logger.success(header)
        logger.success(f"{header_days}")

        for ei in ctx.employees:
            sched = ""
            for w, week in enumerate(ctx.month_by_billing_weeks):
                for d in week:
                    for s in ei.allowed_shift_types.keys():
                        if (ei.get().pk, s.id, d[0]) in forbidden_work:
                            continue
                        if solver.BooleanValue(work[ei.get().pk, s.id, d[0]]):
                            sched += f"{s.name[0]:>2} "
                sched += "   "

            logger.success(f"employee {ei.get().pk:2d}: {sched} | JT: {ei.job_time:4d} | WT: {work_time[ei.get().pk]:4d} | "
                           f"RATIO: {work_time[ei.get().pk] / ei.job_time:.2f}")

        logger.success("")
        logger.success(f"MONTH: {month:2d} | YEAR: {year:4d}{' ' * (7 - 22 + num_days * 3 + len(ctx.month_by_billing_weeks) * 3)}TOTALS | "
                       f"JT: {ctx.total_job_time:4d} | WT: {ctx.total_work_time:4d} | JT RATIO: {ctx.job_time_multiplier:.3f}")
        logger.success(f"{' ' * (35 + num_days * 3 + len(ctx.month_by_billing_weeks) * 3)} | OT RATIO: {ctx.overtime_multiplier:.3f}")

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
                            output_shifts.append(Shift(date=dt(year, month, d).date(), schedule=schedule_dict[s.workplace.id], employee=ei.get(), shift_type=s))
        # else:
        #     for el in obj_int_vars:
        #         logger.trace(el)
        #     for el in obj_bool_vars:
        #         logger.trace(el)

        return output_shifts

    logger.log("MODEL", "Statistics:")
    logger.log("MODEL", f"  - status     : {solver.StatusName(status)}")
    logger.log("MODEL", f"  - conflicts  : {solver.NumConflicts():d}")
    logger.log("MODEL", f"  - branches   : {solver.NumBranches():d}")
    logger.log("MODEL", f"  - wall time  : {solver.WallTime():.3f} s")
    logger.log("MODEL", "")
    # logger.info("{}".format(solver.SufficientAssumptionsForInfeasibility()))

    return {"data": output_inflate(), "status": True if (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE) else False}


def main_algorithm(schedule_dict, emp, shift_types, year, month, emp_for_workplaces, emp_preferences, emp_absences,
                   emp_assignments, job_time, work_for_workplace_closing, shifts_before, shifts_after, username):
    # Starting logger
    logger.remove()

    # Adding custom logger levels
    try:
        logger.level("ADDED")
    except (Exception,):
        logger.level("ADDED", no=23, color="<blue><bold>", icon="\u2795")

    try:
        logger.level("MODEL")
    except (Exception,):
        logger.level("MODEL", no=24, color="<magenta><bold>")

    # Configuring logging outputs
    logger.add("./scripts/logs/debug/debug_{time}.log", level="TRACE", backtrace=True, diagnose=True)
    logger.add("./scripts/logs/console/console_{time}.log", level="INFO", format="<level>{level} | {message}</level>", backtrace=True, diagnose=True)
    logger.add(sys.stdout, format="<level>{level} | {message}</level>", level="INFO", backtrace=True, diagnose=True)

    logger.success(f"Generating started by {username}...")
    logger.info(f"Month: {month} | Year: {year}")

    # Calendar data
    global num_days
    num_days = get_month_by_weeks(year, month)[-1][-1][0]

    # Adding free shift to shift_types
    shift_free = ShiftType(hour_start=dt.time(dt.strptime("00:00", "%H:%M")), hour_end=dt.time(dt.strptime("00:00", "%H:%M")),
                           name="-", workplace=Workplace.objects.all().first(), active_days="1111111", shift_code="---",
                           is_used=True, is_archive=False)
    shift_free.pk = 0
    shift_types.insert(0, shift_free)

    # Only consider employees with set job time
    new_emp = list()
    for e in emp:
        if e.job_time in ["1", "1/2", "1/4", "3/4"]:
            new_emp.append(e)
        else:
            logger.warning(f"Employee no. {e.pk} has invalid job time ({e.job_time}) and won't be used in solving!")

    if type(job_time) is not int or job_time == 0:
        logger.critical(f"Job time is not set! Current value: {job_time}")

    data = {}

    try:
        data = solve_shift_scheduling(emp_for_workplaces,
                                      emp_preferences,
                                      emp_absences,
                                      emp_assignments,
                                      schedule_dict,
                                      new_emp,
                                      shift_types,
                                      work_for_workplace_closing,
                                      shifts_before,
                                      year, month,
                                      job_time,
                                      params="max_time_in_seconds:300.0", output_proto=None)
    except Exception as e:
        logger.exception(f"Something went wrong! {e}")

    logger.remove()

    return data
