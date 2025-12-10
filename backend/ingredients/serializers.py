from rest_framework import serializers
from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""
    
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        read_only_fields = ('id',)

