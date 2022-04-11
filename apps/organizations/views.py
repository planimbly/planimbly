from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.urls import reverse
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
            manager = Employee.objects.create_user(data['email'], data['username'],
                                                   data['first_name'], data['last_name'], password, org, True)

            # Password activate generation:
            # - get domain
            # - get relative url
            # - enocded uid
            # - token
            #domain = get_current_site(request).domain
            token = PasswordResetTokenGenerator().make_token(manager)
            print(token)

            # DOKONCZYCZ TWORZENIE USERA + wysyłanie maila z linkiem aktywacyjnym
            return HttpResponseRedirect(reverse('home'))
        else:
            context = super(OrganizationCreateView, self).get_context_data()
            context['organization_create_form'] = OrganizationCreateForm(self.request.GET or None)
            context['manager_create_form'] = ManagerCreateForm(self.request.GET or None)
            return self.render_to_response(context)


