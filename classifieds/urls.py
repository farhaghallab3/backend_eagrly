from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
# from apps.users.views import CustomTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve as static_serve
from django.http import Http404
from django.shortcuts import redirect
import os
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Classifieds API",
        default_version='v1',
        description="API documentation for the Classifieds project",
        contact=openapi.Contact(email="your_email@example.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT
    # path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Moved to auth
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Apps
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.reviews.urls')),
    path('api/', include('apps.chats.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.reports.urls')),
    path("api/", include("apps.chatbot.urls")),
    path('api/', include('apps.wishlist.urls')),
    path('api/', include('apps.support.urls')),
    # Swagger
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),  # ✅
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

def _media_serve_case_insensitive(request, path):
    # Normalize path separators
    normalized = os.path.normpath(path).lstrip(os.sep)
    full_path = os.path.join(settings.MEDIA_ROOT, normalized)
    if os.path.exists(full_path):
        return static_serve(request, normalized, document_root=settings.MEDIA_ROOT)

    # Case-insensitive fallback: walk each segment
    parts = normalized.split(os.sep)
    search_root = settings.MEDIA_ROOT
    matched_parts = []
    for part in parts:
        try:
            entries = os.listdir(search_root)
        except FileNotFoundError:
            raise Http404
        match = None
        for e in entries:
            if e.lower() == part.lower():
                match = e
                break
        if not match:
            raise Http404
        matched_parts.append(match)
        search_root = os.path.join(search_root, match)

    found_rel = os.path.join(*matched_parts)
    return static_serve(request, found_rel, document_root=settings.MEDIA_ROOT)


# Serve static and media files in development (even if DEBUG is False)
if not getattr(settings, 'DJANGO_PRODUCTION', False):
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', _media_serve_case_insensitive),
    ]
elif settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', _media_serve_case_insensitive),
    ]


# When a file is not present locally but a GS bucket is configured, redirect to the
# public GCS URL so Cloud Run can serve media stored in Google Cloud Storage.
GS_BUCKET = os.environ.get('GS_BUCKET_NAME') or getattr(settings, 'GS_BUCKET_NAME', None)
if GS_BUCKET:
    def _media_redirect_fallback(request, path):
        normalized = os.path.normpath(path).lstrip(os.sep)
        gcs_url = f'https://storage.googleapis.com/{GS_BUCKET}/{normalized}'
        return redirect(gcs_url)

    # Add redirect as last-resort fallback
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', _media_redirect_fallback),
    ]
