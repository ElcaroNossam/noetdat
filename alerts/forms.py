from django import forms

from .models import AlertRule


class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ("metric", "operator", "threshold", "telegram_chat_id")


