from django.db import models
from django.conf import settings
from doctors.models import Availability

class Booking(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        limit_choices_to={"role": "PATIENT"},
    )
    slot = models.OneToOneField(
        Availability,
        on_delete=models.CASCADE,
        related_name="booking",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} -> {self.slot}"