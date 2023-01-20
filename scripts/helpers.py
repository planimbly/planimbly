import calendar
import time
from math import floor, ceil

from loguru import logger
from ortools.sat.python import cp_model


def get_month_by_weeks(year: int, month: int):
    """Returns list of lists containing days of given month

    Sub-lists contain days of given week (the last element of every sublist is either a sunday or the last day of the month)

    Days are stored in a tuple:
    day - (day, weekday)
    """
    cal = calendar.Calendar()
    x = cal.monthdays2calendar(year, month)
    x = [list(filter(lambda item: item[0] != 0, week)) for week in x]
    return x


def get_month_by_billing_weeks(year: int, month: int):
    """Returns list of lists containing days of given month

    Sub-lists contain days of given week (the last element of every sublist is either a sunday or the last day of the month)

    Days are stored in a tuple:
    day - (day, weekday)
    """
    cal = calendar.Calendar()
    x = cal.monthdays2calendar(year, month)
    x = [list(filter(lambda item: item[0] != 0, week)) for week in x]
    x = flatten(x)

    billing_cycles = list()
    week = list()

    for day in x:
        if len(week) == 7:
            billing_cycles.append(week)
            week = []

        week.append(day)

    if len(week) > 0:
        billing_cycles.append(week)

    return billing_cycles


def flatten(t: list):
    return [item for sublist in t for item in sublist]


def get_letters_for_weekday(day: int):
    match day:
        case 0:
            return "Mo"
        case 1:
            return "Tu"
        case 2:
            return "We"
        case 3:
            return "Th"
        case 4:
            return "Fr"
        case 5:
            return "Sa"
        case 6:
            return "Su"
        case _:
            return None


def floor_to_multiple(number, multiple: int):
    return multiple * floor(number / multiple)


def ceil_to_multiple(number, multiple: int):
    return multiple * ceil(number / multiple)


class SolutionsLoggerPrinter(cp_model.ObjectiveSolutionPrinter):
    def __init__(self):
        cp_model.ObjectiveSolutionPrinter.__init__(self)
        super().__init__()
        self.__solution_count = 0
        self.__start_time = time.time()

    def on_solution_callback(self):
        """Called on each new solution."""
        current_time = time.time()
        obj = self.ObjectiveValue()
        logger.log("MODEL", f"Solution {self.__solution_count} | Time = {current_time - self.__start_time:.2f} s | Objective = {int(obj)}")
        self.__solution_count += 1
