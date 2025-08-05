"""
URL configuration for hotelAi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include("staff.urls")),
    path('staff/', include('staff.urls')),
    path('laundry/', include('laundry.urls')),
    path('hmsAdmin/', include('hmsAdmin.urls')),
    path('users/', include('users.urls')),
     path('chat/', include(('chat.urls', 'chat'), namespace='chat')),
    path('cafe/', include('cafe.urls')),
    path('room-service/', include('room_service.urls')),
    path('concierge/', include('concierge.urls')),
    path('activity/', include('activity.urls')),
    path('housekeeping/', include('housekeeping.urls')),
    path('assessment/',include('assessment.urls')),
    path('guestbooking/', include('guestbooking.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
