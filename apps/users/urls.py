from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserLoginView, AdminLoginView, GoogleLoginView

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('token/', UserLoginView.as_view(), name='token_obtain_pair'),
    path('google_login/', GoogleLoginView.as_view(), name='google_login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('', include(router.urls))
]
