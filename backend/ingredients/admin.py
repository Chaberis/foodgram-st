from django.contrib import admin
from .models import Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    
    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'Кол-во рецептов'
