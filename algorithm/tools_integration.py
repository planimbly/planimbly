from ortools.sat.python import cp_model
from dummy_data import return_dummy_data
#from patrial_solution_printer import PartialSolutionPrinter

class PartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_workres, num_days, num_shifts, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_workres = num_workres
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._solution_count = 0
        self._solution_limit = limit

    def on_solution_callback(self):
        self._solution_count += 1
        print('Solution %i' % self._solution_count)
        for d in range(self._num_days):
            print('Day %i' % d)
            for n in range(self._num_workres):
                is_working = False
                for s in range(self._num_shifts):
                    if self.Value(self._shifts[(n, d, s)]):
                        is_working = True
                        print('  Workre %i works shift %i' % (n, s))
                if not is_working:
                    print('  Worker {} does not work'.format(n))
        if self._solution_count >= self._solution_limit:
            print('Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()

    def solution_count(self):
        return self._solution_count

data = return_dummy_data()

num_workers = len(data.employees)
num_shifts = len(data.shift_types)

num_days = 0
for shift_type in data.shift_types:
    for active_days in shift_type.active_days:
        num_days += int(active_days)

num_days = int(num_days/num_shifts)

model = cp_model.CpModel()

shifts = {}
for n in data.employees:
    for d in range(num_days):
        for s in data.shift_types:
            shifts[(n.id, d, s.id)] = model.NewBoolVar('shift_n%id%is%i' % (n.id, d, s.id))

for d in range(num_days):
    for s in data.shift_types:
        model.AddExactlyOne(shifts[(n.id, d, s.id)] for n in data.employees)

for n in data.employees:
    for d in range(num_days):
        model.AddAtMostOne(shifts[(n.id, d, s.id)] for s in data.shift_types)

min_shifts_per_worker = (num_shifts * num_days) // num_workers
if num_shifts * num_days % num_workers == 0:
    max_shifts_per_worker = min_shifts_per_worker
else:
    max_shifts_per_worker = min_shifts_per_worker + 1
for n in data.employees:
    num_shifts_worked = []
    for d in range(num_days):
        for s in data.shift_types:
            num_shifts_worked.append(shifts[(n.id, d, s.id)])
    model.Add(min_shifts_per_worker <= sum(num_shifts_worked))
    model.Add(sum(num_shifts_worked) <= max_shifts_per_worker)

solver = cp_model.CpSolver()
solver.parameters.linearization_level = 0
solver.parameters.enumerate_all_solutions = True

solution_limit = 5
solution_printer = PartialSolutionPrinter(shifts, num_workers, num_days, num_shifts, solution_limit)
solver.Solve(model, solution_printer)