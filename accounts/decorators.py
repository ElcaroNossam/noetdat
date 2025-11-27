from functools import wraps
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


def access_required(view_func):
    """
    Декоратор для проверки доступа к скринеру.
    Пользователь должен быть:
    1. Авторизован
    2. Подтвердил email
    3. Одобрен администратором
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "Authentication required"}, status=401)
            messages.warning(request, "Войдите в систему для доступа к скринеру.")
            return redirect(reverse("accounts:login") + "?next=" + request.path)
        
        if not hasattr(request.user, "profile"):
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "Profile not found"}, status=403)
            messages.error(request, "Профиль не найден. Обратитесь к администратору.")
            return redirect("accounts:profile")
        
        profile = request.user.profile
        
        if not profile.email_verified:
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "Email verification required"}, status=403)
            messages.warning(
                request,
                "Пожалуйста, подтвердите ваш email адрес для доступа к скринеру. "
                "Проверьте вашу почту."
            )
            return redirect("accounts:profile")
        
        if not profile.admin_approved:
            if request.path.startswith("/api/"):
                return JsonResponse({"error": "Admin approval required"}, status=403)
            messages.info(
                request,
                "Ваш аккаунт ожидает одобрения администратором. "
                "Вы получите уведомление после одобрения."
            )
            return redirect("accounts:profile")
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

