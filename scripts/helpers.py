import calendar
from math import floor, ceil


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


def floor_to_multiple(number, multiple: int):
    return multiple * floor(number / multiple)


def ceil_to_multiple(number, multiple: int):
    return multiple * ceil(number / multiple)
