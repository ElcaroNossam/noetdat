import secrets
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse


def generate_verification_token():
    """Генерирует случайный токен для подтверждения email."""
    return secrets.token_urlsafe(32)


def send_verification_email(user, request):
    """Отправляет HTML email с ссылкой для подтверждения."""
    token = generate_verification_token()
    user.profile.email_verification_token = token
    user.profile.save()
    
    verification_url = request.build_absolute_uri(
        reverse("accounts:verify_email", args=[token])
    )
    
    subject = "Подтвердите ваш email - Noet-Dat"
    
    # Plain text версия (для клиентов без поддержки HTML)
    text_message = f"""Здравствуйте, {user.username}!

Пожалуйста, подтвердите ваш email адрес, перейдя по ссылке:
{verification_url}

После подтверждения email ваш аккаунт будет отправлен на модерацию администратору.

Если вы не регистрировались на Noet-Dat, просто проигнорируйте это письмо.

С уважением,
Команда Noet-Dat"""
    
    # HTML версия с табличной версткой и инлайн стилями
    html_message = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Подтверждение email - Noet-Dat</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #0b0c10;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #0b0c10; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 20px 0;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="background-color: #1f2833; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #45a29e 0%, #66fcf1 100%); padding: 30px 40px; text-align: center;">
                            <h1 style="margin: 0; color: #0b0c10; font-size: 28px; font-weight: 700; letter-spacing: 1px;">Noet-Dat</h1>
                            <p style="margin: 10px 0 0 0; color: #0b0c10; font-size: 14px; opacity: 0.9;">Crypto Screener Platform</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px 0; color: #66fcf1; font-size: 24px; font-weight: 600;">Здравствуйте, {user.username}!</h2>
                            
                            <p style="margin: 0 0 20px 0; color: #c5c6c7; font-size: 16px; line-height: 1.6;">
                                Спасибо за регистрацию на <strong style="color: #66fcf1;">Noet-Dat</strong>! 
                                Для завершения регистрации и получения доступа к платформе, пожалуйста, подтвердите ваш email адрес.
                            </p>
                            
                            <p style="margin: 0 0 30px 0; color: #c5c6c7; font-size: 16px; line-height: 1.6;">
                                После подтверждения email ваш аккаунт будет отправлен на модерацию администратору. 
                                Вы получите уведомление после одобрения.
                            </p>
                            
                            <!-- Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #45a29e 0%, #66fcf1 100%); color: #0b0c10; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; letter-spacing: 0.5px; box-shadow: 0 4px 15px rgba(102, 252, 241, 0.3);">
                                            Подтвердить email
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Alternative link -->
                            <p style="margin: 30px 0 0 0; color: #888; font-size: 14px; line-height: 1.6;">
                                Если кнопка не работает, скопируйте и вставьте следующую ссылку в браузер:
                            </p>
                            <p style="margin: 10px 0 0 0; word-break: break-all;">
                                <a href="{verification_url}" style="color: #66fcf1; text-decoration: underline; font-size: 14px;">{verification_url}</a>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0b0c10; padding: 30px 40px; text-align: center; border-top: 1px solid #45a29e33;">
                            <p style="margin: 0 0 10px 0; color: #7f8c8d; font-size: 14px; line-height: 1.6;">
                                Если вы не регистрировались на Noet-Dat, просто проигнорируйте это письмо.
                            </p>
                            <p style="margin: 0; color: #7f8c8d; font-size: 12px;">
                                © 2024 Noet-Dat. Все права защищены.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    # Создаем email сообщение с поддержкой HTML
    email = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)
