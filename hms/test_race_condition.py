import os
import django
import threading

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User
from doctors.models import Availability
from bookings.services import BookingService, SlotAlreadyBookedError

results = []

def attempt_booking(patient, slot_id, label):
    try:
        booking = BookingService.book_slot(patient=patient, slot_id=slot_id)
        results.append(f"{label}: SUCCESS - booking id {booking.id}")
    except SlotAlreadyBookedError as e:
        results.append(f"{label}: FAILED - {e}")


def main():
    # Adjust these usernames to match real patients/slot in your DB
    patient1 = User.objects.get(username="patient_a")
    patient2 = User.objects.get(username="patient_b")
    slot = Availability.objects.filter(is_booked=False).first()

    if not slot:
        print("No free slot found. Create one first via the doctor dashboard.")
        return

    print(f"Testing race condition on slot id={slot.id} ({slot.date} {slot.start_time}-{slot.end_time})")

    t1 = threading.Thread(target=attempt_booking, args=(patient1, slot.id, "Patient A"))
    t2 = threading.Thread(target=attempt_booking, args=(patient2, slot.id, "Patient B"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("\n--- RESULTS ---")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()