from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .services import GoogleCalendarService
import os

@login_required
def connect_calendar(request):
    flow = GoogleCalendarService.get_auth_flow()
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")

    request.session["oauth_state"] = state
    request.session["code_verifier"] = flow.code_verifier  # save it

    return redirect(auth_url)


@login_required
def oauth_callback(request):
    print("OAUTHLIB =", os.environ.get("OAUTHLIB_INSECURE_TRANSPORT"))
    code_verifier = request.session.get("code_verifier")
    
    flow = GoogleCalendarService.get_auth_flow()
    flow.code_verifier = code_verifier  # restore it before exchanging the code

    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    GoogleCalendarService.save_credentials(request.user, credentials)
    return redirect("accounts:dashboard_redirect")