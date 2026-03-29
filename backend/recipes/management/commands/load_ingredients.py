import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Скрипт для загрузки списка ингредиентов в БД из файла."""

    help = 'Импорт ингредиентов из CSV или JSON в базу данных'

    def handle(self, *args, **options):
        """Основные настройки загурузки."""
        data_dir = os.path.join(settings.BASE_DIR.parent, 'data')
        csv_path = os.path.join(data_dir, 'ingredients.csv')
        json_path = os.path.join(data_dir, 'ingredients.json')

        if os.path.exists(csv_path):
            self.import_from_csv(csv_path)
        elif os.path.exists(json_path):
            self.import_from_json(json_path)
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Файл ingredients.csv или ingredients.json не найден'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Импорт ингредиентов завершён'))

    def import_from_csv(self, path):
        """Импорт ингредиентов из ingredients.csv."""
        with open(path, encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    ingredient, created = Ingredient.objects.update_or_create(
                        name=row[0].strip().lower(),
                        defaults={'measurement_unit': row[1].strip()}
                    )
                    if created:
                        self.stdout.write(f'Добавлен: {ingredient.name}')

    def import_from_json(self, path):
        """Импорт ингредиентов из ingredients.json."""
        with open(path, encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                ingredient, created = Ingredient.objects.update_or_create(
                    name=item['name'].lower(),
                    defaults={'measurement_unit': item['measurement_unit']}
                )
                if created:
                    self.stdout.write(f'Добавлен: {ingredient.name}')
