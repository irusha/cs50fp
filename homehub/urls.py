from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.say_hello),
    path('upload/', views.upload),
    path('labels/', views.labels),
    path('library/', views.get_all_videos),
    path('search/', views.search),
    path('recom/', views.recommendations),
    path('delete/', views.delete_videos),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
