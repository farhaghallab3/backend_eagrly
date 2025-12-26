from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # لو المستخدم أدمن -> مسموح له دائمًا
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True

        # لو الـ obj هو المستخدم نفسه
        if hasattr(obj, "id") and obj == request.user:
            return True

        # common owner fields
        for attr in ('seller', 'user', 'reporter', 'reviewer', 'buyer', 'owner'):
            if hasattr(obj, attr):
                return getattr(obj, attr) == request.user

        return False


class IsOwnerOrAdminOrActiveProduct(permissions.BasePermission):
    """
    Custom permission for products that allows:
    - Admin users to do anything
    - Owners to access their own products
    - Anyone to view active products
    """
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True

        # Check if it's a product and it's active - allow anyone to view
        if hasattr(obj, 'status') and obj.status == 'active':
            # For safe methods (GET, HEAD, OPTIONS), allow anyone to view active products
            if request.method in permissions.SAFE_METHODS:
                return True

        # For authenticated users, allow owners to access their products
        if request.user and request.user.is_authenticated:
            # common owner fields
            for attr in ('seller', 'user', 'reporter', 'reviewer', 'buyer', 'owner'):
                if hasattr(obj, attr):
                    if getattr(obj, attr) == request.user:
                        return True

        # Default deny
        return False
