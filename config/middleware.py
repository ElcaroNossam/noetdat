"""
Custom middleware for Content Security Policy header and language handling.
"""
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class CSPMiddleware(MiddlewareMixin):
    """
    Middleware to add Content Security Policy header.
    Required for TradingView widget which uses eval().
    """
    
    def process_response(self, request, response):
        # Set CSP header to allow unsafe-eval for TradingView
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://s3.tradingview.com https://*.tradingview.com https://*.binance.com; "
            "style-src 'self' 'unsafe-inline' https://*.tradingview.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' https://*.tradingview.com https://*.binance.com wss://*.binance.com; "
            "frame-src 'self' https://*.tradingview.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "worker-src 'self' blob:;"
        )
        response['Content-Security-Policy'] = csp_policy
        return response


class ForceLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to ensure language cookie is set correctly.
    This runs AFTER LocaleMiddleware to ensure cookie matches the active language.
    """
    
    def process_response(self, request, response):
        # Skip for API requests and admin
        if '/api/' in request.path_info or request.path_info.startswith('/admin/'):
            return response
        
        # Get current language (set by LocaleMiddleware)
        language = translation.get_language()
        
        # Ensure cookie is set to match current language
        if language and translation.check_for_language(language):
            current_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            if current_cookie != language:
                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME,
                    language,
                    max_age=settings.LANGUAGE_COOKIE_AGE,
                    path=settings.LANGUAGE_COOKIE_PATH,
                    domain=getattr(settings, 'LANGUAGE_COOKIE_DOMAIN', None),
                    secure=getattr(settings, 'LANGUAGE_COOKIE_SECURE', False),
                    httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
                    samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
                )
        
        return response

