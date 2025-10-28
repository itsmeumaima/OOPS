from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ColorDetection

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match!")
        return cleaned_data

class ColorDetectorForm(forms.ModelForm):
    class Meta:
        model = ColorDetection
        fields = ['image']

class CorrectorForm(forms.Form):
    image = forms.ImageField(required=True)
    CORRECTION_CHOICES = [
        ('type1', 'Correction Type 1'),
        ('type2', 'Correction Type 2'),
        ('type3', 'Correction Type 3'),
    ]
    correction_type = forms.ChoiceField(choices=CORRECTION_CHOICES, widget=forms.RadioSelect, initial='type1')
    hue = forms.IntegerField(min_value=-360, max_value=360, initial=0, widget=forms.NumberInput(attrs={'type': 'range', 'min': '-180', 'max': '180'}))
