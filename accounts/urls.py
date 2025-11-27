from django.urls import path

from .views import CustomLoginView, logout_view, profile, register, verify_email, resend_verification

app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile, name="profile"),
    path("verify-email/<str:token>/", verify_email, name="verify_email"),
    path("resend-verification/", resend_verification, name="resend_verification"),
]


