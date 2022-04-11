import base64
from _csv import reader

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import TemplateView
from .forms import *


def generate_passwd_reset_url(user, request):
    # Password activate generation:
    # - encoded uid
    # - token
    # - get domain
    # - generate url with parameters
    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    token = PasswordResetTokenGenerator().make_token(user)
    domain = get_current_site(request).domain
    url = domain + reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
    return url


def send_user_activation_mail(user, request):
    url = generate_passwd_reset_url(user, request)
    # Sending url with email to user
    email_subject = 'New account in Planimbly system'
    email_body = 'New account: ' + user.username + '. Please change password on url: ' + url
    email = EmailMessage(
        email_subject,
        email_body,
        'noreply@planimbyl.com',
        [user.email]
    )
    email.send()


class OrganizationCreateView(TemplateView):
    template_name = 'organizations/organization_create.html'

    def get(self, request, *args, **kwargs):
        context = super(OrganizationCreateView, self).get_context_data()
        context['organization_create_form'] = OrganizationCreateForm(self.request.GET or None)
        context['manager_create_form'] = ManagerCreateForm(self.request.GET or None)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        organization_create_form = OrganizationCreateForm(self.request.POST)
        manager_create_form = ManagerCreateForm(self.request.POST)
        if organization_create_form.is_valid() and manager_create_form.is_valid():
            data = manager_create_form.cleaned_data
            org = organization_create_form.save()
            password = Employee.objects.make_random_password()
            manager = get_user_model().objects.create_user(data['email'], data['username'],
                                                           data['first_name'], data['last_name'], password, org, True)
            send_user_activation_mail(manager, self.request)
            return HttpResponseRedirect(reverse('home'))
        else:
            context = super(OrganizationCreateView, self).get_context_data()
            context['organization_create_form'] = OrganizationCreateForm(self.request.POST)
            context['manager_create_form'] = ManagerCreateForm(self.request.POST)
            return self.render_to_response(context)


class EmployeesImportView(TemplateView):
    template_name = 'organizations/employees_import.html'

    def post(self, request, *args, **kwargs):
        file = request.FILES['employeesList']
        org = self.request.user.user_org
        # TODO Sprawdzać kodowanie pliku, jak?
        # TODO Zabezpieczyć dodawanie plików, sprawdzanie ich poprawności
        file_data = file.read().decode('utf-8')
        lines = file_data.split('\r\n')
        user_list = []
        for line in lines:
            user_list.append(line.split(','))

        for line in user_list:
            password = Employee.objects.make_random_password()
            employee = get_user_model().objects.create_user(line[0], line[1],
                                                            line[2], line[3], password, org, False)
            send_user_activation_mail(employee, self.request)

        return HttpResponseRedirect(reverse('employees_import'))
