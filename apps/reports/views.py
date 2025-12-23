from rest_framework import viewsets, permissions
from .models import Report
from .serializers import ReportSerializer
from apps.common.permissions import IsOwnerOrAdmin

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related('reporter','reported_user','product')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
