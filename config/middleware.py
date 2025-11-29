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
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://s3.tradingview.com https://*.tradingview.com; "
            "style-src 'self' 'unsafe-inline' https://*.tradingview.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' https://*.tradingview.com https://*.binance.com; "
            "frame-src 'self' https://*.tradingview.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp_policy
        return response


class ForceLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to ensure language is determined from URL and cookie only,
    not from Accept-Language header. This prevents language from being
    overridden by browser settings.
    """
    
    def process_request(self, request):
        # Get language from URL path (highest priority)
        language = translation.get_language_from_path(request.path_info)
        if language:
            translation.activate(language)
            request.LANGUAGE_CODE = language
            return None
        
        # Get language from cookie (second priority)
        language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if language and language in [lang[0] for lang in settings.LANGUAGES]:
            translation.activate(language)
            request.LANGUAGE_CODE = language
            return None
        
        # Use default language from settings (do NOT use Accept-Language)
        translation.activate(settings.LANGUAGE_CODE)
        request.LANGUAGE_CODE = settings.LANGUAGE_CODE
        return None
    
    def process_response(self, request, response):
        # Ensure language cookie is set if language is determined from URL
        language = translation.get_language()
        language_from_path = translation.get_language_from_path(request.path_info)
        
        # If language is set from URL, ensure it's activated and cookie is set
        if language_from_path and language_from_path != language:
            translation.activate(language_from_path)
            language = language_from_path
        
        # Set or update language cookie
        if hasattr(request, 'LANGUAGE_CODE'):
            language = request.LANGUAGE_CODE
        
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
        
        translation.deactivate()
        return response

