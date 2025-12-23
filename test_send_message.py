
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.chats.models import Chat, Message
from apps.products.models import Product, Category

User = get_user_model()

@pytest.mark.django_db
def test_send_message():
    # Create users
    seller = User.objects.create_user(username='seller', password='password', email='seller@example.com')
    buyer = User.objects.create_user(username='buyer', password='password', email='buyer@example.com')

    # Create a category
    category = Category.objects.create(name='Electronics', description='Electronics category')

    # Create a product
    product = Product.objects.create(
        name='Test Product',
        description='Test description',
        price=100,
        category=category,
        seller=seller,
        location='Some Location',
        payment_options='Cash'
    )

    # Create a chat
    chat = Chat.objects.create(product=product, seller=seller, buyer=buyer)

    # Authenticate as buyer
    client = APIClient()
    client.force_authenticate(user=buyer)

    # Send a message
    response = client.post('/api/messages/', {'chat': chat.id, 'text': 'Hello, seller!'})

    # Check response status
    assert response.status_code == 201

    # Check if the message was created
    assert Message.objects.count() == 1
    message = Message.objects.first()
    assert message.chat == chat
    assert message.sender == buyer
    assert message.text == 'Hello, seller!'
    
    # Send a message with 'content' instead of 'text'
    response = client.post('/api/messages/', {'chat': chat.id, 'content': 'This should fail'})

    # Check response status
    assert response.status_code == 400
