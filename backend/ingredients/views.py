from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Ingredient
from .serializers import IngredientSerializer
from .filters import IngredientFilter


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None  # Список ингредиентов возвращается без пагинации
