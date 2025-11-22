from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomLoginForm, CustomUserCreationForm

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