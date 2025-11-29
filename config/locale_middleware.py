"""
Custom locale middleware to ensure language is determined from URL and cookie,
not from Accept-Language header.
"""
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class CustomLocaleMiddleware(MiddlewareMixin):
    """
    Custom locale middleware that prioritizes URL prefix and cookie over Accept-Language header.
    This ensures that language selection is preserved and not overridden by browser settings.
    """
    
    def process_request(self, request):
        language = None
        
        # Priority 1: Check URL prefix (from i18n_patterns)
        language = translation.get_language_from_path(request.path_info)
        if language:
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()
            return None
        
        # Priority 2: Check cookie (set by set_language view)
        language = request.COOKIES.get(translation.LANGUAGE_COOKIE_NAME)
        if language and language in [lang[0] for lang in translation.get_language_info_list()]:
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()
            return None
        
        # Priority 3: Use default language from settings
        # Do NOT use Accept-Language header to avoid conflicts
        translation.activate(translation.get_language_from_request(request, check_path=False))
        request.LANGUAGE_CODE = translation.get_language()
        return None
    
    def process_response(self, request, response):
        language = translation.get_language()
        language_from_path = translation.get_language_from_path(request.path_info)
        
        # If language is set from URL, ensure it's activated
        if language_from_path and language_from_path != language:
            translation.activate(language_from_path)
            language = language_from_path
        
        # Set language cookie if not already set or if it differs
        if hasattr(request, 'LANGUAGE_CODE'):
            language = request.LANGUAGE_CODE
        
        if language and translation.check_for_language(language):
            if translation.LANGUAGE_COOKIE_NAME in request.COOKIES and \
               request.COOKIES[translation.LANGUAGE_COOKIE_NAME] != language:
                response.set_cookie(
                    translation.LANGUAGE_COOKIE_NAME,
                    language,
                    max_age=translation.LANGUAGE_COOKIE_AGE,
                    path=translation.LANGUAGE_COOKIE_PATH,
                    domain=translation.LANGUAGE_COOKIE_DOMAIN,
                    secure=translation.LANGUAGE_COOKIE_SECURE,
                    httponly=translation.LANGUAGE_COOKIE_HTTPONLY,
                    samesite=translation.LANGUAGE_COOKIE_SAMESITE,
                )
            elif translation.LANGUAGE_COOKIE_NAME not in request.COOKIES:
                response.set_cookie(
                    translation.LANGUAGE_COOKIE_NAME,
                    language,
                    max_age=translation.LANGUAGE_COOKIE_AGE,
                    path=translation.LANGUAGE_COOKIE_PATH,
                    domain=translation.LANGUAGE_COOKIE_DOMAIN,
                    secure=translation.LANGUAGE_COOKIE_SECURE,
                    httponly=translation.LANGUAGE_COOKIE_HTTPONLY,
                    samesite=translation.LANGUAGE_COOKIE_SAMESITE,
                )
        
        translation.deactivate()
        return response

