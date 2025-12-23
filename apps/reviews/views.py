from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer
from apps.common.permissions import IsOwnerOrAdmin
from apps.products.models import Product
from apps.payments.models import Payment
from django.db.models import Q

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().select_related('product','reviewer','seller')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data.get('product')

        # Check purchase: because ERD lacks Order model, we'll treat a "purchase" as existence of a Payment
        # by the user and status 'active' AND optionally the product seller != user.
        # If you want a stricter purchase model, consider adding a Purchase/Order model.
        has_active_payment = Payment.objects.filter(user=user, status='active').exists()
        if not has_active_payment:
            # Deny creation - user hasn't purchased a package (required by business rule to post reviews)
            raise permissions.PermissionDenied('You can only review a product after purchasing a package (no active payments found).')

        # Save reviewer and seller
        serializer.save(reviewer=user, seller=product.seller)
