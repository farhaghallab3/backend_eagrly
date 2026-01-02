#!/usr/bin/env python3

import re

# Read the file
with open('apps/chatbot/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all instances of the problematic model name
fixed_content = content.replace('gpt-4o-mini-tts', 'gpt-4o-mini')

# Write the fixed content back
with open('apps/chatbot/views.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Fixed all instances of 'gpt-4o-mini-tts' to 'gpt-4o-mini' in apps/chatbot/views.py")
