from django.shortcuts import render, redirect
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
from .forms import CustomLoginForm, CustomUserCreationForm, EmailThread
from .tokens import account_activation_token

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
    email = EmailMultiAlternatives(mail_subject, message, to=[to_email])
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
  