from django.urls import path
from . import views

app_name = "calendar_service"

urlpatterns = [
    path("oauth/connect/", views.connect_calendar, name="connect"),
    path("oauth/callback/", views.oauth_callback, name="callback"),
]