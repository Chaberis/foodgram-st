"""
Management команда для загрузки ингредиентов из CSV или JSON файла.
"""
import csv
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ingredients.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из CSV или JSON файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Путь к файлу с ингредиентами (CSV или JSON)',
            default=None
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            help='Формат файла (csv или json)',
            default='csv'
        )

    def handle(self, *args, **options):
        file_path = options.get('file')
        file_format = options.get('format')

        # Определяем путь к файлу
        possible_paths = []
        
        if file_path:
            if os.path.isabs(file_path):
                # Абсолютный путь используем как есть
                possible_paths.append(file_path)
            else:
                # Относительный путь - ищем в нескольких местах
                # 1. В рабочей директории (текущая директория процесса)
                current_dir = os.getcwd()
                possible_paths.append(os.path.join(current_dir, file_path))
                # 2. В BASE_DIR проекта
                possible_paths.append(os.path.join(str(settings.BASE_DIR), file_path))
                # 3. В родительской директории BASE_DIR
                base_dir = settings.BASE_DIR.parent
                possible_paths.append(os.path.join(str(base_dir), file_path))
                # 4. Явно проверяем /app/ingredients.csv (для Docker)
                possible_paths.append(f'/app/{file_path}')
        else:
            # Используем файл по умолчанию
            base_dir = settings.BASE_DIR.parent
            if file_format == 'csv':
                default_file = 'ingredients.csv'
            else:
                default_file = 'ingredients.json'
            possible_paths.append(os.path.join(str(base_dir), 'data', default_file))
            possible_paths.append(os.path.join(os.getcwd(), default_file))
            possible_paths.append(f'/app/{default_file}')

        # Ищем первый существующий файл
        final_path = None
        for path in possible_paths:
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                final_path = normalized_path
                break
        
        if not final_path:
            self.stdout.write(
                self.style.ERROR('Файл не найден ни по одному из путей:')
            )
            self.stdout.write(
                self.style.WARNING(f'Текущая рабочая директория: {os.getcwd()}')
            )
            self.stdout.write(
                self.style.WARNING(f'BASE_DIR: {settings.BASE_DIR}')
            )
            for path in possible_paths:
                self.stdout.write(
                    self.style.WARNING(f'  - {os.path.normpath(path)}')
                )
            return
        
        file_path = final_path

        self.stdout.write(f'Загрузка ингредиентов из файла: {file_path}')

        if file_format == 'csv' or file_path.endswith('.csv'):
            self.load_from_csv(file_path)
        else:
            self.load_from_json(file_path)

    def load_from_csv(self, file_path):
        """Загрузка ингредиентов из CSV файла."""
        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row_num, row in enumerate(reader, start=1):
                    if len(row) < 2:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Строка {row_num}: пропущена (недостаточно данных)'
                            )
                        )
                        error_count += 1
                        continue

                    name = row[0].strip()
                    measurement_unit = row[1].strip()

                    if not name or not measurement_unit:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Строка {row_num}: пропущена (пустые значения)'
                            )
                        )
                        error_count += 1
                        continue

                    # Создаем или обновляем ингредиент
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=name,
                        defaults={'measurement_unit': measurement_unit}
                    )

                    if created:
                        created_count += 1
                    else:
                        # Обновляем единицу измерения, если она изменилась
                        if ingredient.measurement_unit != measurement_unit:
                            ingredient.measurement_unit = measurement_unit
                            ingredient.save()
                            updated_count += 1

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при чтении CSV файла: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'\nЗагрузка завершена!\n'
                f'Создано: {created_count}\n'
                f'Обновлено: {updated_count}\n'
                f'Ошибок: {error_count}'
            )
        )

    def load_from_json(self, file_path):
        """Загрузка ингредиентов из JSON файла."""
        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Проверяем формат JSON
            if not isinstance(data, list):
                self.stdout.write(
                    self.style.ERROR('JSON файл должен содержать список объектов')
                )
                return

            # Если это список словарей
            for item_num, item in enumerate(data, start=1):
                if not isinstance(item, dict):
                    self.stdout.write(
                        self.style.WARNING(
                            f'Элемент {item_num}: пропущен (неверный формат)'
                        )
                    )
                    error_count += 1
                    continue

                name = item.get('name', '').strip()
                measurement_unit = item.get('measurement_unit', '').strip()

                if not name or not measurement_unit:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Элемент {item_num}: пропущен (пустые значения)'
                        )
                    )
                    error_count += 1
                    continue

                # Создаем или обновляем ингредиент
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    defaults={'measurement_unit': measurement_unit}
                )

                if created:
                    created_count += 1
                else:
                    # Обновляем единицу измерения, если она изменилась
                    if ingredient.measurement_unit != measurement_unit:
                        ingredient.measurement_unit = measurement_unit
                        ingredient.save()
                        updated_count += 1

        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при парсинге JSON файла: {e}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при чтении JSON файла: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'\nЗагрузка завершена!\n'
                f'Создано: {created_count}\n'
                f'Обновлено: {updated_count}\n'
                f'Ошибок: {error_count}'
            )
        )

