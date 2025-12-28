from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer, ChatReadSerializer
from apps.common.permissions import IsOwnerOrAdmin

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all().select_related('product', 'buyer', 'seller')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ChatReadSerializer
        return ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(Q(buyer=user) | Q(seller=user))

    def retrieve(self, request, *args, **kwargs):
        """When retrieving a chat, mark all messages as read for the current user."""
        instance = self.get_object()
        user = request.user
        # Mark all unread messages NOT sent by current user as read
        instance.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark all messages in this chat as read for the current user."""
        chat = self.get_object()
        user = request.user
        # Mark all unread messages NOT sent by current user as read
        updated = chat.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        return Response({'marked_read': updated})

    @action(detail=False, methods=['post'], url_path='find-or-create')
    def find_or_create_chat(self, request):
        print(f"DEBUG: find_or_create_chat data: {request.data}")
        product_id = request.data.get('product')
        seller_id = request.data.get('seller')
        buyer_id = request.data.get('buyer')

        if not product_id:
             return Response({"error": "Product ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not seller_id:
             return Response({"error": "Seller ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not buyer_id:
             return Response({"error": "Buyer ID is missing. Are you logged in?"}, status=status.HTTP_400_BAD_REQUEST)

        chat = Chat.objects.filter(
            product_id=product_id,
            seller_id=seller_id,
            buyer_id=buyer_id
        ).first()

        if chat:
            serializer = ChatReadSerializer(chat, context={'request': request})
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            chat = serializer.save()
            read_serializer = ChatReadSerializer(chat, context={'request': request})
            headers = self.get_success_headers(read_serializer.data)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().select_related('chat', 'sender')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

