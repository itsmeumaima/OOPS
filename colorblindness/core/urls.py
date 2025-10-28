from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),          # Login page (default)
    path("signup/", views.signup_view, name="signup"), # Signup page
    path("dashboard/", views.dashboard, name="dashboard"), # Dashboard
    path("logout/", views.logout_view, name="logout"), # Logout
    path("simulator/", views.simulator_view, name="simulator"), 
    path("color-detector/", views.color_detector_view, name="color_detector"),
    path('corrector/', views.corrector_view, name='corrector'),
    path("test/", views.color_test_view, name="color_test"),
]
