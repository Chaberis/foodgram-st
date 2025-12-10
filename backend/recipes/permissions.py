from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение на редактирование только для автора рецепта."""
    
    def has_object_permission(self, request, view, obj):
        """Проверка прав доступа к объекту."""
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user

