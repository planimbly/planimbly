import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import TemplateView
from .forms import *


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

            # Password activate generation:
            # - encoded uid
            # - token
            # - get domain
            # - generate url with parameters
            uidb64 = urlsafe_base64_encode(force_bytes(manager.id))
            token = PasswordResetTokenGenerator().make_token(manager)
            domain = get_current_site(request).domain
            url = domain + reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
            # Sending ready url with email to manager
            email_subject = 'New account in Planimbly system'
            email_body = 'New account: ' + manager.username + '. Please change password on url: ' + url
            email = EmailMessage(
                email_subject,
                email_body,
                'noreply@planimbyl.com',
                [manager.email]
            )
            email.send()
            #print(url)
            return HttpResponseRedirect(reverse('home'))
        else:
            context = super(OrganizationCreateView, self).get_context_data()
            context['organization_create_form'] = OrganizationCreateForm(self.request.POST)
            context['manager_create_form'] = ManagerCreateForm(self.request.POST)
            return self.render_to_response(context)


