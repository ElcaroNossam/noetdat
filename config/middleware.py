"""
Custom middleware for Content Security Policy header.
"""
from django.utils.deprecation import MiddlewareMixin


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

