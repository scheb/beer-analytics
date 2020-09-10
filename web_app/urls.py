from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('imprint', views.imprint, name='imprint'),
    path('privacy-policy', views.privacy_policy, name='privacy_policy'),

    path('trends/', views.home, name='trends'),
    path('hops/', views.home, name='hop_overview'),
    path('fermentables/', views.home, name='fermentable_overview'),

    path('styles/', views.style_overview, name='style_overview'),
    path('styles/<str:category_slug>', views.style_category_detail, name='style_category_detail'),
    path('styles/<str:category_slug>/<str:slug>', views.style_detail, name='style_detail'),
]
