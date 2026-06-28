import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings as django_settings
from .models import GoogleCredential

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://127.0.0.1:8080/calendar/oauth/callback/"


class GoogleCalendarService:
    @staticmethod
    def get_auth_flow():
        return Flow.from_client_secrets_file(
            str(django_settings.BASE_DIR / "credentials.json"),
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )

    @staticmethod
    def save_credentials(user, credentials):
        GoogleCredential.objects.update_or_create(
            user=user,
            defaults={
                "token": credentials.token,
                "refresh_token": credentials.refresh_token or "",
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": json.dumps(credentials.scopes),
            },
        )

    @staticmethod
    def get_credentials_for_user(user):
        try:
            cred = user.google_credential
        except GoogleCredential.DoesNotExist:
            return None

        return Credentials(
            token=cred.token,
            refresh_token=cred.refresh_token,
            token_uri=cred.token_uri,
            client_id=cred.client_id,
            client_secret=cred.client_secret,
            scopes=json.loads(cred.scopes),
        )

    @staticmethod
    def create_event(user, title, start_datetime, end_datetime, description=""):
        credentials = GoogleCalendarService.get_credentials_for_user(user)
        if not credentials:
            print(f"[CALENDAR] No Google credentials for {user.username}, skipping event creation.")
            return None

        service = build("calendar", "v3", credentials=credentials)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_datetime.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_datetime.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        return service.events().insert(calendarId="primary", body=event).execute()

    @staticmethod
    def create_booking_events(booking):
        from datetime import datetime
        slot = booking.slot
        doctor = slot.doctor
        patient = booking.patient

        start_dt = datetime.combine(slot.date, slot.start_time)
        end_dt = datetime.combine(slot.date, slot.end_time)

        GoogleCalendarService.create_event(
            user=patient,
            title=f"Appointment with Dr. {doctor.username}",
            start_datetime=start_dt,
            end_datetime=end_dt,
            description="Hospital appointment booking",
        )

        GoogleCalendarService.create_event(
            user=doctor,
            title=f"Appointment with {patient.username}",
            start_datetime=start_dt,
            end_datetime=end_dt,
            description="Hospital appointment booking",
        )