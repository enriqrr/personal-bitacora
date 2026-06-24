from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render


def health(request):
    return HttpResponse("ok", content_type="text/plain")


def home(request):
    return render(request, "public/home.html")


@login_required
def dashboard(request):
    return render(request, "owner/dashboard.html")
