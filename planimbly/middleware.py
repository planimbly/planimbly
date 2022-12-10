from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.schedules.models import AlgorithmTask
from apps.schedules.views import CheckAlgorithView


class DenyAccesHueyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            view_class = view_func.view_class
        except:
            view_class = None

        if not request.user.is_anonymous:
            if AlgorithmTask.objects.filter(organization_id=request.user.user_org_id).exists():
                if view_class is not None:
                    if view_class == CheckAlgorithView:
                        return None
                rendered = render_to_string('schedules/schedule_generating.html')
                return HttpResponse(rendered)
        return None
