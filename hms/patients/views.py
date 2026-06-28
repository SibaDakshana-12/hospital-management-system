from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import patient_required
from .services import PatientService
from bookings.services import BookingService, SlotAlreadyBookedError
from bookings.models import Booking
from calendar_service.services import GoogleCalendarService
from email_client.services import EmailService


@login_required
@patient_required
def dashboard(request):
    slots = PatientService.get_available_slots()
    my_bookings = Booking.objects.filter(patient=request.user).select_related("slot", "slot__doctor")
    return render(request, "patients/dashboard.html", {"slots": slots, "my_bookings": my_bookings})


@login_required
@patient_required
def book_slot(request, slot_id):
    if request.method == "POST":
        try:
            booking = BookingService.book_slot(patient=request.user, slot_id=slot_id)
            messages.success(request, "Booking confirmed!")

            GoogleCalendarService.create_booking_events(booking)
            EmailService.send_booking_confirmation(booking)

        except SlotAlreadyBookedError as e:
            messages.error(request, str(e))

    return redirect("patients:dashboard")