from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, 
    UserCreationForm, 
    PasswordResetForm, 
    SetPasswordForm
)
from django.contrib.auth import get_user_model

User = get_user_model()

# --- EXISTING LOGIN FORM ---
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username, Email, or Phone",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-200 text-gray-900 transition duration-200 outline-none',
            'placeholder': 'e.g., john@example.com',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-200 text-gray-900 transition duration-200 outline-none',
            'placeholder': 'Enter your password'
        })
    )

# --- EXISTING REGISTRATION FORM ---
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none',
        'placeholder': 'john@example.com'
    }))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none',
        'placeholder': '+250 7...'
    }))
    is_driver = forms.BooleanField(
        required=False, 
        label="I want to sign up as a Driver",
        widget=forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'is_driver')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none',
            'placeholder': 'Choose a username'
        })

# --- NEW PASSWORD RESET FORMS ---
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none',
            'placeholder': 'Enter your registered email'
        })
    )

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Iterate over all fields (new_password1, new_password2) to apply styling
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none'
            })