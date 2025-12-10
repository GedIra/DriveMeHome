from django.urls import path
from django.contrib.auth.views import (
    LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from .views import (
    UserLoginView,
    RegisterView,
    ActivateAccountView,
    check_username_existence, 
    check_email_existence,
    check_phone_existence,
    landing_view,
    activation_sent_view,
)
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

urlpatterns = [
    # Authentication
    path('', landing_view, name='landing'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('ajax/check-username/', check_username_existence, name='check_username_existence'),
    path('ajax/check-email/', check_email_existence, name='check_email_existence'),
    path('ajax/check-phone/', check_phone_existence, name='check_phone_existence'),

    # Activation Flows
    path('activation-sent/', activation_sent_view, name='activation_sent'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),

    # Password Reset Flows
    path('password-reset/', 
         PasswordResetView.as_view(
             template_name='users/authentication/password_reset.html',
             form_class=CustomPasswordResetForm,
             # Add this line to use the new HTML email
             html_email_template_name='users/authentication/emails/password_reset_email.html'
         ), 
         name='password_reset'),
         
    path('password-reset/done/', 
         PasswordResetDoneView.as_view(template_name='users/authentication/password_reset_done.html'), 
         name='password_reset_done'),
         
    path('password-reset-confirm/<uidb64>/<token>/', 
         PasswordResetConfirmView.as_view(
             template_name='users/authentication/password_reset_confirm.html',
             form_class=CustomSetPasswordForm
         ), 
         name='password_reset_confirm'),
         
    path('password-reset-complete/', 
         PasswordResetCompleteView.as_view(template_name='users/authentication/password_reset_complete.html'), 
         name='password_reset_complete'),
]
