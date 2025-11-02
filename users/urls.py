# maps url path to functions. define the routes
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home_view,name='home'),
    path('signup/',views.signup_view, name='signup'),
    path('login/',views.login_view, name='login'),
    path('user/<str:user_id>/', views.dashboard_view, name="dashboard"),
    path('user/<str:user_id>/settings/', views.settings_view, name="settings")
]