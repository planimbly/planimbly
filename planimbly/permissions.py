from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework import permissions


class Issupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        if (request.user and request.user.groups.filter(name='supervisor')) or request.user.is_superuser:
            return True
        return False


class Isemployee(permissions.BasePermission):
    def has_permission(self, request, view):
        if (request.user and request.user.groups.filter(name='employee')) or request.user.is_superuser:
            return True
        return False


class GroupRequiredMixin(object):
    """
        Function taken from:
        https://gist.github.com/ceolson01/206139a093b3617155a6
    """

    group_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        else:
            if self.group_required is None:
                self.group_required = ['supervisor']
            if request.user.is_superuser:
                return super(GroupRequiredMixin, self).dispatch(request, *args, **kwargs)
            user_groups = []
            for group in request.user.groups.values_list('name', flat=True):
                user_groups.append(group)
            if len(set(user_groups).intersection(self.group_required)) <= 0:
                raise PermissionDenied
        return super(GroupRequiredMixin, self).dispatch(request, *args, **kwargs)
