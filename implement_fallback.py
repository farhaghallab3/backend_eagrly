#!/usr/bin/env python3

import re

# Read the file
with open('apps/chatbot/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the model specification line and replace it with fallback logic
pattern = r'(\s+)# Always enable tools for this assistant\n(\s+)chat_completion = client\.chat\.completions\.create\(\n(\s+)model="[^"]*",'
replacement = r'''\1# Always enable tools for this assistant with fallback model selection
\1models_to_try = ['gpt-3.5-turbo-0125', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k']
\1model = None
\1for model_name in models_to_try:
\1    try:
\1        chat_completion = client.chat.completions.create(
\1            model=model_name,
\1            messages=[
\1                {"role": "system", "content": system_prompt},
\1                {"role": "user", "content": user_message}
\1            ],
\1            tools=tools,
\1            tool_choice="auto",
\1            temperature=0.7,
\1            max_tokens=500
\1        )
\1        model = model_name
\1        print(f"Successfully using model: {model_name}")
\1        break
\1    except Exception as e:
\1        print(f"Failed with model {model_name}: {e}")
\1        continue
\1
\1if model is None:
\1    raise Exception('All OpenAI models failed to work. Please check API key permissions.')

\1# Continue with the successful model
\1chat_completion = client.chat.completions.create(
\1    model=model,'''

# Replace the pattern
fixed_content = re.sub(pattern, replacement, content)

# Also need to update the subsequent model calls to use the same fallback logic
# Look for the two other chat.completions.create calls
pattern2 = r'(\s+)chat_completion = client\.chat\.completions\.create\(\n(\s+)model="[^"]*",'
replacement2 = r'''\1chat_completion = client.chat.completions.create(
\1    model=model,'''

# Apply the second replacement to all occurrences
fixed_content = re.sub(pattern2, replacement2, fixed_content)

# Write the fixed content back
with open('apps/chatbot/views.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Implemented robust fallback model selection in chatbot views")
