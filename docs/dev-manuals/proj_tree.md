# Project files structure

## Files tree
``` 
planimbly
|
│   .coverage                               <coverage related file>
│   .coveragerc                             <coverage config file>
│   .env                                    <environment file>
│   .gitignore   
│   db.sqlite3                              <dev environment database>
│   employees.csv                           <example file for user import>
│   manage.py    
│   Procfile                                <webserver settings for Heroku>
│   README.md
│   requirements.txt                        <app requirements obligatory for production>
│   requirements_dev.txt                    <dev environment requirements>
│   runtime.txt                             <python version for Heroku>
│   schedule_data.sql                       <example schedule data>
│   setup.cfg                               <python setup; only for flake8 currently>
│   
├───.github
│   └───workflows
│           tests.yml                       <Github Actions file>
│           
│           
│           
├───apps                                    <Django apps>
│   │   __init__.py
│   │   
│   ├───accounts
│   │   │   admin.py
│   │   │   apps.py
│   │   │   models.py
│   │   │   serializers.py
│   │   │   tests.py
│   │   │   urls.py
│   │   │   views.py
│   │   │   __init__.py
│   │   │   
│   │   ├───migrations
│   │   │   │   0001_initial.py
│   │   │   │   ...
│   │           
│   ├───organizations
│   │   │   admin.py
│   │   │   apps.py
│   │   │   forms.py
│   │   │   models.py
│   │   │   serializers.py
│   │   │   tests.py
│   │   │   urls.py
│   │   │   views.py
│   │   │   __init__.py
│   │   │   
│   │   ├───migrations
│   │   │   │   0001_initial.py
│   │   │   │   ...
│   │           
│   ├───schedules
│   │   │   admin.py
│   │   │   apps.py
│   │   │   models.py
│   │   │   serializers.py
│   │   │   tests.py
│   │   │   urls.py
│   │   │   views.py
│   │   │   __init__.py
│   │   │   
│   │   ├───management
│   │   │   │   ...
│   │   │           
│   │   ├───migrations
│   │   │   │   0001_initial.py
│   │   │   │   ...
│           
├───docs                                      <Docs directory>
│   ├───automated
│   └───dev-manuals
│           testing.md
|           ...
│           
├───htmlcov                                  <Directory for generated html coverages>
│       index.html
│       ...
│       
├───planimbly                                <Django project directory>
│   │   asgi.py
│   │   context_processors.py
│   │   settings.py
│   │   urls.py
│   │   wsgi.py
│   │   __init__.py
│   
│           
├───scripts                                  <Algorithm directory>
│   │   classes.py
│   │   run_algorithm.py
│   │   __init__.py
│   │   
│   ├───docs
│   │       input_output_definition.txt
│   │       Skan_grafików.pdf
│   │       wymagania_algorytmu_do_maja.txt
│   │       
│   ├───tests
│   │       test_main.py
│   
│           
├───static                                  <Static files directory for django>
│   ├───css
│   │   │   nav-sidebar.css
│   │   │   
│   │   ├───accounts
│   │   │       style.css
│   │   │       
│   │   ├───organizations
│   │   │       employees_manage.css
│   │   │       employee_to_unit.css
│   │   │       units_manage.css
│   │   │       workplace_manage.css
│   │   │       
│   │   └───schedules
│   │           schedule.css
│   │           shiftType_manage.css
│   │           
│   ├───img
│   │       Loading_icon.gif
│   │       Logo-Favicon.svg
│   │       Logo-Main-Big2.svg
│   │       
│   └───js
│       └───components
│               WorkCalendar.js
│               
├───templates                               <Django templates>
│   │   base.html
│   │   
│   ├───accounts
│   │       login.html
│   │       logout.html
│   │       password_change.html
│   │       password_reset.html
│   │       password_reset_complete.html
│   │       password_reset_confirm.html
│   │       password_reset_done.html
│   │       
│   ├───organizations
│   │       employees_import.html
│   │       employees_manage.html
│   │       employee_to_unit_workplace.html
│   │       organization_create.html
│   │       units_manage.html
│   │       workplace_manage.html
│   │       
│   └───schedules
│           schedule_manage.html
│           shiftType_manage.html
│           
└───venv                                  <Python virtual environment>
    │   pyvenv.cfg
    │   
    ├───Include
    ├───Lib              
    └───Scripts
            activate
            activate.bat
            Activate.ps1
            ...
```
