from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser
from .models import ContactMessage
from .serializers import ContactMessageSerializer

class ContactMessageCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

class ContactMessageAdminView(generics.ListAPIView):
    """
    Admin-only view to list all contact messages.
    Supports filtering by resolved status via query param ?is_resolved=true/false
    """
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = ContactMessage.objects.all().order_by('-created_at')
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        return queryset

class ContactMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view to retrieve, update (resolve), or delete a specific message.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]
