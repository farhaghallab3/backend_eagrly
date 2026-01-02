#!/usr/bin/env python3

import re

# Read the file
with open('apps/chatbot/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the line where we raise the exception and replace it with mock response logic
pattern = r'if model is None:\s*raise Exception\([^)]*\)'
replacement = '''if model is None:
    # All OpenAI models failed, provide mock response for development
    print("All OpenAI models failed, providing mock response for development")
    mock_products = search_products(user_message, request.user if request.user.is_authenticated else None)
    return Response({
        "reply": f"I found {len(mock_products)} products matching '{user_message}'. (Note: This is a mock response as OpenAI API is not accessible)",
        "products": mock_products
    }, status=status.HTTP_200_OK)'''

# Replace the pattern
fixed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

# Write the fixed content back
with open('apps/chatbot/views.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Implemented graceful fallback to mock response when OpenAI API fails")
