from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.manage_notes_view, name="manage_notes"),
]