"""
Custom views for language switching and other utilities.
"""
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect


@csrf_protect
@require_POST
def set_language_custom(request):
    """
    Custom language switching view that properly handles prefix_default_language=False.
    """
    next_url = request.POST.get('next', '/')
    language = request.POST.get('language')
    
    if language and language in [lang[0] for lang in settings.LANGUAGES]:
        # Activate the language
        translation.activate(language)
        
        # Translate the next URL to include language prefix if needed
        # For default language (ru), don't add prefix
        if language == settings.LANGUAGE_CODE:
            # Default language - remove prefix if present
            translated_url = next_url
            # Remove any language prefix
            for lang_code, _ in settings.LANGUAGES:
                if next_url.startswith(f'/{lang_code}/'):
                    translated_url = '/' + next_url[len(f'/{lang_code}/'):]
                    break
                elif next_url == f'/{lang_code}/' or next_url == f'/{lang_code}':
                    translated_url = '/'
                    break
        else:
            # Non-default language - add prefix if not present
            # Check if URL already has a language prefix
            has_prefix = False
            for lang_code, _ in settings.LANGUAGES:
                if next_url.startswith(f'/{lang_code}/') or next_url == f'/{lang_code}':
                    has_prefix = True
                    # Replace existing prefix with new one
                    if next_url.startswith(f'/{lang_code}/'):
                        translated_url = f'/{language}/' + next_url[len(f'/{lang_code}/'):]
                    else:
                        translated_url = f'/{language}/'
                    break
            
            if not has_prefix:
                # No prefix - add one
                path = next_url.lstrip('/')
                if path:
                    translated_url = f'/{language}/{path}'
                else:
                    translated_url = f'/{language}/'
        
        # Set language cookie
        response = HttpResponseRedirect(translated_url)
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
    
    # If language is invalid, redirect to next URL without changing language
    return HttpResponseRedirect(next_url)

