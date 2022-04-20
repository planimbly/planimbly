# Testing manual

## Testing the algorithm
New test files should be added to **./algorithm/tests** directory.

Names of files and functions should start with **test_**

Example:
```python
import pytest


@pytest.mark.xfail
def test_something_that_should_fail():
    assert 'a' == 'bb'


def test_sample():
    assert "sample" == "sample"
```

To test the algorithm use command:
```console
$ pytest algorithm
```

## Testing the django app

To test the django app use command:
```console
$ python manage.py test
```

## Running a linter
To run a linter use command:
```console
$ flake8
```

## Generating test coverage reports
```console
$ coverage erase
$ coverage run -ma --source=./algorithm pytest algorithm
$ coverage run -a manage.py test
$ coverage report
$ coverage html
```
Coverage report is generated in **./htmlcov/index.html**
