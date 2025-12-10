"""Views для работы с рецептами."""
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
from collections import defaultdict



from .models import Recipe, ShoppingCart, Favorite, RecipeIngredient
from .serializers import (
    RecipeSerializer,
    RecipeCreateSerializer,
    RecipeUpdateSerializer,
    RecipeMinifiedSerializer,
)
from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from users.pagination import CustomPageNumberPagination


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами (CRUD операции)."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            return RecipeCreateSerializer
        if self.action in ['update', 'partial_update']:
            return RecipeUpdateSerializer
        return RecipeSerializer

    def get_permissions(self):
        """Настройка прав доступа."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        elif self.action in ['shopping_cart', 'download_shopping_cart', 'favorite']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        """Оптимизация запросов с prefetch_related."""
        return Recipe.objects.select_related('author').prefetch_related(
            'recipe_ingredients__ingredient'
        )

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({
            'short-link': short_link
        })

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite_item = Favorite.objects.filter(user=user, recipe=recipe).first()
            if not favorite_item:
                return Response(
                    {'errors': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из корзины."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в корзину.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe).first()
            if not cart_item:
                return Response(
                    {'errors': 'Рецепт не найден в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        

        user = request.user
        cart_recipes = ShoppingCart.objects.filter(user=user).select_related(
            'recipe'
        ).prefetch_related(
            'recipe__recipe_ingredients__ingredient'
        )

        buy_list = {}
        for item in cart_recipes:
            for recipe_item in item.recipe.recipe_ingredients.all():
                name = recipe_item.ingredient.name
                unit = recipe_item.ingredient.measurement_unit
                amount = recipe_item.amount

                key = (name, unit)
                if key in buy_list:
                    buy_list[key] += amount
                else:
                    buy_list[key] = amount

        today = timezone.now().strftime('%d-%m-%Y')
        shopping_list = [f'Список покупок на {today}:\n\n']

        for (name, unit), amount in sorted(buy_list.items()):
            shopping_list.append(f'• {name}: {amount} {unit}\n')

        shopping_list.append(f'\nВсего позиций: {len(buy_list)}')

        response = HttpResponse(
            ''.join(shopping_list),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="foodgram_shopping_list.txt"'
        return response