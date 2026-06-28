import requests

EMAIL_SERVICE_URL = "http://localhost:3000/sendEmail"


class EmailService:
    @staticmethod
    def _send(trigger_type, recipient, data):
        try:
            response = requests.post(
                EMAIL_SERVICE_URL,
                json={"type": trigger_type, "recipient": recipient, "data": data},
                timeout=5,
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            # Don't let email failures break the actual booking/signup flow
            print(f"[EMAIL ERROR] Could not reach email service: {e}")
            return None

    @staticmethod
    def send_signup_welcome(user):
        return EmailService._send(
            trigger_type="SIGNUP_WELCOME",
            recipient=user.email,
            data={"username": user.username},
        )

    @staticmethod
    def send_booking_confirmation(booking):
        slot = booking.slot
        doctor = slot.doctor
        patient = booking.patient

        # Email to patient
        EmailService._send(
            trigger_type="BOOKING_CONFIRMATION",
            recipient=patient.email,
            data={
                "username": patient.username,
                "date": str(slot.date),
                "start_time": str(slot.start_time),
                "other_party": f"Dr. {doctor.username}",
            },
        )

        # Email to doctor
        EmailService._send(
            trigger_type="BOOKING_CONFIRMATION",
            recipient=doctor.email,
            data={
                "username": doctor.username,
                "date": str(slot.date),
                "start_time": str(slot.start_time),
                "other_party": patient.username,
            },
        )