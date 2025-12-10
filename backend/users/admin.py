from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Subscription

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'recipes_count', 'subscribers_count', 'subscriptions_count', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'Кол-во рецептов'
    
    def subscribers_count(self, obj):
        return obj.subscribers.count()
    subscribers_count.short_description = 'Кол-во подписчиков'
    
    def subscriptions_count(self, obj):
        return obj.subscriptions.count()
    subscriptions_count.short_description = 'Кол-во подписок'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'user__email', 'author__username', 'author__email')
    list_filter = ('user', 'author')
