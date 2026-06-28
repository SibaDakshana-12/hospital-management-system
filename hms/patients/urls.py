from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("book/<int:slot_id>/", views.book_slot, name="book_slot"),
]