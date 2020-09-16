from django.shortcuts import render


def overview(request):
    return render(request, 'yeast/overview.html')
