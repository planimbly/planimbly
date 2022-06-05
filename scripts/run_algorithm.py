# python manage.py runscript run_algorithm

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

from absl import flags
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


def add_soft_sum_constraint(model, works, hard_min, soft_min, min_cost,
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
        h = i_delta.seconds // 3600
        # print(f"{shifts[i].name} working time: {h}")
        i_end = i_start + timedelta(hours=h)  # do all of above in case of overnight shifts
        for j in range(1, len(shifts)):
            if i == j:
                continue
            j_start = datetime.strptime("1970-01-02" + shifts[j].hour_start.strftime('%H:%M'), "%Y-%m-%d%H:%M")
            dt = j_start - i_end
            dt = int(dt.total_seconds() // 3600)
            # print(f"dt between {shifts[i].name} and {shifts[j].name} is {dt}")
            # print(f"{i_end} to {j_start}")
            if dt < 11:  # break between i and j is below 11 hours
                print(f"Found illegal transition: {shifts[i].name} to {shifts[j].name}")
                it.append((i, j, 0))
    return it


def solve_shift_scheduling(schedule_dict, employees: list[Employee], shift_types: list[ShiftType], year: int,
                           month: int, params, output_proto):
    """Solves the shift scheduling problem."""
    # All employes
    all_employees = Employee.objects.all()
    # Calendar data
    list_month = get_month_by_weeks(year, month)
    # num_weeks = len(list_month)
    num_days = list_month[-1][-1][0]
    # num_sundays = sum([x[1] == 6 for x in flatten(list_month)])

    # Shift data

    shifts = []

    for shift__ in shift_types:
        shifts.append(shift__.id)

    num_shifts = len(shifts)

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

    # TODO: faktycznie sparametryzować algorytm względem shiftów
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
        (0, 1, 2, 7, 2, 3, 4),
        # At least 1 night shift per week (penalized). At most 4 (hard).
        # (5, 0, 1, 3, 4, 4, 0),
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

    # TODO: faktycznie sparametryzować algorytm względem shiftów
    # TODO: shifty dla każdego z obiektów
    # daily demands for work shifts (morning, afternoon, night) for each day
    # of the week starting on Monday.
    weekly_cover_demands = [
        (1, 1, 1, 1, 1),  # Monday
        (1, 1, 1, 1, 1),  # Tuesday
        (1, 1, 1, 1, 1),  # Wednesday
        (1, 1, 1, 1, 1),  # Thursday
        (1, 1, 1, 1, 1),  # Friday
        (1, 1, 1, 1, 1),  # Saturday
        (1, 1, 1, 1, 1),  # Sunday
    ]

    # TODO: zamienić 1 na parametr daily cover demand który będzie w klasie shift_type
    weekly_cover_demands = [tuple(1 for x in shift_types) for _ in range(7)]

    # Penalty for exceeding the cover constraint per shift type.
    excess_cover_penalties = tuple(20 for x in shift_types)

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

    # Fixed assignments.
    for e, s, d in fixed_assignments:
        model.Add(work[e, s, d] == 1)

    # Employee requests
    for e, s, d, w in requests:
        obj_bool_vars.append(work[e, s, d])
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

    # Weekly sum constraints
    # BUG: when dealing with 6 week months, the algorithm fails because of this constraint
    for ct in weekly_sum_constraints:
        shift, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for e in employees:
            for w, week in enumerate(list_month):
                if len(week) < 3:  # temporary bandaid fix... probably need to account for weeks in some another way..
                    continue
                works = [work[e.pk, shift, d[0]] for d in week]
                variables, coeffs = add_soft_sum_constraint(
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
                min_demand = weekly_cover_demands[d[1]][s - 1]
                worked = model.NewIntVar(min_demand, len(employees), '')
                model.Add(worked == sum(works))
                over_penalty = excess_cover_penalties[s - 1]
                if over_penalty > 0:
                    name = 'excess_demand(shift=%i, week=%i, day=%i)' % (s, w,
                                                                         d[0])
                    excess = model.NewIntVar(0, len(employees) - min_demand,
                                             name)
                    model.Add(excess == worked - min_demand)
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

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print()
        header = '          '
        for w, week in enumerate(list_month):
            for d in week:
                header += get_letter_for_weekday(d[1]) + " "
        print(header)
        for e in employees:
            sched = ''
            for d in range(1, num_days + 1):
                for s in range(num_shifts):
                    if solver.BooleanValue(work[e.pk, s, d]):
                        sched += str(shifts[s]) + ' '
            print('worker %i: %s' % (e.pk, sched))
        print()
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

    # TODO: wywalić nasze modele i zastąpić klasami Mirona
    # Chcemy zwracać na dobrą sprawę tylko listę obiektów shift
    def output_inflate(shift_types, schedule_dict):
        output_shifts = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for e in employees:
                for d in range(1, num_days + 1):
                    for s in range(num_shifts):
                        if solver.BooleanValue(work[e.pk, s, d]):
                            shift_day = datetime(year, month, d)
                            shift_type = next((x for x in shift_types if x.id == shifts[s]), None)
                            if shift_type.name == "-":
                                continue

                            output_shifts.append(
                                Shift(date=shift_day.date(), schedule=schedule_dict[shift_type.workplace.id],
                                      employee=e,
                                      shift_type=shift_type))
        return output_shifts

    print()
    print('Statistics')
    print('  - status          : %s' % solver.StatusName(status))
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())

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


def main_algorithm(schedule_dict, emp, shift_types, year, month):
    workplace = Workplace.objects.all().first()

    active_days = '1111111'
    shift_free = ShiftType(hour_start='00:00', hour_end='00:00', name='-', workplace=workplace, active_days=active_days,
                           is_used=True, is_archive=False)
    shift_types.insert(0, shift_free)

    data = solve_shift_scheduling(schedule_dict,
                                  emp,  # employee list
                                  shift_types,  # shift type list
                                  year, month,  # date
                                  params=None, output_proto=None)
    print(data)
    return data


def main_test_algorithm():
    emp = [Employee.objects.all()]
    workplace = Workplace.objects.all().first()
    workplace2 = Workplace.objects.all().last()
    # schedule = Schedule.objects.all().first()
    active_days = '1111111'
    schedule = Schedule(date_start="2022-05-15", date_end="2022-05-16",
                        workplace=workplace)
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

    data = solve_shift_scheduling(schedule,
                                  emp,  # employee list
                                  shift_types,  # shift type list
                                  2022, 6,  # date
                                  params=None, output_proto=None)
    return data


'''def run(employee_list):
    app.run(main)'''
