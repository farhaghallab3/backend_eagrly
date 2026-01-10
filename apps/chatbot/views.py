from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .serializers import ChatbotSerializer
from openai import OpenAI
import os
import json
import traceback
import logging
from apps.products.models import Product, Category

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)


def parse_location_from_query(query):
    """Parse location keywords from search query"""
    query_lower = query.lower()

    # Common location keywords and their mappings
    location_keywords = {
        'giza': 'giza',
        'cairo': 'cairo',
        'alexandria': 'alexandria',
        'alex': 'alexandria',
        'aswan': 'aswan',
        'asyut': 'asyut',
        'beheira': 'beheira',
        'beni suef': 'beni suef',
        'dakahlia': 'dakahlia',
        'damietta': 'damietta',
        'faiyum': 'faiyum',
        'gharbia': 'gharbia',
        'ismailia': 'ismailia',
        'kafr el-sheikh': 'kafr el-sheikh',
        'luxor': 'luxor',
        'matruh': 'matruh',
        'minya': 'minya',
        'monufia': 'monufia',
        'new valley': 'new valley',
        'north sinai': 'north sinai',
        'port said': 'port said',
        'qalyubia': 'qalyubia',
        'qena': 'qena',
        'red sea': 'red sea',
        'sharqia': 'sharqia',
        'sohag': 'sohag',
        'south sinai': 'south sinai',
        'suez': 'suez'
    }

    # Check for location patterns: "from X", "in X", "X ruler", etc.
    patterns = [
        r'from (\w+(?:\s+\w+)*)',
        r'in (\w+(?:\s+\w+)*)',
        r'at (\w+(?:\s+\w+)*)'
    ]

    import re
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            location_candidate = match.group(1).strip()
            # Check if it's a known location
            for keyword, location in location_keywords.items():
                if keyword in location_candidate or location_candidate in keyword:
                    return location

    # Direct location mentions
    for keyword, location in location_keywords.items():
        if keyword in query_lower:
            return location

    return None


def search_products(query, user=None):
    """
    Search for products in the database with hierarchical filtering:
    1. Specified location (if mentioned in query)
    2. Same university + same faculty (highest priority)
    3. Same university + different faculty (medium priority)
    4. Transfer not available (fallback - no filtering)
    Returns only top 3 cheapest results from each level
    Uses flexible search with common substrings for better matching
    """
    # Clean and prepare search query
    query = query.lower().strip()

    # Parse location from query
    specified_location = parse_location_from_query(query)
    logger.debug(f"Parsed location from query: '{specified_location}'")

    # Remove location words from search query for better product matching
    location_words = ['from', 'in', 'at', 'cairo', 'giza', 'alexandria', 'alex']
    search_query = query
    for word in location_words:
        search_query = search_query.replace(word, '').strip()

    # Create search variations for better matching
    search_terms = [search_query]
    # Add common shortened versions
    if 'calculator' in search_query:
        search_terms.extend(['calc', 'calculat'])
    if 'computer' in search_query:
        search_terms.extend(['comp', 'comput'])
    if 'notebook' in search_query:
        search_terms.extend(['note', 'book'])
    if 'pencil' in search_query:
        search_terms.extend(['pen', 'cil'])
    # Add the first 4-5 characters as a fallback
    if len(search_query) > 4:
        search_terms.append(search_query[:4])

    logger.debug(f"Searching for '{search_query}' with terms: {search_terms}")

    # Get user info for filtering
    user_university = ""
    user_faculty = ""
    if user:
        user_university = (getattr(user, 'university', '') or '').lower().strip()
        user_faculty = (getattr(user, 'faculty', '') or '').lower().strip()

    logger.debug(f"User university: '{user_university}', faculty: '{user_faculty}'")

    # Base queryset
    base_queryset = Product.objects.filter(status='active').select_related('category', 'seller')
    final_results = []

    # Define search strategies - check each search term
    search_strategies = []
    for term in search_terms:
        search_strategies.extend([
            ('title__icontains', term),
            ('description__icontains', term),
            ('category__name__icontains', term)
        ])

    # Use a set to track product IDs and avoid duplicates
    seen_product_ids = set()

    # LEVEL 0: Specified location in query (highest priority if location mentioned)
    if specified_location:
        logger.debug(f"Level 0 - Searching ONLY in specified location: {specified_location}")
        level0_products = []

        for field, value in search_strategies:
            if len(level0_products) >= 3:
                break

            products = base_queryset.filter(**{field: value})
            # Filter by governorate (location)
            products = products.filter(governorate__iexact=specified_location)
            products = products.order_by('price')  # Cheapest first

            for product in products:
                if product.id not in seen_product_ids and len(level0_products) < 3:
                    level0_products.append(product)
                    seen_product_ids.add(product.id)

        final_results.extend(level0_products)
        logger.debug(f"Level 0 found {len(level0_products)} products in {specified_location}")

        # For location-specific searches, if no products found in that location,
        # return empty results (don't fall back to other locations)
        return format_products(final_results)

    # LEVEL 1: Same university + same faculty (highest priority)
    if user_university and user_faculty:
        logger.debug("Level 1 - Searching same university + same faculty")
        level1_products = []

        for field, value in search_strategies:
            if len(level1_products) >= 3:
                break

            products = base_queryset.filter(**{field: value})
            products = products.filter(university__iexact=user_university, faculty__iexact=user_faculty)
            products = products.order_by('price')  # Cheapest first

            for product in products:
                if product.id not in seen_product_ids and len(level1_products) < 3:
                    level1_products.append(product)
                    seen_product_ids.add(product.id)

        final_results.extend(level1_products)
        logger.debug(f"Level 1 found {len(level1_products)} products")

        # If we have results from level 1, return them
        if final_results:
            return format_products(final_results)

    # LEVEL 2: Same university + different faculty (medium priority)
    if user_university and len(final_results) < 3:
        logger.debug("Level 2 - Searching same university + different faculty")
        level2_products = []

        for field, value in search_strategies:
            if len(level2_products) >= 3:
                break

            products = base_queryset.filter(**{field: value})
            products = products.filter(university__iexact=user_university)

            # Exclude user's faculty to get different faculties
            if user_faculty:
                products = products.exclude(faculty__iexact=user_faculty)

            products = products.order_by('price')  # Cheapest first

            for product in products:
                if product.id not in seen_product_ids and len(level2_products) < 3:
                    level2_products.append(product)
                    seen_product_ids.add(product.id)

        final_results.extend(level2_products)
        logger.debug(f"Level 2 found {len(level2_products)} products")

        # If we have results from level 2, return them
        if final_results:
            return format_products(final_results)

    # LEVEL 3: Transfer not available - general search (lowest priority)
    logger.debug("Level 3 - Transfer not available, general search")
    level3_products = []

    for field, value in search_strategies:
        if len(level3_products) >= 3:
            break

        products = base_queryset.filter(**{field: value})
        products = products.order_by('price')  # Cheapest first

        for product in products:
            if product.id not in seen_product_ids and len(level3_products) < 3:
                level3_products.append(product)
                seen_product_ids.add(product.id)

    final_results.extend(level3_products)
    logger.debug(f"Level 3 found {len(level3_products)} products")

    return format_products(final_results)


def format_products(products):
    """Helper function to format product queryset to dictionary"""
    results = []
    for product in products:
        results.append({
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": float(product.price),
            "condition": product.condition,
            "category": product.category.name if product.category else "No category",
            "university": product.university or "Not specified",
            "faculty": product.faculty or "Not specified",
            "seller": {
                "id": product.seller.id,
                "name": product.seller.first_name or product.seller.username,
                "username": product.seller.username,
            } if product.seller else {"name": "Unknown Seller"}
        })
    return results


def get_personalized_recommendations(user):
    """
    Get products recommended for the user's university and faculty
    Only recommend if there's a university/faculty match
    Case-insensitive matching
    """
    university = (getattr(user, 'university', '') or '').lower().strip()
    faculty = (getattr(user, 'faculty', '') or '').lower().strip()

    logger.debug(f"Getting recommendations for university: {university}, faculty: {faculty}")

    if not university and not faculty:
        # No university/faculty info, return empty recommendations
        return []

    # Search for products by PRODUCT university and faculty
    products = Product.objects.filter(status='active').select_related('category', 'seller')

    matching_products = []

    for product in products:
        # Case-insensitive comparison
        product_university = (product.university or '').lower().strip()
        product_faculty = (product.faculty or '').lower().strip()

        matches = []

        if university and product_university == university:
            matches.append('university')
        if faculty and product_faculty == faculty:
            matches.append('faculty')

        # Include if at least one field matches (university or faculty)
        if matches:
            matching_products.append(product)
            logger.debug(f"Product '{product.title}' matches on: {matches}")
            if len(matching_products) >= 10:  # Limit to 10
                break

    products = matching_products
    
    # Convert to list
    products = list(products)

    results = []
    for product in products:
        results.append({
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": float(product.price),
            "condition": product.condition,
            "category": product.category.name if product.category else "No category",
            "university": product.university or "Not specified",
            "faculty": product.faculty or "Not specified",
            "seller": {
                "id": product.seller.id,
                "name": product.seller.first_name or product.seller.username,
                "username": product.seller.username,
            } if product.seller else {"name": "Unknown Seller"}
        })

    return results


@method_decorator(csrf_exempt, name="dispatch")
class ChatbotAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_permissions(self):
        return [permissions.AllowAny()]

    def post(self, request):
        try:
            is_initial = request.data.get("initial", False)
            if is_initial:
                # Return initial welcome message
                return Response({
                    "reply": "Looking for something specific? Can I help you?",
                    "products": []
                    }, status=status.HTTP_200_OK)

            # Handle audio file if present
            audio_file = request.FILES.get('audio')
            image_file = request.FILES.get('image')
            transcribe_only = request.data.get('transcribe_only', 'false').lower() == 'true'
            user_message = ""
            image_analysis = None
            
            client = OpenAI(api_key=OPENAI_API_KEY)

            if audio_file:
                try:
                    # Save temporary file for Whisper
                    import tempfile
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    
                    # Create a temp file path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                        for chunk in audio_file.chunks():
                            temp_audio.write(chunk)
                        temp_audio_path = temp_audio.name

                    # Transcribe using Whisper (auto-detects language - supports Arabic and English)
                    with open(temp_audio_path, "rb") as audio:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio
                            # No language parameter = auto-detect (supports Arabic, English, etc.)
                        )
                    
                    
                    user_message = transcription.text
                    logger.debug(f"Transcribed audio to: '{user_message}'")
                    
                    # Clean up temp file
                    os.remove(temp_audio_path)
                    
                    # If transcribe_only mode, return just the transcription
                    if transcribe_only:
                        return Response({"transcription": user_message}, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    logger.error(f"Error processing audio: {e}")
                    return Response({"error": "Failed to process audio recording"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle image file if present - analyze for product search
            if image_file:
                try:
                    import base64
                    
                    # Read image and encode to base64
                    image_data = image_file.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    image_mime = image_file.content_type or 'image/jpeg'
                    
                    # Ask GPT-4o Vision to analyze the image for product identification
                    vision_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Analyze this image and identify what product or item type it shows. Return ONLY a short search query (1-3 words) that describes the main product. Examples: 'circuit board', 'arduino', 'lab coat', 'calculator', 'ruler'. Be specific but concise."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{image_mime};base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=50
                    )
                    
                    image_analysis = vision_response.choices[0].message.content.strip()
                    logger.debug(f"Image analysis result: '{image_analysis}'")
                    
                except Exception as e:
                    logger.error(f"Error analyzing image: {e}")
                    image_analysis = None
            
            # Get text message if no audio
            if not audio_file:
                # Standard text message
                serializer = ChatbotSerializer(data=request.data)
                # If serializer is invalid and we didn't have audio, return error
                # Note: if audio was sent, we might not have a message body, so we skip serializer validation of 'message'
                if not serializer.is_valid():
                    # Check if we got 'message' in data even if serializer complained (e.g. standard form data)
                    user_message = request.data.get('message', '')
                    if not user_message and not image_file:
                         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user_message = serializer.validated_data.get("message", "")

            # If we have image analysis but no/empty user message, use image analysis as the query
            if image_analysis and not user_message.strip():
                user_message = f"I'm looking for products similar to this: {image_analysis}"
            elif image_analysis and user_message.strip():
                # Combine user message with image analysis context
                user_message = f"{user_message}. [The user also attached an image that appears to show: {image_analysis}]"

            if not user_message:
                 return Response({"error": "No message provided"}, status=status.HTTP_400_BAD_REQUEST)

            if not OPENAI_API_KEY:
                if settings.DEBUG:
                    logger.debug("OpenAI API key missing, returning mock response")
                    # Mock response for testing when API key is missing
                    mock_products = search_products(user_message, request.user if request.user.is_authenticated else None)
                    return Response({
                        "reply": f"I'm currently in test mode (no API key). I found {len(mock_products)} products matching '{user_message}'.",
                        "products": mock_products
                    }, status=status.HTTP_200_OK)
                
                return Response(
                    {"error": "OpenAI API key not configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Define functions for product search and personalized recommendations
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_products",
                        "description": "Search for available college tools and supplies in our e-commerce store",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The tool or item to search for (e.g., ruler, calculator, thermometer)",
                                }
                            },
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_personalized_recommendations",
                        "description": "Get personalized product recommendations based on the user's location, university and faculty",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "escalate_to_supervisor",
                        "description": "Escalate a user issue to a human supervisor when the AI cannot resolve the problem. Use this when: 1) The user is frustrated after multiple attempts to help, 2) The issue requires human intervention (refunds, account issues, disputes), 3) Technical bugs that need developer attention, 4) The user explicitly requests to speak with a human.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "issue_summary": {
                                    "type": "string",
                                    "description": "A brief summary of the user's issue and what has been attempted to resolve it"
                                },
                                "issue_type": {
                                    "type": "string",
                                    "enum": ["technical_bug", "payment_issue", "account_problem", "product_complaint", "seller_dispute", "feature_request", "other"],
                                    "description": "Category of the issue"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high"],
                                    "description": "Priority level based on urgency and user frustration"
                                }
                            },
                            "required": ["issue_summary", "issue_type", "priority"]
                        }
                    }
                }
            ]

            system_prompt = """
            You are a helpful AI assistant for a college supplies e-commerce website called "Eagerly" (also known as "Classifieds").
            You help students find and purchase tools they need for their studies, AND you provide customer support.

            === PRODUCT SEARCH ===
            CRITICAL: When a user asks about ANY tools, supplies, or items for sale, ALWAYS use the search_products function first. Do not answer from memory or make up information.
            
            Available tools and supplies include: rulers, calculators, thermometers, notebooks, pens, pencils, erasers, geometry sets, laboratory equipment, measuring tools, and many other study supplies.

            When products are found:
            - Take direct action: Always navigate the user to the product details page automatically
            - Say something brief like "Found it! Here are the options..." 

            LOCATION-BASED SEARCHES: If a user specifies a location, the search prioritizes products from that location.

            === CUSTOMER SUPPORT ===
            You also handle customer support, troubleshooting, and complaints. Common issues include:
            
            **Technical Issues:**
            - Login/registration problems → Suggest: clear browser cache, try different browser, check email for verification
            - Page not loading → Suggest: refresh, check internet connection, try incognito mode
            - Images not displaying → Suggest: refresh page, check internet speed
            - Payment failing → Suggest: check card details, try different payment method, ensure sufficient funds
            - App crashes → Suggest: update browser, clear cache, disable extensions
            
            **Account Issues:**
            - Forgot password → Direct to "Forgot Password" link on login page
            - Can't verify email → Suggest checking spam folder, request new verification email
            - Profile not updating → Suggest: log out and back in, clear cache
            
            **Product/Order Issues:**
            - Product not as described → Advise to contact seller first via chat, explain dispute process
            - Seller not responding → Suggest waiting 24-48 hours, then escalate
            - Want refund → Explain the platform connects buyers/sellers directly, refunds depend on seller
            
            **Platform Navigation:**
            - How to post ad → Explain: go to "My Ads" → "Add New Product" → fill details → submit
            - How to contact seller → Explain: click on product → "Chat with Seller" button
            - How to edit/delete listing → Go to "My Ads" → find listing → edit/delete options
            
            **Troubleshooting Approach:**
            1. Listen carefully and acknowledge the user's frustration
            2. Ask clarifying questions if needed
            3. Provide step-by-step solutions
            4. If first solution doesn't work, try alternatives
            5. If you cannot resolve after 2-3 attempts OR the user is very frustrated OR it requires human intervention → USE escalate_to_supervisor function

            === ESCALATION RULES ===
            Use escalate_to_supervisor when:
            - User explicitly asks for a human/manager/supervisor
            - Issue involves money/payments that need manual review  
            - Account is locked or banned (needs admin)
            - Dispute between buyer and seller
            - Bug that you cannot help troubleshoot
            - User remains unsatisfied after your troubleshooting attempts
            - Any issue you genuinely cannot resolve

            When escalating, be empathetic: "I understand this is frustrating. Let me escalate this to our support team who will personally look into this for you."

            === LANGUAGE ===
            Respond in the same language the user writes in (Arabic or English).
            Be friendly, helpful, and professional. Use emojis sparingly for friendliness.
            """

            # Always enable tools for this assistant
            chat_completion = client.chat.completions.create(
                model="gpt-4o",  # Use a widely available model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                tools=tools,
                tool_choice="auto",  # Let AI decide when to use tools
                temperature=0.7,
                max_tokens=500
            )

            response_message = chat_completion.choices[0].message

            # Track if we had a search function call
            searched_products = None
            search_query = None

            # Check if the model wants to call a function
            if response_message.tool_calls:
                # Call the function
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "search_products":
                        # Parse the arguments
                        args = json.loads(tool_call.function.arguments)
                        search_query = args.get("query", "")
                        print(f"DEBUG: Searching for: {search_query}")

                        # Search for products (pass user for hierarchical filtering)
                        # Handle anonymous user for public access
                        search_user = request.user if request.user.is_authenticated else None
                        searched_products = search_products(search_query, search_user)
                        logger.debug(f"Found products: {len(searched_products)}")

                        # Add the function result to the conversation
                        chat_completion = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message},
                                response_message,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": json.dumps(searched_products)
                                }
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )

                        response_message = chat_completion.choices[0].message
                        logger.debug(f"Final response content: '{response_message.content}'")

                    elif tool_call.function.name == "get_personalized_recommendations":
                        print("DEBUG: Getting personalized recommendations")
                        
                        # Get recommendations
                        search_user = request.user if request.user.is_authenticated else None
                        searched_products = get_personalized_recommendations(search_user)
                        logger.debug(f"Found recommendations: {len(searched_products)}")
                        
                        # Add the function result to the conversation
                        chat_completion = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message},
                                response_message,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": json.dumps(searched_products)
                                }
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        response_message = chat_completion.choices[0].message
                        logger.debug(f"Final response content: '{response_message.content}'")

                    elif tool_call.function.name == "escalate_to_supervisor":
                        logger.debug("Escalating issue to supervisor")
                        
                        # Parse escalation details
                        args = json.loads(tool_call.function.arguments)
                        issue_summary = args.get("issue_summary", "No summary provided")
                        issue_type = args.get("issue_type", "other")
                        priority = args.get("priority", "medium")
                        
                        # Get user info if authenticated
                        user_info = "Anonymous user"
                        user_email = None
                        if request.user.is_authenticated:
                            user_info = f"User: {request.user.username} (ID: {request.user.id})"
                            user_email = getattr(request.user, 'email', None)
                        
                        # Log the escalation (in production, save to database or send to support system)
                        escalation_data = {
                            "timestamp": str(json.dumps({"time": "now"})),  # Will be replaced by actual timestamp
                            "user": user_info,
                            "user_email": user_email,
                            "issue_type": issue_type,
                            "priority": priority,
                            "summary": issue_summary,
                            "original_message": user_message
                        }
                        
                        logger.info(f"=== SUPPORT TICKET ESCALATION ===")
                        logger.info(f"Priority: {priority.upper()}")
                        logger.info(f"Type: {issue_type}")
                        logger.info(f"User: {user_info}")
                        logger.info(f"Summary: {issue_summary}")
                        logger.info(f"Original message: {user_message}")
                        logger.info(f"=================================")
                        
                        # TODO: In production, save to SupportTicket model or send to external system
                        # Example: SupportTicket.objects.create(**escalation_data)
                        
                        # Return confirmation to AI
                        escalation_result = {
                            "status": "escalated",
                            "ticket_created": True,
                            "message": "Issue has been escalated to human support. A supervisor will review and respond within 24-48 hours."
                        }
                        
                        # Add the function result to the conversation
                        chat_completion = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message},
                                response_message,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": json.dumps(escalation_result)
                                }
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        response_message = chat_completion.choices[0].message
                        logger.debug(f"Final response content: '{response_message.content}'")

            else:
                logger.debug("No tool calls made by AI")

            # Extract the final response
            bot_reply = response_message.content or ""

            # Prepare response data
            response_data = {"reply": bot_reply}

            # Generate Audio Response (TTS)
            if bot_reply:
                try:
                    import base64
                    
                    # Limit text length for TTS to avoid excessive usage/latency
                    tts_text = bot_reply[:1000] 
                    
                    speech_response = client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=tts_text
                    )
                    
                    # Get binary data
                    audio_binary = speech_response.content
                    # Encode to base64
                    audio_base64 = base64.b64encode(audio_binary).decode('utf-8')
                    
                    response_data["audio"] = f"data:audio/mp3;base64,{audio_base64}"
                    
                except Exception as e:
                    logger.error(f"TTS Error: {e}")
                    # Don't fail the whole request if separate TTS fails
                    pass

            # Always include product data if we searched (even if AI response is empty)
            if searched_products is not None:
                response_data["products"] = searched_products
                logger.debug(f"Including {len(searched_products)} products in response")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.error("CRITICAL ERROR IN CHATBOT VIEW:", exc_info=True)
            return Response(
                {
                    "error": "internal_server_error",
                    "detail": str(exc) if settings.DEBUG else "Server error",
                    "trace": traceback.format_exc() if settings.DEBUG else None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
