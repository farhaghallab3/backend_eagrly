# Fix for Product Governorate Field Database Constraint

## Problem
Creating new products was failing with `500 Internal Server Error` and the error:
```
django.db.utils.IntegrityError: NOT NULL constraint failed: products_product.governorate
```

## Root Cause
The database migration `0004_product_governorate.py` added the `governorate` field with `blank=True`, but the Django model definition was missing this field entirely. This caused:

1. The serializer not handling the `governorate` field in API requests
2. Frontend not sending `governorate` data
3. Database constraint violation when trying to save products

## Solution Applied

### 1. Updated Product Model
Added the missing `governorate` field to the Product model in `apps/products/models.py`:
```python
governorate = models.CharField(max_length=255, blank=True, default='')
```

### 2. Updated Product Serializer
Added `governorate` to the ProductSerializer fields in `apps/products/serializers.py`:
```python
fields = ['id', 'title', 'description', 'price', 'condition', 'image', 'images', 'category', 'seller', 'university', 'faculty', 'governorate', 'is_featured', 'status', 'created_at', 'updated_at', 'category_name']
```

### 3. Created Migration
Created and applied migration `0005_fix_governorate_default.py` to ensure the database schema matches the model definition.

## Result
Product creation now works correctly. The `governorate` field is optional (blank=True) and defaults to an empty string, preventing NOT NULL constraint violations.

## Frontend Note
The `ProductForm.jsx` in the frontend does not currently include a field for governorate input. If you want users to be able to specify a governorate, you should add it as an optional text input in the product creation/edit form.
