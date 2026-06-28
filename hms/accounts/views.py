from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm
from .models import User
from email_client.services import EmailService

def landing(request):
    return render(request, "accounts/landing.html")

class SignUpView(View):
    template_name = "accounts/signup.html"

    def get(self, request):
        form = SignUpForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Trigger SIGNUP_WELCOME email via serverless function
            EmailService.send_signup_welcome(user)

            return redirect("accounts:dashboard_redirect")
        return render(request, self.template_name, {"form": form})

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


@login_required
def dashboard_redirect(request):
    if request.user.is_doctor():
        return redirect("doctors:dashboard")
    return redirect("patients:dashboard")