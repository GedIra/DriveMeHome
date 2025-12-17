from .models import Notification

def send_notification(recipient, title, message, type=Notification.NotificationType.SYSTEM, ride=None, sender=None):
    """
    Utility to create a notification.
    """
    try:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            ride=ride,
            title=title,
            message=message,
            notification_type=type
        )
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False