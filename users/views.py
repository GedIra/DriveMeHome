from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomLoginForm, CustomUserCreationForm
from django.http import JsonResponse
from django.contrib.auth import get_user_model


User = get_user_model()

def landing_view(request):
    return render(request, 'users/landing.html')

# --- EXISTING LOGIN VIEW ---
class UserLoginView(LoginView):
  template_name = 'users/authentication/login.html'
  authentication_form = CustomLoginForm
  redirect_authenticated_user = True
  
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = 'Log In - DriveMe Home'
    return context
  
# --- USRNAME EXISTENCE CHECK VIEW --- 

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
  success_url = reverse_lazy('login') # Or redirect to dashboard

  def form_valid(self, form):
    # Save the user
    user = form.save()
    # Automatically log them in
    login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(self.request, f"Account created successfully! Welcome, {user.username}.")
    return super().form_valid(form)

  def form_invalid(self, form):
    messages.error(self.request, "Registration failed. Please correct the errors below.")
    return super().form_invalid(form)