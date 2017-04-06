from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.http import JsonResponse
import json

def index(request):
    json_data = open('main/static/data.json')
    data = json.load(json_data)
    context = {
        'spaces':data
    }
    return render(request, 'main/index.html', context)

def spaces(request):
    json_data = open('main/static/data.json')
    data = json.load(json_data)
    return JsonResponse({'spaces':data})

def starting(request):
    return render(request, 'main/starting.html')


def join(request):
    return render(request, 'main/join.html')


def join_supporter(request):
    return render(request, 'main/supporter.html')

class Login(View):
    def get(self, request):
        return render(request, 'main/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'main/login.html')


def logout_view(request):
    logout(request)
    return redirect('/')
