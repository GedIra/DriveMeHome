from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailPhoneUsernameBackend(ModelBackend):
  # Allows users to log in using their Username, Email, or Phone Number.
  def authenticate(self, request, username=None, password=None, **kwargs):
    if username is None:
      return None
    try:
      # Check if the input matches username, email, OR phone_number
      user = User.objects.get(
        Q(username=username) | 
        Q(email=username) | 
        Q(phone_number=username)
      )
    except User.DoesNotExist:
      return None
    # Verify the password and ensure the user is active
    if user.check_password(password) and self.user_can_authenticate(user):
      return user
    return None