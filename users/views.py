# logic of each route
from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseNotFound
from django.core.cache import cache
from datetime import timedelta
from django.contrib import messages
from backend.services.database import add_user_to_db, get_user_by_email, users_collection
from backend.utils.notification import send_email
from backend.utils.security import hash_password
from bson import ObjectId

def home_view(request):
    return render(request, 'home.html')

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
        user = get_user_by_email(email, password)
        if not user:
            messages.error(request, "Invalid credentials.")
            return render(request, "login.html")
        print("user found")
        return redirect(f"/user/{str(user['_id'])}/")
    return render(request, "login.html")

def about_view(request):
    pass

def dashboard_view(request, user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return HttpResponseNotFound("User not found")
    context={'user':user}
    return render(request,'dashboard.html',context)

def settings_view(request):
    # user_id = 
    # context = {'user_id':user_id}
    # return render(request, 'settings.html',context)
    pass

def forgot_password_view(request):
    if request.method=='POST':
        email=request.POST.get('email')
        user = users_collection.find_one({'email':email})
        if user:
            generated_otp = send_email(email)
            if not generated_otp:
               messages.error(request, "Some error occured while sending the email") 
               return render(request, 'forgot_password.html')
           
            cache.set(email,generated_otp, timeout=300)
            request.session['reset_email']=email
            messages.success(request, "Email has been sent to your account")
            return redirect("reset_password")
        
        else:
            messages.error(request, "No account found with this email.")
    return render(request, 'forgot_password.html')

def reset_password_view(request):
    email=request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    
    if request.method=='POST':
        entered_otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        recheck_new_password = request.POST.get('recheck_new_password')
        
        saved_otp = cache.get(email)
        if not saved_otp:
            messages.error(request, "OTP expired. Please try again.")
            return redirect('forgot-password')
        
        if str(entered_otp).strip()==str(saved_otp).strip():
            cache.delete(email)
            if new_password==recheck_new_password:
                users_collection.update_one(
                    {'email':email},
                    {'$set':{'password':hash_password(new_password)}}
                )
                messages.success(request, "Password reset successful.")
                del request.session["reset_email"]
                return redirect("login")
            else:
                messages.error(request, "Passwords don't match!")
        else:
            messages.error(request, "Invalid OTP.")
    return render(request, 'reset_password.html')

def manage_notes_view(request):
    pass

def chatbot_view(request):
    pass