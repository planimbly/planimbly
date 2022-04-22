
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