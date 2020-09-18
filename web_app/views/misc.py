from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from recipe_db.models import Recipe


def home(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    return render(request, 'index.html', {'recipes': recipes})


def legal(request: HttpRequest) -> HttpResponse:
    return render(request, 'legal.html')


def about(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    return render(request, 'about.html', {'recipes': recipes})
