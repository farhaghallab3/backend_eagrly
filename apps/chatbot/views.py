from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .serializers import ChatbotSerializer
from openai import OpenAI
import os
import json
import traceback
from apps.products.models import Product, Category

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
    print(f"DEBUG: Parsed location from query: '{specified_location}'")

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

    print(f"DEBUG: Searching for '{search_query}' with terms: {search_terms}")

    # Get user info for filtering
    user_university = ""
    user_faculty = ""
    if user:
        user_university = (getattr(user, 'university', '') or '').lower().strip()
        user_faculty = (getattr(user, 'faculty', '') or '').lower().strip()

    print(f"DEBUG: User university: '{user_university}', faculty: '{user_faculty}'")

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
        print(f"DEBUG: Level 0 - Searching ONLY in specified location: {specified_location}")
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
        print(f"DEBUG: Level 0 found {len(level0_products)} products in {specified_location}")

        # For location-specific searches, if no products found in that location,
        # return empty results (don't fall back to other locations)
        return format_products(final_results)

    # LEVEL 1: Same university + same faculty (highest priority)
    if user_university and user_faculty:
        print("DEBUG: Level 1 - Searching same university + same faculty")
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
        print(f"DEBUG: Level 1 found {len(level1_products)} products")

        # If we have results from level 1, return them
        if final_results:
            return format_products(final_results)

    # LEVEL 2: Same university + different faculty (medium priority)
    if user_university and len(final_results) < 3:
        print("DEBUG: Level 2 - Searching same university + different faculty")
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
        print(f"DEBUG: Level 2 found {len(level2_products)} products")

        # If we have results from level 2, return them
        if final_results:
            return format_products(final_results)

    # LEVEL 3: Transfer not available - general search (lowest priority)
    print("DEBUG: Level 3 - Transfer not available, general search")
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
    print(f"DEBUG: Level 3 found {len(level3_products)} products")

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

    print(f"DEBUG: Getting recommendations for university: {university}, faculty: {faculty}")

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
            print(f"DEBUG: Product '{product.title}' matches on: {matches}")
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
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Allow anonymous access for initial load, require authentication for messages
        if self.request.data.get("initial", False):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def post(self, request):
        try:
            is_initial = request.data.get("initial", False)
            if is_initial:
                # Return initial welcome message
                return Response({
                    "reply": "Looking for something specific? Can I help you?",
                    "products": []
                    }, status=status.HTTP_200_OK)

            serializer = ChatbotSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user_message = serializer.validated_data["message"]

            if not OPENAI_API_KEY:
                return Response(
                    {"error": "OpenAI API key not configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            client = OpenAI(api_key=OPENAI_API_KEY)

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
                }
            ]

            system_prompt = """
            You are a helpful AI assistant for a college supplies e-commerce website called "Classifieds".
            You help students find and purchase tools they need for their studies.

            CRITICAL: When a user asks about ANY tools, supplies, or items for sale, ALWAYS use the search_products function first. Do not answer from memory or make up information.

            Available tools and supplies include: rulers, calculators, thermometers, notebooks, pens, pencils, erasers, geometry sets, laboratory equipment, measuring tools, and many other study supplies.

            When products are found:
            - Take direct action: Always navigate the user to the product details page automatically
            - The frontend will handle the automatic navigation when it receives products data
            - Say something brief like "Found it! Taking you to the product details..." followed by navigation

            IMPORTANT: When products are found, the frontend should automatically redirect to show product details. Include navigation message in response.

            LOCATION-BASED SEARCHES: If a user specifies a location (like "from Giza", "in Cairo", "Alexandria ruler"), the search prioritizes products from that location. If no products are found in the specified location, inform the user that the item is not available in that location and suggest checking other locations or browsing categories.

            If no products are found at all, suggest alternatives like browsing categories or asking for recommendations based on their university and faculty.

            Users can ask for recommendations at any time, and you can use get_personalized_recommendations to show products based on their university and faculty.
            """

            # Always enable tools for this assistant
            chat_completion = client.chat.completions.create(
                model="gpt-4o-mini",  # Use a cost-effective model
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
                        searched_products = search_products(search_query, request.user)
                        print(f"DEBUG: Found products: {len(searched_products)}")

                        # Add the function result to the conversation
                        chat_completion = client.chat.completions.create(
                            model="gpt-4o-mini",
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
                        print(f"DEBUG: Final response content: '{response_message.content}'")
            else:
                print("DEBUG: No tool calls made by AI")

            # Extract the final response
            bot_reply = response_message.content

            # Prepare response data
            response_data = {"reply": bot_reply}

            # Always include product data if we searched (even if AI response is empty)
            if searched_products is not None:
                response_data["products"] = searched_products
                print(f"DEBUG: Including {len(searched_products)} products in response")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as exc:
            return Response(
                {
                    "error": "internal_server_error",
                    "detail": str(exc) if settings.DEBUG else "Server error",
                    "trace": traceback.format_exc() if settings.DEBUG else None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
