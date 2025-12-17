from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Notification

@login_required
def get_notifications_api(request):
    """
    API to fetch unread notifications for the logged-in user.
    Used for polling in the navbar.
    """
    # Get unread notifications
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:10]
    
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'ride_id': n.ride.id if n.ride else None,
        'created_at': n.created_at.strftime("%H:%M") # e.g. 14:30
    } for n in notifications]
    
    return JsonResponse({
        'count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
        'notifications': data
    })

@login_required
@require_POST
def mark_read_api(request, notification_id):
    """
    API to mark a specific notification as read.
    """
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
@require_POST
def mark_all_read_api(request):
    """
    API to mark ALL notifications as read for the user.
    """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})