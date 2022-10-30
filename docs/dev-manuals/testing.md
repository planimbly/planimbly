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
$ pytest scripts
```

## Testing the django app

To test the django app use command:
```console
$ python manage.py test
```


## Running a python linter
To run a python linter use command:
```console
$ flake8
```

## Generating test coverage reports
```console
$ coverage erase
$ coverage run -ma --source=./scripts pytest scripts
$ coverage run -a manage.py test
$ coverage report
$ coverage html
```
Coverage report is generated in **./htmlcov/index.html**

## Testing Frontend
To test frontend, firstly install nodejs (stable - currently v18.12.0)
```console
$ node --version
```
Then install npm
```console
$ npm --version
```

go to the right directory:
```console
$ cd frontend_tests
```
if you don't want to update packages run
```console
$ npm ci
```
if you want to update them, then run
```console
$ npm install
```
### Testing vue apps

To test the vue app use command:
```console
$ npm test
```

### E2E Testing
To run e2e test run:
```console
$ 
```

### Running a js linter
To run a js linter use command:
```console
$ 
```