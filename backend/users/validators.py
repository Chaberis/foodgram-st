"""Валидаторы для пользователей."""
from rest_framework import serializers


def validate_current_password(value, user):
    """
    Валидация текущего пароля пользователя.
    
    Args:
        value: Текущий пароль
        user: Пользователь, для которого проверяется пароль
        
    Returns:
        value: Валидированный пароль
        
    Raises:
        ValidationError: Если пароль неверный
    """
    if not user.check_password(value):
        raise serializers.ValidationError('Неверный текущий пароль.')
    return value

