
from django.contrib import admin
from django.urls import path
from users.views import landing_view
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('rides/', include('rides.urls')),
    path('', landing_view),
    path('notifications/', include('notifications.urls')),
]
