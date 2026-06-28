from django.utils import timezone
from doctors.models import Availability


class PatientService:
    @staticmethod
    def get_available_slots():
        return Availability.objects.filter(
            is_booked=False,
            date__gte=timezone.now().date(),
        ).select_related("doctor")