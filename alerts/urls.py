from django.urls import path

from .views import create_alert, alert_list, edit_alert, delete_alert, toggle_alert

app_name = "alerts"

urlpatterns = [
    path("", alert_list, name="list"),
    path("create/<str:symbol>/", create_alert, name="create"),
    path("edit/<int:alert_id>/", edit_alert, name="edit"),
    path("delete/<int:alert_id>/", delete_alert, name="delete"),
    path("toggle/<int:alert_id>/", toggle_alert, name="toggle"),
]


