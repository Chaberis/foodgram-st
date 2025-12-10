from django.db import models


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        'Название',
        max_length=128,
        help_text='Название ингредиента'
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64,
        help_text='Единица измерения ингредиента (кг, г, л, шт и т.д.)'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'
