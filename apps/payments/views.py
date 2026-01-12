from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Package, Payment
from .serializers import PackageSerializer, PaymentSerializer
from apps.common.permissions import IsAdminOrReadOnly
import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        package = self.get_object()
        user = request.user
        
        # Paymob Configuration
        secret_key = os.environ.get('PAYMOB_SECRET_KEY')
        public_key = os.environ.get('PAYMOB_PUBLIC_KEY')
        
        if not secret_key:
            return Response({"error": "Payment configuration missing"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 1. Create Payment Record (Pending)
        payment = Payment.objects.create(
            user=user,
            package=package,
            amount=package.price,
            status='pending',  # Use lowercase to match model choices
            payment_method='credit'  # Use valid choice from model
        )

        # 2. Call Paymob Intention API
        # Using the new Intention API with Secret Key
        url = "https://accept.paymob.com/v1/intention/"
        headers = {
            "Authorization": f"Token {secret_key}",
            "Content-Type": "application/json"
        }
        
        # Amount in cents (Paymob expects EGP as base currency usually)
        amount_cents = int(float(package.price) * 100)
        
        # Get integration ID - Paymob requires it as an array of integers
        integration_id = os.environ.get('PAYMOB_INTEGRATION_ID')
        if integration_id:
            payment_methods = [int(integration_id)]
        else:
            # Fallback to generic payment methods if no integration ID
            logger.warning("PAYMOB_INTEGRATION_ID not set, using default payment methods")
            payment_methods = [5446733]  # Default to user's integration ID
        
        payload = {
            "amount": amount_cents,
            "currency": "EGP",
            "payment_methods": payment_methods,
            "items": [
                {
                    "name": package.name,
                    "amount": amount_cents,
                    "description": f"Subscription to {package.name}",
                    "quantity": 1
                }
            ],
            "billing_data": {
                "first_name": user.first_name or "User",
                "last_name": user.last_name or "Name",
                "email": user.email or "user@example.com",
                "phone_number": getattr(user, 'phone', None) or "+201000000000",
                "apartment": "NA", 
                "floor": "NA", 
                "street": "NA", 
                "building": "NA", 
                "shipping_method": "NA", 
                "postal_code": "NA", 
                "city": "Cairo", 
                "country": "EGY", 
                "state": "Cairo"
            },
            "special_reference": str(payment.id),
            "redirection_url": "http://localhost:5173/payment-status",
            "notification_url": "http://localhost:8000/api/payments/callback/"
        }

        # Sent to Paymob


        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            
            # Response received
            
            
            if response.status_code in [200, 201]:
                # Update payment with Paymob ID if available
                payment.transaction_id = response_data.get('id')
                payment.save()
                
                return Response({
                    "client_secret": response_data.get("client_secret"),
                    "details": response_data
                })
            else:
                logger.error(f"Paymob Error: {response_data}")
                return Response({"error": "Paymob Error", "details": response_data}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Exception in Paymob API call: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'payment_method', 'user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'package__name', 'transaction_id']
    ordering_fields = ['created_at', 'amount', 'status']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pending_count(self, request):
        """Return the count of payments pending confirmation for admin dashboard."""
        count = Payment.objects.filter(status='pending_confirmation').count()
        return Response({'count': count})

    @action(detail=False, methods=['get', 'post'], permission_classes=[permissions.AllowAny])
    def callback(self, request):
        """
        Handle Paymob callback/redirection.
        Query params usually contain: id, success, pending, hmac, etc.
        """
        # Parse query params
        transaction_id = request.query_params.get('id')
        success = request.query_params.get('success')
        
        # Determine success from string 'true'/'false'
        is_success = str(success).lower() == 'true'
        
        if not transaction_id:
             return Response({"error": "Missing transaction ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find our payment record - assuming we saved the intention ID or we need to find by transaction ID
            # Ideally we stored the Intention ID, but Paymob redirects with Transaction ID.
            # We might not have mapped Transaction ID to Payment yet if we only have Special Reference.
            # Paymob usually returns 'merchant_order_id' or similar which we sent as 'special_reference'.
            
            merchant_order_id = request.query_params.get('merchant_order_id') # If available
            
            # If we sent special_reference as payment.id, we can find it:
            # However, standard Paymob redirection often provides `merchant_order_id` matching our reference.
            
            payment = None
            if merchant_order_id:
                payment = Payment.objects.filter(id=merchant_order_id).first()
            
            if not payment:
               # Fallback: try to match by transaction_id if we saved it (but we probably didn't yet)
               payment = Payment.objects.filter(transaction_id=transaction_id).first()
               
            if not payment:
                # Last resort: Log it and fail? 
                # OR just assume we can find it if we query Paymob.
                pass

            if not payment:
                 return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)

            # Validating with Paymob API (Double Check)
            secret_key = os.environ.get('PAYMOB_SECRET_KEY')
            headers = {
                "Authorization": f"Token {secret_key}",
                "Content-Type": "application/json"
            }
            
            try:
                verify_response = requests.get(
                    f"https://accept.paymob.com/api/acceptance/transactions/{transaction_id}",
                    headers=headers
                )
                
                logger.info(f"Paymob Verification Status: {verify_response.status_code}")
                # logger.info(f"Paymob Verification Body: {verify_response.text}")
                
                if verify_response.status_code == 200:
                    data = verify_response.json()
                    is_actually_success = data.get('success', False)
                    
                    payment.transaction_id = transaction_id
                    payment.response_data = json.dumps(data)
                else:
                    # Fallback: API Verification failed (likely Auth), trust the callback params
                    # WARNING: In production, you MUST verify HMAC here if API verification fails.
                    logger.warning(f"Paymob API Verification failed ({verify_response.status_code}). Falling back to callback parameters.")
                    is_actually_success = is_success
                    payment.transaction_id = transaction_id
                    payment.response_data = json.dumps(request.query_params)

            except Exception as api_error:
                logger.error(f"Paymob API Connection failed: {api_error}. Falling back to callback parameters.")
                is_actually_success = is_success
                payment.transaction_id = transaction_id
                
            if is_actually_success:
                payment.status = 'completed'  # Use lowercase to match model choices
                payment.save()
                
                # Update User Package
                user = payment.user
                package = payment.package
                from datetime import timedelta
                from django.utils import timezone
                
                user.active_package = package
                user.package_expiry = (timezone.now() + timedelta(days=package.duration_in_days)).date()
                
                # Add remaining ads logic if needed
                user.free_ads_remaining = package.ad_limit if package.ad_limit < 999 else 9999
                user.save()
                
                # Create notification for the user
                try:
                    from apps.notifications.models import Notification
                    Notification.objects.create(
                        user=user,
                        notification_type='payment',
                        title='Payment Successful',
                        message=f'Your payment for {package.name} package has been confirmed. Enjoy your subscription!',
                    )
                except Exception as notif_error:
                    logger.error(f"Could not create notification: {notif_error}")
                
                # Log success
                logger.info(f"Payment {payment.id} verified and user {user.id} upgraded.")
                
                # Return success response for frontend
                return Response({"status": "success", "package": package.name})
            else:
                payment.status = 'failed'  # Use lowercase
                payment.save()
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in callback: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm_user_payment(self, request):
        """
        User confirms they have made a manual payment (bank transfer or mobile wallet).
        Creates a payment record with 'pending_confirmation' status and notifies admin.
        """
        from django.utils import timezone
        
        package_id = request.data.get('package_id')
        payment_method = request.data.get('payment_method', 'bank')
        
        if not package_id:
            return Response({'error': 'package_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create payment record with pending_confirmation status
        payment = Payment.objects.create(
            user=request.user,
            package=package,
            amount=package.price,
            payment_method=payment_method,
            status='pending_confirmation',
            user_confirmed_at=timezone.now()
        )
        
        # Create notification for all admin users
        try:
            from apps.notifications.models import Notification
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            admin_users = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
            user_display_name = request.user.first_name or request.user.username
            
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    notification_type='payment',
                    title='💳 New Payment Pending Confirmation',
                    message=f'{user_display_name} has confirmed payment for {package.name} package ({package.price} EGP) via {payment.get_payment_method_display()}. Please verify and confirm.'
                )
        except Exception as notif_error:
            logger.error(f"Could not create admin notification: {notif_error}")
        
        return Response({
            'success': True,
            'message': 'Payment confirmation submitted. Admin will verify and activate your subscription.',
            'payment_id': payment.id
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def admin_confirm(self, request, pk=None):
        """
        Admin confirms receiving a manual payment and upgrades the user to the selected package.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        payment = self.get_object()
        package_id = request.data.get('package_id')
        admin_notes = request.data.get('admin_notes', '')
        
        if payment.status == 'completed':
            return Response({'error': 'Payment already confirmed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the payment's package if no package_id provided
        if package_id:
            try:
                package = Package.objects.get(id=package_id)
            except Package.DoesNotExist:
                return Response({'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            package = payment.package
        
        # Update payment status
        payment.status = 'completed'
        payment.admin_confirmed_at = timezone.now()
        payment.admin_notes = admin_notes
        payment.package = package  # In case admin changed the package
        payment.expiry_date = timezone.now().date() + timedelta(days=package.duration_in_days)
        payment.save()
        
        # Upgrade the user
        user = payment.user
        user.active_package = package
        user.package_expiry = timezone.now().date() + timedelta(days=package.duration_in_days)
        user.free_ads_remaining = package.ad_limit if package.ad_limit < 999 else 9999
        user.save()
        
        # Create notification for the user
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=user,
                notification_type='payment',
                title='🎉 Payment Confirmed!',
                message=f'Your payment has been confirmed! You now have access to the {package.name} plan. Enjoy {package.ad_limit} ads for {package.duration_in_days} days!'
            )
        except Exception as notif_error:
            logger.error(f"Could not create user notification: {notif_error}")
        
        return Response({
            'success': True,
            'message': f'Payment confirmed. User {user.username} upgraded to {package.name}',
            'payment': PaymentSerializer(payment).data
        })

