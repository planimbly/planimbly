from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

from ....accounts.models import Employee
from ....organizations.models import Organization, Unit, Workplace, WorkplaceClosing
from ....schedules.models import JobTime, FreeDay, Schedule, ShiftType, Preference, Assignment, Shift, Absence

GROUPS_PERMISSIONS = {
    'supervisor': {
        Employee: ['add', 'change', 'delete', 'view'],
        Organization: ['add', 'change', 'delete', 'view'],
        Unit: ['add', 'change', 'delete', 'view'],
        Workplace: ['add', 'change', 'delete', 'view'],
        WorkplaceClosing: ['add', 'change', 'delete', 'view'],
        JobTime: ['add', 'change', 'delete', 'view'],
        FreeDay: ['add', 'change', 'delete', 'view'],
        Schedule: ['add', 'change', 'delete', 'view'],
        ShiftType: ['add', 'change', 'delete', 'view'],
        Preference: ['add', 'change', 'delete', 'view'],
        Assignment: ['add', 'change', 'delete', 'view'],
        Shift: ['add', 'change', 'delete', 'view'],
        Absence: ['add', 'change', 'delete', 'view'],

    },
    'employee': {
        Schedule: ['view'],
        Shift: ['view'],
    }
}


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Create default groups"

    def handle(self, *args, **options):
        # Loop groups
        for group_name in GROUPS_PERMISSIONS:

            # Get or create group
            group, created = Group.objects.get_or_create(name=group_name)

            # Loop models in group
            for model_cls in GROUPS_PERMISSIONS[group_name]:

                # Loop permissions in group/model
                for perm_index, perm_name in \
                        enumerate(GROUPS_PERMISSIONS[group_name][model_cls]):

                    # Generate permission name as Django would generate it
                    codename = perm_name + "_" + model_cls._meta.model_name

                    try:
                        # Find permission object and add to group
                        perm = Permission.objects.get(codename=codename)
                        group.permissions.add(perm)
                        '''self.stdout.write("Adding "
                                          + codename
                                          + " to group "
                                          + group.__str__())'''
                    except Permission.DoesNotExist:
                        '''self.stdout.write(codename + " not found")'''

        employees = Employee.objects.filter(is_supervisor=False).filter(is_staff=False).filter(is_superuser=False)
        supervisors = Employee.objects.filter(is_supervisor=True)
        emp_group = Group.objects.filter(name='employee').first()
        sup_group = Group.objects.filter(name='supervisor').first()
        for e in employees:
            e.groups.add(emp_group)
        for s in supervisors:
            s.groups.add(sup_group)
        # print("Done!")
