import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def generate_verification_token():
    """Генерирует случайный токен для подтверждения email."""
    return secrets.token_urlsafe(32)


def send_verification_email(user, request):
    """Отправляет email с ссылкой для подтверждения."""
    token = generate_verification_token()
    user.profile.email_verification_token = token
    user.profile.save()
    
    verification_url = request.build_absolute_uri(
        reverse("accounts:verify_email", args=[token])
    )
    
    subject = "Подтвердите ваш email - Noet-Dat"
    message = f"""
Здравствуйте, {user.username}!

Пожалуйста, подтвердите ваш email адрес, перейдя по ссылке:
{verification_url}

После подтверждения email ваш аккаунт будет отправлен на модерацию администратору.

Если вы не регистрировались на Noet-Dat, просто проигнорируйте это письмо.

С уважением,
Команда Noet-Dat
"""
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

