# Chatbot Audio Message Fix Plan

## Problem Analysis
The frontend ChatbotWidget is getting a 400 Bad Request error when trying to send voice messages to the backend chatbot endpoint.

## Root Cause Analysis
Looking at the code, the issue is likely in one of these areas:
1. **Content-Type mismatch** - Frontend sends multipart/form-data but backend expects specific format
2. **FormData structure** - Audio file not properly formatted in FormData
3. **CSRF protection** - Missing CSRF token for authenticated requests
4. **Request validation** - Backend serializer rejecting the audio request
5. **File handling** - Backend not properly processing the audio file

## Steps to Debug and Fix

### Step 1: Test Backend Endpoint Directly
- [ ] Run the debug script to test the chatbot audio endpoint
- [ ] Check backend server logs for specific error messages
- [ ] Verify the endpoint is receiving and processing the request

### Step 2: Analyze Backend Error Response
- [ ] Check what specific validation is failing in the backend
- [ ] Review the ChatbotSerializer validation
- [ ] Examine the audio file processing logic

### Step 3: Fix Frontend Request
- [ ] Update the FormData structure to match backend expectations
- [ ] Add proper headers and CSRF handling if needed
- [ ] Ensure audio file is properly formatted

### Step 4: Test and Validate
- [ ] Test the fix with a real audio recording
- [ ] Verify the full flow: recording → upload → transcription → response
- [ ] Test edge cases (empty audio, large files, etc.)

## Expected Solutions

### Common Fixes:
1. **Add CSRF token** for authenticated requests
2. **Fix FormData structure** with proper field names
3. **Update request headers** to include Content-Type boundary
4. **Handle empty audio files** gracefully
5. **Add request size limits** and validation

### Testing Strategy:
1. Start with simple text-based request to verify endpoint works
2. Test with minimal audio file to isolate the audio processing issue
3. Test with actual recorded audio to verify full functionality
