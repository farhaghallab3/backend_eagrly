from django.urls import path
from .views import ContactMessageCreateView, ContactMessageAdminView, ContactMessageDetailView

urlpatterns = [
    path('contact/', ContactMessageCreateView.as_view(), name='contact-create'),
    path('contact/admin/', ContactMessageAdminView.as_view(), name='contact-list-admin'),
    path('contact/admin/<int:pk>/', ContactMessageDetailView.as_view(), name='contact-detail-admin'),
]
