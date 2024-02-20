from django.test import TestCase
from rest_framework.test import APIClient
from .models import Organization, Unit, Workplace
from ..accounts.models import Employee
from django.core.management import call_command


class organization_test_case(TestCase):

    def setUp(self):
        Organization.objects.create(name='Uniwersytet').save
        Unit.objects.create(name='wydzial', unit_org=Organization.objects.get(name='Uniwersytet')).save
        Workplace.objects.create(name='portiernia', workplace_unit=Unit.objects.get(name='wydzial')).save

        user = Employee.objects.create(email='admin@wp.pl', username='admin', first_name='admin',
                                       last_name='admin', order_number=0,
                                       user_org=Organization.objects.get(name='Uniwersytet'),
                                       job_time=1, is_supervisor=True)
        user.set_password('admin12')
        user.save()

        call_command('create_groups')

    def test_organization_models(self):
        org = Organization.objects.get(name='Uniwersytet')
        unit = Unit.objects.get(name='wydzial')
        wp = Workplace.objects.get(name='portiernia')
        admin = Employee.objects.get(username='admin')

        self.assertEqual(org.name, 'Uniwersytet')
        self.assertEqual(unit.name, 'wydzial')
        self.assertEqual(unit.unit_org, org)
        self.assertEqual(wp.name, 'portiernia')
        self.assertEqual(wp.workplace_unit, unit)
        self.assertEqual(admin.username, 'admin')

    def test_login(self):
        response = self.client.post("/accounts/login/", {
            "username": "admin",
            "password": "Admin123Admin123"
        })

        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        response = self.client.get("/", follow=True)

        self.assertEqual(response.redirect_chain, [('/accounts/login/?next=/', 302)])

        response = self.client.post("/accounts/login/", {
            "username": "admin",
            "password": "admin12"
        }, follow=True)

        self.assertEqual(response.redirect_chain, [('/', 302), ('/schedules/schedule_manage/', 302)])

    def test_site_get(self):
        response = self.client.post("/accounts/login/", {
            "username": "admin",
            "password": "admin12"
        })

        response = self.client.get("/", follow=True)
        response = self.client.get("/organizations/workplace_manage/")

        self.assertEqual(response.status_code, 200)

    api_client = APIClient()

    def test_api_unit_manage(self):
        user = Employee.objects.get(username='admin')
        self.api_client.force_authenticate(user=user)

        response = self.api_client.post('/organizations/api/unit/', {
            "name": "WMI"
        })

        self.assertEqual(response.status_code, 201)

        response = self.api_client.get('/organizations/api/unit/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {'id': 2, 'name': 'WMI'},
            {'id': 1, 'name': 'wydzial'}
        ])

        response = self.api_client.put('/organizations/api/unit/2/', {'name': 'WNPiD'})
        self.assertEqual(response.status_code, 200)
        response = self.api_client.get('/organizations/api/unit/')
        self.assertEqual(response.json(), [
            {'id': 2, 'name': 'WNPiD'},
            {'id': 1, 'name': 'wydzial'}
        ])

        response = self.api_client.delete('/organizations/api/unit/2/')
        self.assertEqual(response.status_code, 204)
        response = self.api_client.get('/organizations/api/unit/')
        self.assertEqual(response.json(), [
            {'id': 1, 'name': 'wydzial'}
        ])

    def test_api_get(self):
        user = Employee.objects.get(username='admin')
        self.api_client.force_authenticate(user=user)

        response = self.api_client.get('/organizations/api/unit/')

        self.assertEqual(response.status_code, 200)
