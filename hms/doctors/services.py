from datetime import datetime, timedelta
from .models import Availability


class DoctorService:
    @staticmethod
    def get_own_slots(doctor):
        return Availability.objects.filter(doctor=doctor)

    @staticmethod
    def create_slots(doctor, date, start_time, end_time, duration_minutes):
        duration = timedelta(minutes=int(duration_minutes))

        current_start = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)

        created_slots = []
        while current_start + duration <= end_datetime:
            current_end = current_start + duration

            slot, created = Availability.objects.get_or_create(
                doctor=doctor,
                date=date,
                start_time=current_start.time(),
                end_time=current_end.time(),
            )
            if created:
                created_slots.append(slot)

            current_start = current_end

        return created_slots