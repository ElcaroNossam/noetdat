from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/setlang/", set_language, name="set_language"),
]

urlpatterns += i18n_patterns(
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("api/", include(("api.urls", "api"), namespace="api")),
    path("alerts/", include(("alerts.urls", "alerts"), namespace="alerts")),
    path("", include(("screener.urls", "screener"), namespace="screener")),
    prefix_default_language=False,
)


