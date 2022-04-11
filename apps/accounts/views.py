from django.shortcuts import render

# Create your views here.
from django.views import View


class PasswordActivateView(View):
    def get(self, request, uidb64, token):
        pass
