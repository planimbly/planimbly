from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import TemplateView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from planimbly.permissions import GroupRequiredMixin, Issupervisor
from .forms import ManagerCreateForm, OrganizationCreateForm
from .models import Unit, Workplace, WorkplaceClosing
from .serializers import WorkplaceSerializer, UnitSerializer, WorkplaceClosingSerializer
from ..accounts.models import Employee
from ..accounts.serializers import EmployeeSerializer


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


# TODO DO POPRAWY TWORZENIE ORGANIZACJI + UŻYTKOWNIKÓW, dużo zmian było
class OrganizationCreateView(GroupRequiredMixin, TemplateView):
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
            v_data = manager_create_form.cleaned_data
            org = organization_create_form.save()
            password = Employee.objects.make_random_password()
            manager = get_user_model().objects.create_user(email=v_data.get('email'), username=v_data.get('username'),
                                                           first_name=v_data.get('first_name'),
                                                           last_name=v_data.get('last_name'),
                                                           order_number=v_data.get('order_number'), password=password,
                                                           user_org=org)
            send_user_activation_mail(manager, self.request)
            return HttpResponseRedirect(reverse('employees_manage'))
        else:
            context = super(OrganizationCreateView, self).get_context_data()
            context['organization_create_form'] = OrganizationCreateForm(self.request.POST)
            context['manager_create_form'] = ManagerCreateForm(self.request.POST)
            return self.render_to_response(context)


class EmployeesManageView(GroupRequiredMixin, TemplateView):
    template_name = 'organizations/employees_manage.html'


class EmployeeToUnitWorkplaceView(GroupRequiredMixin, TemplateView):
    template_name = 'organizations/employee_to_unit_workplace.html'

    def get_context_data(self, **kwargs):
        user_org = self.request.user.user_org
        context = super().get_context_data(**kwargs)
        if not Workplace.objects.filter(workplace_unit__unit_org=user_org).exists():
            context['is_any_workplace'] = False
            return context
        units = Unit.objects.filter(unit_org=user_org)
        select_unit = list(units.values(
            'id', 'name'))
        workplace_list = Workplace.objects.filter(workplace_unit__in=units)
        select_workplace = dict()
        for obj in workplace_list:
            select_workplace.setdefault(obj.workplace_unit_id, []).append({"id": obj.id, "name": obj.name})

        context['default_unit'] = select_unit[0]['id']
        context['select_unit'] = select_unit
        context['select_workplace'] = select_workplace
        context['is_any_workplace'] = True
        return context


class UnitsManageView(GroupRequiredMixin, TemplateView):
    template_name = 'organizations/units_manage.html'


class WorkplaceManageView(GroupRequiredMixin, TemplateView):
    template_name = 'organizations/workplace_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_org = self.request.user.user_org
        if not Unit.objects.filter(unit_org=user_org).exists():
            context['is_any_unit'] = False
            return context
        select_unit = list(Unit.objects.filter(unit_org=user_org).values('id', 'name'))
        context['is_any_unit'] = True
        context['default_unit'] = select_unit[0]['id']
        context['select_unit'] = select_unit
        return context


# API TEMPLATES
class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [Issupervisor]

    def get_queryset(self):
        queryset = Unit.objects.filter(unit_org=self.request.user.user_org)
        return queryset

    def perform_create(self, serializer):
        v_data = serializer.validated_data
        unit = Unit(name=v_data['name'], unit_org=self.request.user.user_org)
        unit.save()


class WorkplaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkplaceSerializer
    permission_classes = [Issupervisor]

    def get_queryset(self):
        unit_pk = self.kwargs['unit_pk']
        queryset = Workplace.objects.filter(workplace_unit=unit_pk)
        return queryset

    def perform_create(self, serializer):
        v_data = serializer.validated_data
        unit = Unit.objects.filter(pk=self.kwargs['unit_pk']).first()
        workplace = Workplace(name=v_data['name'], workplace_unit=unit)
        workplace.save()


class EmployeesImportApiView(APIView):
    permission_classes = [Issupervisor]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('employeeList')
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
            employee = get_user_model().objects.create_user(email=line[0], username=line[1], first_name=line[2],
                                                            last_name=line[3], order_number=line[4], job_time=line[5],
                                                            password=password, user_org=org, is_supervisor=False)
            send_user_activation_mail(employee, self.request)

        return Response()


class EmployeeToUnitApiView(APIView):
    permission_classes = [Issupervisor]

    def get(self, request, unit_workplace_pk):
        unit = Unit.objects.filter(id=unit_workplace_pk).first()
        employee_unit_list = Employee.objects.filter(user_unit=unit)
        employee_list = Employee.objects.filter(user_org=self.request.user.user_org).exclude(id__in=employee_unit_list)
        serializer1 = EmployeeSerializer(employee_list, many=True)
        serializer2 = EmployeeSerializer(employee_unit_list, many=True)
        serializer = [serializer1.data, serializer2.data]
        return Response(serializer)

    def post(self, request, unit_workplace_pk):
        if request.data.get('action') and request.data.get('pk'):
            employee = Employee.objects.filter(id=request.data['pk']).first()
            unit = Unit.objects.filter(id=unit_workplace_pk).first()
            if employee is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if request.data['action'] == 'add':
                employee.user_unit.add(unit)
            elif request.data['action'] == 'delete':
                employee.user_unit.remove(unit)
                for workplace in Workplace.objects.filter(workplace_unit=unit):
                    employee.user_workplace.remove(workplace)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class EmployeeToWorkplaceApiView(APIView):
    permission_classes = [Issupervisor]

    def get(self, request, unit_workplace_pk):
        workplace = Workplace.objects.filter(id=unit_workplace_pk).first()
        employee_workplace_list = Employee.objects.filter(user_workplace=workplace)
        employee_list = Employee.objects.filter(user_unit=workplace.workplace_unit).exclude(
            id__in=employee_workplace_list)
        serializer1 = EmployeeSerializer(employee_list, many=True)
        serializer2 = EmployeeSerializer(employee_workplace_list, many=True)
        serializer = [serializer1.data, serializer2.data]
        return Response(serializer)

    def post(self, request, unit_workplace_pk):
        if request.data.get('action') and request.data.get('pk'):
            employee = Employee.objects.filter(id=request.data['pk']).first()
            workplace = Workplace.objects.filter(id=unit_workplace_pk).first()
            if employee is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if request.data['action'] == 'add':
                employee.user_workplace.add(workplace)
            elif request.data['action'] == 'delete':
                employee.user_workplace.remove(workplace)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class WorkplaceClosingViewSet(viewsets.ModelViewSet):
    queryset = WorkplaceClosing.objects.all()
    serializer_class = WorkplaceClosingSerializer
    permission_classes = [Issupervisor]

    def list(self, request, *args, **kwargs):
        queryset = WorkplaceClosing.objects.filter(workplace__workplace_unit__unit_org_id=request.user.user_org_id)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class WorkplaceClosingView(GroupRequiredMixin, TemplateView):
    template_name = 'organizations/workplace_closing.html'
