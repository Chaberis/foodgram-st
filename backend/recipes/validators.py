"""Валидаторы для рецептов."""
from rest_framework import serializers
from ingredients.models import Ingredient


def validate_recipe_image(serializer, initial_data):
    """
    Валидация изображения рецепта.
    
    Args:
        serializer: Экземпляр сериализатора
        initial_data: Исходные данные запроса
        
    Raises:
        ValidationError: Если изображение отсутствует или пустое
    """
    image_data = initial_data.get('image', '')
    if not image_data or image_data.strip() == '':
        raise serializers.ValidationError({
            'image': ['Изображение обязательно для заполнения.']
        })


def validate_recipe_ingredients_present(serializer, initial_data):
    """
    Валидация наличия ингредиентов в запросе.
    
    Args:
        serializer: Экземпляр сериализатора
        initial_data: Исходные данные запроса
        
    Raises:
        ValidationError: Если поле ingredients отсутствует
    """
    if 'ingredients' not in initial_data:
        raise serializers.ValidationError({
            'ingredients': ['Это поле обязательно.']
        })


def validate_ingredients(value):
    """
    Валидация списка ингредиентов.
    
    Args:
        value: Список словарей с ингредиентами
        
    Returns:
        value: Валидированный список ингредиентов
        
    Raises:
        ValidationError: Если ингредиенты невалидны
    """
    if not value:
        raise serializers.ValidationError(
            'Необходимо указать хотя бы один ингредиент.'
        )
    
    ingredient_ids = [item['id'] for item in value]

    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise serializers.ValidationError(
            'Ингредиенты не должны повторяться.'
        )

    existing_ids = set(
        Ingredient.objects.filter(id__in=ingredient_ids).values_list('id', flat=True)
    )
    missing_ids = set(ingredient_ids) - existing_ids
    if missing_ids:
        raise serializers.ValidationError(
            f'Ингредиенты с id {list(missing_ids)} не найдены в базе данных.'
        )
    
    return value

