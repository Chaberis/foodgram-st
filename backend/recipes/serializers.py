from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from .models import Recipe, RecipeIngredient, ShoppingCart, Favorite
from .validators import (
    validate_recipe_image,
    validate_recipe_ingredients_present,
    validate_ingredients,
)


def fix_media_url(url, request=None):
    """Исправляет URL медиафайла, добавляя порт 8080 если его нет."""
    if not url:
        return url
    
    # Если URL уже абсолютный
    if url.startswith('http://'):
        # Заменяем localhost без порта или с другим портом на localhost:8080
        import re
        # Заменяем http://localhost/ или http://localhost:8000/ на http://localhost:8080/
        url = re.sub(r'http://localhost(?!:8080)(?::\d+)?/', 'http://localhost:8080/', url)
        # Заменяем http://127.0.0.1/ или http://127.0.0.1:8000/ на http://127.0.0.1:8080/
        url = re.sub(r'http://127\.0\.0\.1(?!:8080)(?::\d+)?/', 'http://127.0.0.1:8080/', url)
        return url
    
    # Если URL относительный, делаем его абсолютным с портом
    if url.startswith('/media/'):
        if request:
            # Пытаемся использовать request, но исправляем порт
            base_url = request.build_absolute_uri('/')
            # Заменяем порт на 8080 если это localhost
            import re
            base_url = re.sub(r'http://localhost(?!:8080)(?::\d+)?', 'http://localhost:8080', base_url)
            base_url = re.sub(r'http://127\.0\.0\.1(?!:8080)(?::\d+)?', 'http://127.0.0.1:8080', base_url)
            return base_url.rstrip('/') + url
        else:
            return f'http://localhost:8080{url}'
    
    return url


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента в рецепте."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания связи рецепт-ингредиент."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта."""
    author = serializers.SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('id', 'author')

    def get_author(self, obj):
        """Возвращает информацию об авторе."""
        from users.serializers import UserSerializer
        return UserSerializer(obj.author, context=self.context).data

    def get_is_favorited(self, obj):
        """Проверка избранного."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверка корзины."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_image(self, obj):
        """Возвращает полный URL изображения."""
        if obj.image:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.image.url)
                return fix_media_url(url, request)
            return fix_media_url(obj.image.url)
        return None


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""
    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, attrs):
        """Валидация всех полей."""
        validate_recipe_image(self, self.initial_data)

        validate_recipe_ingredients_present(self, self.initial_data)
        
        return attrs

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        return validate_ingredients(value)

    def create(self, validated_data):
        """Создание рецепта с ингредиентами."""
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def to_representation(self, instance):
        """Возвращает рецепт в формате RecipeSerializer."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeUpdateSerializer(RecipeCreateSerializer):
    """Сериализатор для обновления рецепта."""
    image = Base64ImageField(required=False)

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами."""
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )

        return instance


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта (для корзины и избранного)."""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def get_image(self, obj):
        """Возвращает полный URL изображения."""
        if obj.image:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.image.url)
                return fix_media_url(url, request)
            return fix_media_url(obj.image.url)
        return None

