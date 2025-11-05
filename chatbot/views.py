from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpResponseNotFound
from django.core.cache import cache
from datetime import timedelta
from django.contrib import messages

def chatbot(request):
    pass