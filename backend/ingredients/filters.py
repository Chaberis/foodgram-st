from django_filters import rest_framework as filters
from .models import Ingredient


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        help_text='Поиск по частичному вхождению в начале названия ингредиента'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)

