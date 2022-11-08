import calendar

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