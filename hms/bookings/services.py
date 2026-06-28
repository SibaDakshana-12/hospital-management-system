from django.db import transaction, IntegrityError
from doctors.models import Availability
from .models import Booking

class SlotAlreadyBookedError(Exception):
    pass

class BookingService:
    @staticmethod
    def book_slot(patient, slot_id):
        with transaction.atomic():
            try:
                # select_for_update() locks this row until the transaction commits.
                # A second concurrent request for the SAME slot will block here
                # until the first one finishes — then see is_booked=True and fail cleanly.
                slot = Availability.objects.select_for_update().get(id=slot_id)
            except Availability.DoesNotExist:
                raise SlotAlreadyBookedError("Slot does not exist.")

            if slot.is_booked:
                raise SlotAlreadyBookedError("This slot was just booked by another patient.")

            slot.is_booked = True
            slot.save()

            booking = Booking.objects.create(patient=patient, slot=slot)
            return booking