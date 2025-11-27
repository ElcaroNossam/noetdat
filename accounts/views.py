from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.models import User

from .forms import LoginForm, RegisterForm
from .utils import send_verification_email


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            
            try:
                send_verification_email(user, request)
                messages.info(
                    request,
                    "Регистрация успешна! Пожалуйста, проверьте вашу почту и подтвердите email адрес."
                )
            except Exception as e:
                messages.error(
                    request,
                    f"Ошибка отправки email: {e}. Обратитесь к администратору."
                )
            
            return redirect("accounts:login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def verify_email(request, token):
    """Подтверждение email по токену."""
    try:
        from .models import Profile
        profile = get_object_or_404(Profile, email_verification_token=token)
        
        if profile.email_verified:
            messages.info(request, "Email уже подтвержден.")
        else:
            profile.email_verified = True
            profile.email_verification_token = ""
            profile.save()
            messages.success(
                request,
                "Email подтвержден! Ваш аккаунт отправлен на модерацию администратору. "
                "Вы получите уведомление после одобрения."
            )
        
        return redirect("accounts:login")
    except Exception as e:
        messages.error(request, f"Ошибка подтверждения email: {e}")
        return redirect("accounts:login")


class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("screener:list")


# noinspection PyUnusedLocal
@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def resend_verification(request):
    """Повторная отправка email для подтверждения."""
    if request.method == "POST":
        if not hasattr(request.user, "profile"):
            messages.error(request, "Профиль не найден.")
            return redirect("accounts:profile")
        
        if request.user.profile.email_verified:
            messages.info(request, "Email уже подтвержден.")
            return redirect("accounts:profile")
        
        try:
            send_verification_email(request.user, request)
            messages.success(request, "Письмо с подтверждением отправлено на ваш email.")
        except Exception as e:
            messages.error(request, f"Ошибка отправки email: {e}")
    
    return redirect("accounts:profile")


