from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Report
from .serializers import ReportSerializer
from apps.common.permissions import IsOwnerOrAdmin


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related('reporter', 'reported_user', 'product')
    serializer_class = ReportSerializer

    def get_permissions(self):
        """Allow authenticated users to create reports, but restrict other actions."""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_create(self, serializer):
        """Automatically set the reporter to the current user."""
        serializer.save(reporter=self.request.user)

