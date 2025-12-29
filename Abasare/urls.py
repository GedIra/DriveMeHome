
from django.contrib import admin
from django.urls import path
from users.views import landing_view
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('rides/', include('rides.urls')),
    path('', landing_view, name='landing'),
    path('notifications/', include('notifications.urls')),
    path('', include('info.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
