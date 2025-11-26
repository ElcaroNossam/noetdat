from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import LoginForm, RegisterForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("accounts:profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


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


