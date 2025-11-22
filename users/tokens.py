from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
  def _make_hash_value(self, user, timestamp):
    # Hash the user's ID, timestamp, and their active state.
    # If any of these change, the token becomes invalid.
    return (
      str(user.pk) + str(timestamp) +
      str(user.is_active)
    )

account_activation_token = AccountActivationTokenGenerator()