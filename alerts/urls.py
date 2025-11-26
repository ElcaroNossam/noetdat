from django.urls import path

from .views import create_alert

app_name = "alerts"

urlpatterns = [
    path("create/<str:symbol>/", create_alert, name="create"),
]


