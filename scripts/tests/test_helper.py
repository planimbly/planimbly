import pytest
from ..helpers import get_month_by_billing_weeks, get_month_by_weeks


def test_get_month():
    expected_list = [[(1, 3), (2, 4), (3, 5), (4, 6)],
                     [(5, 0), (6, 1), (7, 2), (8, 3), (9, 4), (10, 5), (11, 6)],
                     [(12, 0), (13, 1), (14, 2), (15, 3), (16, 4), (17, 5), (18, 6)],
                     [(19, 0), (20, 1), (21, 2), (22, 3), (23, 4), (24, 5), (25, 6)],
                     [(26, 0), (27, 1), (28, 2), (29, 3)]]
    assert get_month_by_weeks(2024, 2) == expected_list


@pytest.mark.xfail
def test_get_month_fail():
    expected_list = []
    assert get_month_by_weeks(2024, 2) == expected_list


def test_get_month_billing():
    expected_list = [[(1, 3), (2, 4), (3, 5), (4, 6), (5, 0), (6, 1), (7, 2)],
                     [(8, 3), (9, 4), (10, 5), (11, 6), (12, 0), (13, 1), (14, 2)],
                     [(15, 3), (16, 4), (17, 5), (18, 6), (19, 0), (20, 1), (21, 2)],
                     [(22, 3), (23, 4), (24, 5), (25, 6), (26, 0), (27, 1), (28, 2)], [(29, 3)]]
    assert get_month_by_billing_weeks(2024, 2) == expected_list


@pytest.mark.xfail
def test_get_month_billing_fail():
    expected_list = []
    assert get_month_by_billing_weeks(2024, 2) == expected_list
