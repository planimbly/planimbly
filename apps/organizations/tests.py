from django.test import TestCase, Client
from rest_framework.test import APIClient
from .models import Organization
from ..accounts.models import Employee
from django.core.management import call_command


class organization_test_case(TestCase):

    api_client = APIClient()

    def setUp(self):
        Organization.objects.create(name='Uniwersytet')
        user = Employee.objects.create(email='admin@wp.pl', username='admin', first_name='admin',\
                                       last_name='admin', order_number=0, user_org=Organization.objects.get(name='Uniwersytet'),\
                                       job_time=1, is_supervisor=True, is_superuser=True)
        user.set_password('admin12')
        user.save()

        call_command('create_groups')
        

    def test_organization_models(self):
        org = Organization.objects.get(name='Uniwersytet')
        admin = Employee.objects.get(username='admin')

        self.assertEqual(org.__str__(), 'Uniwersytet')
        self.assertEqual(admin.username, 'admin' )


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
    
    
    def test_api_post(self):
        user = Employee.objects.get(username='admin')
        self.api_client.force_authenticate(user=user)

        response = self.api_client.post('/organizations/api/unit/', {
            "id": 1,
            "name": "WMI"
        })

        self.assertEqual(response.status_code, 201)
    

    def test_api_get(self):
        user = Employee.objects.get(username='admin')
        self.api_client.force_authenticate(user=user)

        response = self.api_client.get('/organizations/api/unit/')

        self.assertEqual(response.status_code, 200)

        print(response.json())
