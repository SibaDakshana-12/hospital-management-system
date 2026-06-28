from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def doctor_required(view_func):
    def check(user):
        if user.is_authenticated and user.is_doctor():
            return True
        raise PermissionDenied
    return user_passes_test(check)(view_func)


def patient_required(view_func):
    def check(user):
        if user.is_authenticated and user.is_patient():
            return True
        raise PermissionDenied
    return user_passes_test(check)(view_func)