from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("api/", include(("api.urls", "api"), namespace="api")),
    path("alerts/", include(("alerts.urls", "alerts"), namespace="alerts")),
    path("", include(("screener.urls", "screener"), namespace="screener")),
]


