import pytest
# from algorithm.main import make_schedule


@pytest.mark.xfail
def test_something_that_should_fail():
    assert 'a' == 'bb'


def test_sample():
    assert "sample" == "sample"
