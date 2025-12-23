# Frontend Integration Guide for Chatbot

## Overview
This guide explains how to integrate the updated chatbot frontend with the backend API.

## Key Changes in Updated Frontend

### 1. Initial Load Updated
The frontend now calls the chatbot API with `initial: true` on first open, skipping any keyword triggers.

### 2. Response Handling
The frontend now handles both response fields:
- `response.recommendations` - for recommendation mode
- `response.results` - for search mode

### 3. Product Display Fields
Updated to match the actual backend response structure:
- `product.seller.first_name` instead of `product.seller.name`
- `product.seller.email` - email address
- `product.category_name` - category display name
- `product.price` - displayed as EGP (Egyptian Pounds)
- **Governorate field removed** - only shows University and Faculty

### 4. Show More/Less Functionality
Fixed to use object-based state management per message index:
```javascript
const [showAll, setShowAll] = useState({});
```

### 5. Error Handling
Enhanced error handling to display backend error messages:
```javascript
const errorMessage = err.response?.data?.reply || 
                     err.response?.data?.error || 
                     "An error occurred...";
```

## Backend API Response Formats

### Recommendation Mode Response
When user types: "show tools", "recommend", "list products", etc.

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
      "image": "/media/products/calculator.jpg",
      "images": "",
      "category": 2,
      "category_name": "Electronics",
      "university": "Cairo University",
      "faculty": "Engineering",
      "governorate": "Cairo",
      "is_featured": false,
      "status": "active",
      "created_at": "2025-12-13T17:00:00Z",
      "updated_at": "2025-12-13T17:00:00Z",
      "seller": {
        "id": 5,
        "email": "seller@example.com",
        "first_name": "Ahmed",
        "phone": "01234567890"
      }
    }
  ]
}
```

### Search Mode Response
When user types a specific tool name: "calculator", "ruler", etc.

```json
{
  "reply": "Found 2 tool(s) matching 'calculator' from Cairo University in Cairo:",
  "results": [
    {
      "id": 1,
      "title": "Scientific Calculator",
      // ... same structure as above
    },
    {
      "id": 3,
      "title": "Graphing Calculator",
      // ... same structure as above
    }
  ]
}
```

### Not Found Response
```json
{
  "reply": "Sorry, 'microscope' is not available from Cairo University in Cairo at the moment."
}
```

### Profile Incomplete Response
```json
{
  "reply": "Please complete your profile with your university and governorate information to get personalized tool recommendations."
}
```

## Frontend Component Changes Summary

### File: `ChatbotWidget.jsx`

#### 1. State Management
```javascript
// Changed from single boolean to object for managing multiple messages
const [showAll, setShowAll] = useState({});

// New toggle function
const toggleShowAll = (messageIndex) => {
  setShowAll(prev => ({
    ...prev,
    [messageIndex]: !prev[messageIndex]
  }));
};
```

#### 2. Initial Fetch
```javascript
const fetchRecommendations = async () => {
  setLoading(true);
  try {
    const response = await sendMessageToBot("", true); // Send empty message with initial=true
    const botMsg = {
      role: "bot",
      content: response.reply || "",
      products: response.products || []
    };
    setMessages([botMsg]);
  } catch (err) {
    // Enhanced error handling
    const errorMessage = err.response?.data?.reply ||
                        err.response?.data?.error ||
                        "An error occurred while fetching recommendations.";
    setMessages([{ role: "bot", content: errorMessage }]);
  } finally {
    setLoading(false);
  }
};
```

#### 3. Send Message
```javascript
const sendMessage = async () => {
  if (!input.trim()) return;

  const userMsg = { role: "user", content: input };
  setMessages(prev => [...prev, userMsg]);
  setInput("");
  setLoading(true);

  try {
    const response = await sendMessageToBot(input);
    const botMsg = {
      role: "bot",
      content: response.reply || "Here are the results:",
      products: response.recommendations || response.results || []
    };
    setMessages(prev => [...prev, botMsg]);
  } catch (err) {
    const errorMessage = err.response?.data?.reply || 
                        err.response?.data?.error || 
                        "An error occurred while contacting the server.";
    setMessages(prev => [...prev, { role: "bot", content: errorMessage }]);
  } finally {
    setLoading(false);
  }
};
```

#### 4. Render Bot Message
```javascript
const renderBotMessage = (msg, messageIndex) => {
  if (!msg.products || msg.products.length === 0) {
    return <span>{msg.content}</span>;
  }

  const isExpanded = showAll[messageIndex] || false;
  const displayedProducts = isExpanded ? msg.products : msg.products.slice(0, 3);

  return (
    <div>
      <div style={{ marginBottom: '10px' }}>{msg.content}</div>

      {displayedProducts.map(product => (
        <div key={product.id} className={styles.productPreview}>
          <div 
            className={styles.productTitle} 
            style={{ cursor: 'pointer', color: '#007bff', textDecoration: 'underline' }}
            onClick={() => navigate(`/product/${product.id}`)}
          >
            {product.title}
          </div>
        <div className={styles.productMeta}>
              {product.seller?.first_name && `Seller: ${product.seller.first_name}`}
              {product.seller?.email && ` (${product.seller.email})`}
              {product.university && ` | University: ${product.university}`}
              {product.faculty && ` | Faculty: ${product.faculty}`}
              {product.price && ` | Price: EGP ${product.price}`}
              {product.condition && ` | Condition: ${product.condition}`}
              {product.category_name && ` | Category: ${product.category_name}`}
            </div>
        </div>
      ))}

      {msg.products.length > 3 && (
        <button
          className={styles.seeMoreBtn}
          onClick={() => toggleShowAll(messageIndex)}
        >
          {isExpanded ? "Show Less" : `See ${msg.products.length - 3} more`}
        </button>
      )}
    </div>
  );
};
```

## Testing Checklist

### Frontend Testing
- [ ] Open chatbot on homepage
- [ ] Verify initial recommendations load automatically
- [ ] Type "show tools" - verify all tools display
- [ ] Type specific tool name - verify search results
- [ ] Type non-existent tool - verify "not available" message
- [ ] Test with user who has no governorate - verify profile prompt
- [ ] Click on product title - verify navigation to product page
- [ ] Test "See more" button with >3 products
- [ ] Test error handling with network failure

### Backend Testing (Already Complete)
- [x] Database migrations applied
- [x] Governorate field in User model
- [x] Governorate field in Product model
- [x] API filters by university and faculty only
- [x] Recommendation keywords recognized
- [x] Search functionality working
- [x] Profile validation working

## Important Notes

1. **Authentication Required**: The chatbot API requires user authentication. Ensure the frontend sends the authentication token with requests.

2. **Governorate Field**: Users must have their governorate field populated. Consider:
   - Adding governorate to registration form
   - Adding validation on profile update
   - Showing a profile completion prompt if governorate is missing

3. **Product Creation**: When sellers create products, ensure they can specify governorate along with university and faculty.

4. **Currency**: Changed from "$" to "EGP" for Egyptian Pounds in the frontend display.

5. **Seller Information**: Backend returns seller as an object with `first_name`, `email`, and `phone`. The frontend now uses `first_name` instead of `name`.

## Installation Steps

1. Replace your existing `ChatbotWidget.jsx` with the updated version from `docs/frontend_chatbot_update.jsx`

2. Ensure your chat service is configured correctly:
```javascript
// chatService.js
export const sendMessageToBot = async (message, initial = false) => {
  const requestData = { message };
  if (initial) {
    requestData.initial = true;
  }

  const response = await axios.post('/api/chatbot/',
    requestData,
    {
      headers: {
        'Authorization': `Token ${yourAuthToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.data;
};
```

3. Test the integration with authenticated users

4. Update user registration/profile forms to include governorate field

## Troubleshooting

### Issue: "401 Unauthorized"
**Solution**: Ensure authentication token is included in API requests

### Issue: "Profile incomplete" message
**Solution**: User needs to set university and governorate in their profile

### Issue: No products showing
**Solution**: 
- Verify products exist with matching university and governorate
- Check product status is 'active'
- Ensure seller has set governorate on products

### Issue: Product fields missing in display
**Solution**: Check backend ProductSerializer includes all fields (it should with `fields = '__all__'`)
