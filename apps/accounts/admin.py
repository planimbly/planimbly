from django.contrib import admin

from .models import Employee


class EmployeeAdmin(admin.ModelAdmin):
    class Meta:
        model = Employee
        fields = '__all__'

    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj is None:  # obj is not None, so this is a change page
            kwargs['exclude'] = ['password', 'last_login', 'user_permissions', 'user_unit', 'user_workplace']
        return super(EmployeeAdmin, self).get_form(request, obj, **kwargs)


admin.site.register(Employee, EmployeeAdmin)
