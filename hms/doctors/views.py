from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import doctor_required
from .forms import AvailabilityForm
from .services import DoctorService


@login_required
@doctor_required
def dashboard(request):
    slots = DoctorService.get_own_slots(request.user)
    form = AvailabilityForm()
    return render(request, "doctors/dashboard.html", {"slots": slots, "form": form})


@login_required
@doctor_required
def create_slot(request):
    if request.method == "POST":
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            DoctorService.create_slots(
                doctor=request.user,
                date=form.cleaned_data["date"],
                start_time=form.cleaned_data["start_time"],
                end_time=form.cleaned_data["end_time"],
                duration_minutes=form.cleaned_data["slot_duration_minutes"],
            )
            return redirect("doctors:dashboard")
    return redirect("doctors:dashboard")