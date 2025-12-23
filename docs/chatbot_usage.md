# Chatbot Feature Documentation

## Overview
The chatbot feature provides personalized tool recommendations based on a user's university and governorate. Users can view available tools and search for specific items.

## Prerequisites
- User must be authenticated
- User profile must have `university` and `governorate` fields filled

## API Endpoint
**POST** `/api/chatbot/`

### Headers
```
Authorization: Token <your-auth-token>
Content-Type: application/json
```

## Usage

### 1. Get All Available Tools/Recommendations
When a user opens the chatbot, they can request recommendations using keywords like:
- "show tools"
- "what tools are available"
- "recommend"
- "list products"
- "available tools"

**Request:**
```json
{
  "message": "show available tools"
}
```

**Response (with tools available):**
```json
{
  "reply": "Here are the available tools from Cairo University in Cairo:",
  "recommendations": [
    {
      "id": 1,
      "title": "Scientific Calculator",
      "description": "TI-84 Plus Calculator",
      "price": "500.00",
      "condition": "new",
      "university": "Cairo University",
      "faculty": "Engineering",
      "governorate": "Cairo",
      "category_name": "Electronics",
      "status": "active",
      "seller": {
        "id": 5,
        "email": "seller@example.com",
        "first_name": "John",
        "phone": "01234567890"
      }
    }
  ]
}
```

**Response (no tools available):**
```json
{
  "reply": "No tools are currently available from Cairo University in Cairo."
}
```

### 2. Search for Specific Tool by Name
Users can type a tool name directly to search for it:

**Request:**
```json
{
  "message": "calculator"
}
```

**Response (tool found):**
```json
{
  "reply": "Found 2 tool(s) matching 'calculator' from Cairo University in Cairo:",
  "results": [
    {
      "id": 1,
      "title": "Scientific Calculator",
      ...
    },
    {
      "id": 3,
      "title": "Graphing Calculator",
      ...
    }
  ]
}
```

**Response (tool not found):**
```json
{
  "reply": "Sorry, 'microscope' is not available from Cairo University in Cairo at the moment."
}
```

### 3. Profile Validation
If user hasn't set university or governorate:

**Response:**
```json
{
  "reply": "Please complete your profile with your university and governorate information to get personalized tool recommendations."
}
```

## How It Works

### Filter Logic
The chatbot filters products based on:
1. **University** - matches user's university (case-insensitive)
2. **Governorate** - matches user's governorate (case-insensitive)
3. **Status** - only shows `active` products
4. **Search term** - if user types a specific name, it searches using `title__icontains`

### Recommendation Keywords
The system recognizes these keywords as recommendation requests:
- recommend
- show
- available
- list
- tools
- products
- what

If the message contains any of these keywords, it shows all available tools. Otherwise, it treats the input as a search query.

## Database Schema

### User Model Fields (relevant)
- `university` - CharField(max_length=255)
- `governorate` - CharField(max_length=255) - **NEW**
- `faculty` - CharField(max_length=255)

### Product Model Fields (relevant)
- `title` - CharField(max_length=255)
- `university` - CharField(max_length=255)
- `governorate` - CharField(max_length=255) - **NEW**
- `faculty` - CharField(max_length=255)
- `status` - CharField (must be 'active')

## Example User Flow

1. **User opens chatbot on homepage**
2. **User types**: "show tools" or "what's available"
3. **System responds**: Shows all tools from their university + governorate
4. **User types**: "calculus book"
5. **System responds**: Shows only tools matching "calculus book" from their location
6. **User types**: "laptop"
7. **System responds**: "Sorry, 'laptop' is not available..." (if none found)

## Migration Notes

The `governorate` field was added via migrations:
- `apps/users/migrations/0003_user_governorate.py`
- `apps/products/migrations/0004_product_governorate.py`

Existing users and products will have blank governorate fields by default. They should be populated through:
- User registration/profile update
- Product creation/update forms
