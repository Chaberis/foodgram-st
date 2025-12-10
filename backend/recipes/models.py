from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название',
        max_length=256,
        help_text='Название рецепта'
    )
    text = models.TextField(
        'Описание',
        help_text='Описание рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(1)],
        help_text='Время приготовления в минутах'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
        help_text='Изображение рецепта'
    )
    ingredients = models.ManyToManyField(
        'ingredients.Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецепта и ингредиента."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        'ingredients.Ingredient',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
        help_text='Количество ингредиента в рецепте'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}: {self.amount}'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'