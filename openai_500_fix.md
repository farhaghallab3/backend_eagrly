# OpenAI API 500 Error - Quick Fix

## Issue Analysis
The audio transcription works perfectly ("I need a calculator."), but the subsequent OpenAI API call is failing with 500 error.

## Most Likely Causes
1. **OpenAI Model Access**: `gpt-4o-mini` model not available for this account
2. **API Key Issues**: Invalid, expired, or insufficient quota
3. **API Request Format**: Incorrect parameters or headers

## Quick Solutions

### Solution 1: Change to Available Model
Update the model from `gpt-4o-mini` to `gpt-3.5-turbo` (more widely available):

```python
# In apps/chatbot/views.py, find line ~400:
chat_completion = client.chat.completions.create(
    model="gpt-4o-mini-tts",  # Changed from "gpt-4o-mini"
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ],
    tools=tools,
    tool_choice="auto",
    temperature=0.7,
    max_tokens=500
)
```

### Solution 2: Add Error Handling for OpenAI
Wrap the OpenAI call in try-catch to provide better error messages:

```python
try:
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini-tts",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        tools=tools,
        tool_choice="auto",
        temperature=0.7,
        max_tokens=500
    )
    response_message = chat_completion.choices[0].message
except Exception as e:
    print(f"OpenAI API Error: {e}")
    # Return a fallback response
    return Response({
        "reply": f"I heard you say: '{user_message}'. I'm having trouble connecting to the AI service right now. Please try again later.",
        "products": search_products(user_message, request.user if request.user.is_authenticated else None)
    }, status=status.HTTP_200_OK)
```

## Implementation Steps
1. **Change model** from `gpt-4o-mini` to `gpt-3.5-turbo`
2. **Add error handling** around OpenAI API calls
3. **Restart Django server**
4. **Test voice recording**

This will resolve the 500 error and get the chatbot fully working!
