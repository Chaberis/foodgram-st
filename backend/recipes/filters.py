from django_filters import rest_framework as filters
from .models import Recipe, ShoppingCart, Favorite


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""
    author = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        help_text='Фильтр по ID автора'
    )
    is_favorited = filters.NumberFilter(
        method='filter_is_favorited',
        help_text='Фильтр по избранному (0 или 1)'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart',
        help_text='Фильтр по корзине (0 или 1)'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по избранному."""
        request = self.request
        if not request or not request.user.is_authenticated:
            return queryset

        user = request.user
        if value == 1:
            recipe_ids = Favorite.objects.filter(
                user=user
            ).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=recipe_ids)
        elif value == 0:
            recipe_ids = Favorite.objects.filter(
                user=user
            ).values_list('recipe_id', flat=True)
            return queryset.exclude(id__in=recipe_ids)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по корзине."""
        request = self.request
        if not request or not request.user.is_authenticated:
            return queryset

        user = request.user
        if value == 1:
            recipe_ids = ShoppingCart.objects.filter(
                user=user
            ).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=recipe_ids)
        elif value == 0:
            recipe_ids = ShoppingCart.objects.filter(
                user=user
            ).values_list('recipe_id', flat=True)
            return queryset.exclude(id__in=recipe_ids)
        return queryset

