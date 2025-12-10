from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .validators import validate_current_password


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

User = get_user_model()


def get_subscription_status(user, obj):
    """Проверка подписки пользователя на автора."""
    if user and user.is_authenticated:
        from .models import Subscription
        return Subscription.objects.filter(user=user, author=obj).exists()
    return False


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = ('id', 'email', 'username')

    def get_is_subscribed(self, obj):
        """Проверка подписки."""
        request = self.context.get('request')
        user = request.user if request else None
        return get_subscription_status(user, obj)

    def get_avatar(self, obj):
        """Возвращает полный URL аватара."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.avatar.url)
                return fix_media_url(url, request)
            return fix_media_url(obj.avatar.url)
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Создание пользователя с хешированием пароля."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """Проверка текущего пароля."""
        user = self.context['request'].user
        return validate_current_password(value, user)

    def save(self):
        """Установка нового пароля."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор для добавления аватара."""
    avatar = Base64ImageField()


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа после добавления аватара."""
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('avatar',)

    def get_avatar(self, obj):
        """Возвращает полный URL аватара."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.avatar.url)
                return fix_media_url(url, request)
            return fix_media_url(obj.avatar.url)
        return None


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с рецептами (для подписок)."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки."""
        request = self.context.get('request')
        user = request.user if request else None
        return get_subscription_status(user, obj)

    def get_recipes(self, obj):
        """Получение рецептов автора с ограничением количества."""
        from recipes.serializers import RecipeMinifiedSerializer
        request = self.context.get('request')

        recipes_limit = request.query_params.get('recipes_limit') if request else None
        try:
            recipes_limit = int(recipes_limit) if recipes_limit else None
        except (ValueError, TypeError):
            recipes_limit = None

        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]
        
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        """Общее количество рецептов автора."""
        return obj.recipes.count()

    def get_avatar(self, obj):
        """Возвращает полный URL аватара."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.avatar.url)
                return fix_media_url(url, request)
            return fix_media_url(obj.avatar.url)
        return None
