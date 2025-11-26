from django.urls import path

from . import views

app_name = "screener"

urlpatterns = [
    path("", views.screener_list, name="list"),
    path("symbol/<str:symbol>/", views.symbol_detail, name="symbol_detail"),
]


