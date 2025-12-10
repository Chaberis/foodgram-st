"""Views для работы с пользователями."""
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    SetPasswordSerializer,
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
    UserWithRecipesSerializer,
)
from .pagination import CustomPageNumberPagination
from .models import Subscription

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями (CRUD операции)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """Настройка прав доступа."""
        if self.action in ['subscribe', 'subscriptions', 'me', 'set_password', 'avatar']:
            return [IsAuthenticated()]
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(
        detail=False,
        methods=['get'],
        url_path='me'
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password'
    )
    def set_password(self, request):
        """Изменение пароля текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Добавление или удаление аватара текущего пользователя."""
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            user = request.user
            user.avatar = serializer.validated_data['avatar']
            user.save()
            response_serializer = SetAvatarResponseSerializer(
                user,
                context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            user = request.user
            if user.avatar:
                user.avatar.delete()
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        """Подписка или отписка от пользователя."""
        user = request.user
        author = self.get_object()

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user,
                author=author
            ).first()
            if not subscription:
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        user = request.user

        subscribed_authors = User.objects.filter(
            subscribers__user=user
        ).prefetch_related('recipes')

        paginated_queryset = self.paginate_queryset(subscribed_authors)

        serializer = UserWithRecipesSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        
        return self.get_paginated_response(serializer.data)
