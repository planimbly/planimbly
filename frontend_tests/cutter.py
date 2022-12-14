from bs4 import BeautifulSoup
import os

rootdir = os.path.join(os.getcwd(), 'templates')

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        file_path = os.path.join(subdir, file)
        savefile_path = os.getcwd() + '/frontend_tests/unit/templates/' + file.split('.')[0] + '.js'
        js = None
        condition = \
            file != 'base.html' and \
            file != 'login.html' and \
            file != 'logout.html' and \
            file != 'password_change.html' and \
            file != 'password_reset.html' and \
            file != 'password_reset_done.html' and \
            file != 'password_reset_confirm.html' and \
            file != 'password_reset_complete.html' and \
            file != 'employees_import.html' and \
            file != 'organization_create.html' and \
            file != 'schedule_generating.html'

        print(file_path)
        print(savefile_path)

        if file == 'base.html':
            js = BeautifulSoup(open(file_path, 'r'), 'html.parser').find('script', attrs={"type": "application/javascript"}).text

        if condition:
            js = BeautifulSoup(open(file_path, 'r'), 'html.parser').find('script', attrs={"type": "module"}).text

        if js is not None:
            open(savefile_path, 'w').write(js)
