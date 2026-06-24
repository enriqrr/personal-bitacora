from django.http import HttpResponse
from django.shortcuts import render

from .permissions import owner_required


def health(request):
    return HttpResponse("ok", content_type="text/plain")


def home(request):
    return render(request, "public/home.html")


@owner_required
def dashboard(request):
    return render(request, "owner/dashboard.html")
