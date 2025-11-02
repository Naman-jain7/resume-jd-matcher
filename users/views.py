# logic of each route
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from backend.services.database import add_user_to_db, get_user_by_email

def home_view(request):
    return render(request, 'home.html')

def dashboard_view(request, user_id):
    return render(request,'dashboard.html')

def settings_view(request):
    # user_id = 
    # context = {'user_id':user_id}
    # return render(request, 'settings.html',context)
    pass

# Create your views here.
def signup_view(request):
    if request.method=="POST":
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email=request.POST.get('email')
        password=request.POST.get('password')
        
        user = add_user_to_db(first_name, last_name, email, password)
        if not user:
            messages.error(request, "Error creating account")
            return render(request, "signup.html")
        
        user_id=str(user['_id'])
        messages.success(request, "Account created successfully")
        return redirect(f"/user/{user_id}")
    
    return render(request, "signup.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = get_user_by_email(email,password)
        if not user:
            messages.error(request, "Invalid credentials.")
            return render(request, "login.html")
        return redirect(f"/user/{user['user_id']}")
    return render(request, "login.html")