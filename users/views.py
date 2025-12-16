from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from .forms import CustomLoginForm, CustomUserCreationForm
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from .tokens import account_activation_token
from django.conf import settings
from .forms import (
    CustomLoginForm, 
    CustomUserCreationForm, 
    EmailThread, 
    DriverProfileForm, 
    CustomerProfileForm,
    DriverApplicationForm
)
from .tokens import account_activation_token
from .models import DriverProfile, CustomerProfile
from django.contrib.auth.decorators import login_required

User = get_user_model()

def landing_view(request):
    return render(request, 'users/landingPage.html')

# --- LOGIN VIEW ---
class UserLoginView(LoginView):
  template_name = 'users/authentication/login.html'
  authentication_form = CustomLoginForm
  redirect_authenticated_user = True
  
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = 'Log In - DriveMe Home'
    return context
  
# --- USERNAME EMAIL PHONENUMBER EXISTENCE CHECK VIEWS --- 
def check_username_existence(request):
  username = request.GET.get('username', None)
  exists = User.objects.filter(username=username).exists()
  if exists:
    return JsonResponse({'exists': True, 'message': 'Username is already taken.'})
  else:
    return JsonResponse({'exists': False, 'message': 'Username is available.'})


def check_email_existence(request):
  email = request.GET.get('email', None)
  exists = False
  if email:
    exists = User.objects.filter(email__iexact=email).exists()
  if exists:
    return JsonResponse({'exists': True, 'message': 'Email is already registered.'})
  else:
    return JsonResponse({'exists': False, 'message': 'Email is available.'})


def check_phone_existence(request):
  phone = request.GET.get('phone', None)
  exists = False
  if phone:
    exists = User.objects.filter(phone_number=phone).exists()
  if exists:
    return JsonResponse({'exists': True, 'message': 'Phone number is already registered.'})
  else:
    return JsonResponse({'exists': False, 'message': 'Phone number is available.'})
  
# --- NEW REGISTER VIEW ---
class RegisterView(CreateView):
  form_class = CustomUserCreationForm
  template_name = 'users/authentication/register.html'
  success_url = reverse_lazy('login')

  def form_valid(self, form):
    # 1. Create the user object but DO NOT save to DB yet
    user = form.save(commit=False)
    # 2. Deactivate the account until verified
    user.is_active = False 
    user.save()

    # 3. Setup Email Data
    current_site = get_current_site(self.request)
    mail_subject = 'Activate your DriveMe Home account'
    
    # 4. Render the HTML Email
    message = render_to_string('users/authentication/emails/activation_email.html', {
      'user': user,
      'domain': current_site.domain,
      'uid': urlsafe_base64_encode(force_bytes(user.pk)),
      'token': account_activation_token.make_token(user),
      'protocol': 'https' if self.request.is_secure() else 'http',
    })
      
    # 5. Send Email (using the Thread class we defined in forms.py)
    to_email = form.cleaned_data.get('email')
    email = EmailMultiAlternatives(
      mail_subject,
      message,
      settings.DEFAULT_FROM_EMAIL,   # explicitly set from_email
      [to_email]
    )
    email.attach_alternative(message, "text/html")
    EmailThread(email).start()

    # 6. Redirect to the "Check your email" page
    return redirect('activation_sent')

  def form_invalid(self, form):
    messages.error(self.request, "Registration failed. Please correct the errors below.")
    return super().form_invalid(form)
  
# --- NEW ACTIVATION VIEW ---
class ActivateAccountView(View):
  def get(self, request, uidb64, token):
    try:
      uid = force_str(urlsafe_base64_decode(uidb64))
      user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
      user = None

    if user is not None and account_activation_token.check_token(user, token):
      # Token is valid!
      user.is_active = True
      user.save()
      messages.success(request, 'Your account has been activated successfully! You can now log in.')
      return redirect('login')
    else:
      # Token invalid or expired
      messages.error(request, 'Activation link is invalid or has expired!')
      return redirect('login')

# --- EMAIL SENT PAGE  VIEW---
def activation_sent_view(request):
  return render(request, 'users/authentication/activation_sent.html')

@login_required
def profile_view(request):
    """
    Unified profile view that determines if the user is a Driver or Customer
    and renders the appropriate form to update their profile.
    """
    user = request.user
    
    # Initialize vars
    form = None
    template_name = 'users/profile_form.html'
    profile_type = 'User'

    if user.is_driver:
        profile_type = 'Driver'
        # Get or create ensures we don't crash if signal failed (safety net)
        profile, created = DriverProfile.objects.get_or_create(user=user)
        
        if request.method == 'POST':
            form = DriverProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Driver profile updated successfully!')
                return redirect('profile')
        else:
            form = DriverProfileForm(instance=profile)

    elif user.is_customer:
        profile_type = 'Customer'
        profile, created = CustomerProfile.objects.get_or_create(user=user)
        
        if request.method == 'POST':
            form = CustomerProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
        else:
            form = CustomerProfileForm(instance=profile)
    
    else:
        # Fallback for admins or weird states
        messages.info(request, "You are viewing a generic account.")

    context = {
        'form': form,
        'profile_type': profile_type,
        'page_title': f'Edit {profile_type} Profile'
    }
    return render(request, template_name, context)

# --- DRIVER APPLICATION VIEW ---
@login_required
def driver_application_view(request):
    user = request.user
    
    if not user.is_driver:
        messages.error(request, "Only drivers can access the verification application.")
        return redirect('profile')

    profile, created = DriverProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = DriverApplicationForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application submitted successfully! Your documents are under review.')
            return redirect('profile') # Or redirect to a 'status' page
    else:
        form = DriverApplicationForm(instance=profile)

    context = {
        'form': form,
        'page_title': 'Driver Verification Application'
    }
    return render(request, 'users/driver_application.html', context)

# ... (Existing simple views like activation_sent_view if present) ...
def activation_sent_view(request):
    return render(request, 'users/activation_sent.html')