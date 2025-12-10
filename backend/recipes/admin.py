from django.contrib import admin
from .models import Recipe, RecipeIngredient, ShoppingCart, Favorite


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'cooking_time', 'created', 'favorites_count', 'shopping_cart_count', 'ingredients_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('created', 'cooking_time', 'author')
    readonly_fields = ('created',)
    filter_horizontal = ()
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'author', 'text', 'image', 'cooking_time')
        }),
        ('Дата создания', {
            'fields': ('created',)
        }),
    )
    
    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'Кол-во в избранном'
    
    def shopping_cart_count(self, obj):
        return obj.shopping_cart.count()
    shopping_cart_count.short_description = 'Кол-во в корзине'
    
    def ingredients_count(self, obj):
        return obj.recipe_ingredients.count()
    ingredients_count.short_description = 'Кол-во ингредиентов'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')
    autocomplete_fields = ('recipe', 'ingredient')


admin.site.register(Favorite)


admin.site.register(ShoppingCart)
