from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def overview(request: HttpRequest) -> HttpResponse:
    return render(request, 'yeast/overview.html')
