from django.urls import path

from .views import screener_list_api, symbol_detail_api, symbols_list_api

app_name = "api"

urlpatterns = [
    path("screener/", screener_list_api, name="screener_list"),
    path("symbol/<str:symbol>/", symbol_detail_api, name="symbol_detail"),
    path("symbols/", symbols_list_api, name="symbols_list"),
]


