from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Package, Payment
from .serializers import PackageSerializer, PaymentSerializer
from apps.common.permissions import IsAdminOrReadOnly
import os
import requests
import json

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
            status='PENDING', # Assuming 'PENDING' is a valid status choice
            payment_method='PAYMOB'
        )

        # 2. Call Paymob Intention API
        # Using the new Intention API with Secret Key
        url = "https://accept.paymob.com/v1/intention/"
        headers = {
            "Authorization": f"Token {secret_key}",
            "Content-Type": "application/json"
        }
        
        # Amount in cents (Paymob expects EGP as base currency usually, check project currency)
        # Assuming EGP for now as keys are 'egy_...'
        amount_cents = int(package.price * 100)
        
        payload = {
            "amount": amount_cents,
            "currency": "EGP", # Change if needed
            "payment_methods": [int(os.environ.get('PAYMOB_INTEGRATION_ID'))] if os.environ.get('PAYMOB_INTEGRATION_ID') else ["card", "wallet"], # requesting card and wallet
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
                "email": user.email,
                "phone_number": "NA", # Should be collected or user.phone if available
                "apartment": "NA", 
                "floor": "NA", 
                "street": "NA", 
                "building": "NA", 
                "shipping_method": "NA", 
                "postal_code": "NA", 
                "city": "NA", 
                "country": "EG", 
                "state": "NA"
            },
            "special_reference": str(payment.id),
            "redirection_url": "http://localhost:5173/payment-status" # Adjust for production
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code in [200, 201]:
                # Update payment with Paymob ID if available
                payment.transaction_id = response_data.get('id')
                payment.save()
                
                return Response({
                    "client_secret": response_data.get("client_secret"),
                    "details": response_data
                })
            else:
                print(f"DEBUG: Paymob Error: {response_data}")
                return Response({"error": "Paymob Error", "details": response_data}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

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
            
            verify_response = requests.get(
                f"https://accept.paymob.com/api/acceptance/transactions/{transaction_id}",
                headers=headers
            )
            
            if verify_response.status_code == 200:
                data = verify_response.json()
                is_actually_success = data.get('success', False)
                
                payment.transaction_id = transaction_id
                payment.response_data = json.dumps(data)
                
                if is_actually_success:
                    payment.status = 'COMPLETED'
                    payment.save()
                    
                    # Update User Package
                    user = payment.user
                    package = payment.package
                    from datetime import timedelta
                    from django.utils import timezone
                    
                    user.active_package = package
                    user.package_expiry = timezone.now() + timedelta(days=package.duration_in_days)
                    
                    # Add remaining ads logic if needed
                    user.free_ads_remaining = package.ad_limit if package.ad_limit < 999 else 9999
                    user.save()
                    
                    # Log success
                    print(f"DEBUG: Payment {payment.id} verified and user {user.id} upgraded.")
                    
                    # If this is a redirect from browser, return 302
                    # But since this is DRF, we can just return success or redirect
                    # Frontend expects us to redirect?
                    # views.py provided says redirection_url is localhost:5173/payment/status
                    # So Paymob redirects THERE, not HERE.
                    # Wait, if Paymob redirects to Frontend, Frontend executes `useEffect` to verify?
                    # NO, standard flow is: Paymob -> Frontend -> Backend Verify.
                    # This view should be called BY FRONTEND or Webhook.
                    
                    # Let's assume this is the 'Verify' endpoint called by Frontend
                    return Response({"status": "success", "package": package.name})
                else:
                    payment.status = 'FAILED'
                    payment.save()
                    return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
                    
            return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error in callback: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
