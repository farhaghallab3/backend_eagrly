# Fix for Chatbot User Service Authorization

## Problem
The chatbot widget gets a 401 Unauthorized error when trying to fetch user data via `GET /api/users/{id}/` from `userService.js`. The error occurs because the frontend userService.js is not sending the authorization token in the request headers.

## Root Cause
Looking at `chatService.js`, it properly sends the authorization token:
```javascript
const config = {
  headers: { Authorization: `Token ${token}` },
};
```

However, `userService.js` is not including this authorization header in its requests.

## Solutions

### Preferred: Backend Solution (Already Implemented)
A new `/api/users/me/` endpoint has been added to the UserViewSet that allows authenticated users to access their own profile data without object-level permission checks. This is simpler and more secure.

**Use this endpoint instead:**
```javascript
export const getCurrentUser = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("User not authenticated");
    }

    const config = {
      headers: { Authorization: `Token ${token}` },
    };

    const res = await axios.get("http://127.0.0.1:8000/api/users/me/", config);
    return res.data;
  } catch (err) {
    console.error("Error fetching user data:", err);

    if (err.response?.status === 401) {
      throw new Error("Authentication required");
    }

    throw new Error("Failed to fetch user data");
  }
};
```

### Alternative: Frontend Solution
If you prefer to keep using the existing `/api/users/{id}/` endpoint, update `userService.js` to include the authorization token:

```javascript
export const getUserById = async (userId) => {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("User not authenticated");
    }

    const config = {
      headers: { Authorization: `Token ${token}` },
    };

    const res = await axios.get(`http://127.0.0.1:8000/api/users/${userId}/`, config);
    return res.data;
  } catch (err) {
    console.error("Error fetching user data:", err);

    if (err.response?.status === 401) {
      throw new Error("Authentication required");
    }

    throw new Error("Failed to fetch user data");
  }
};
```

## Backend Status
The backend Django API now includes:
- **New endpoint**: `/api/users/me/` - allows authenticated users to get their own profile
- **Existing endpoint**: `/api/users/{id}/` - requires authentication + ownership verification
- JWT token authentication is properly configured
- Proper security measures remain in place

Use the `/api/users/me/` endpoint for chatbot functionality as it's cleaner and avoids potential permission issues.
