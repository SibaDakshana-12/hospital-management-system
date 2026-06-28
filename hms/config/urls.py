from django.contrib import admin
from django.urls import path, include
from accounts.views import landing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="root_landing"),
    path("accounts/", include("accounts.urls")),
    path("doctors/", include("doctors.urls")),
    path("patients/", include("patients.urls")),
    path("calendar/", include("calendar_service.urls")),
]