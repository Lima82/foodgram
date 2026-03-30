# Foodgram

## Описание
Foodgram - это онлайн-платформа дял публикации и поиска кулинарных рецептов.

Позволяет пользователям:
- публиковать собственные рецепты с фотографиями,
- добавлять чужие рецепты в избранное,
- подписываться на публикации других авторов,
- получить доступ к сервису «Список покупок» (для зарегистрированных пользователей),
- формировать список продуктов из выбранных рецептов,
- экспортировать «Список покупок» в форматах TXT или CSV,
- генерировать короткие ссылки на рецепты.

---

## Технологии
- Python
- Django
- Django REST Framework (DRF)
- Django Filter
- Djoser (аутентификация, регистрация, управление пользователями)
- Token Authentication (DRF токены)
- SQLite3 (разработка)/PostrgSQL (продакшен)
- Pillow (работа с изображениями)
- Gunicorn (WSGI-сервер)
- Docker, Docker Compose
- Nginx

---

## Установка и запуск проекта

1. **Клонирование репозитория и переход в него:**

```bash
git clone https://github.com/Lima82/foodgram.git
```
```bash
cd foodgram/backend
```
2. **Создание и активация виртуального окружения:**

```bash
python -m venv venv
```
- **Linux / macOS:**

```bash
source venv/bin/activate
```
- **Windows:**
```bash
venv\Scripts\activate
```
3. **Установка зависимостей:**

```bash
python -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```
4. **Применение миграций:**

```bash
python manage.py migrate
```
5. **Загрузка ингредиентов:**

```bash
python manage.py load_ingredients
```
6. **Создание суперпользователя (для доступа к админке):**

```bash
python manage.py createsuperuser
```
7. **Запуск сервера разработки:**

```bash
python manage.py runserver
```
Сервер будет доступен по адресу: http://127.0.0.1:8000/.

8. **Запуск контейнера frontend:**

Находясь в папке infra, выполните команду docker-compose up.

При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

Фронтенд веб-приложения будет доступен по адресу http://localhost.

Спецификацию API будет доступна по адресу http://localhost/api/docs/.

---

## Аутентификация

В проекте используется токен-аутентификация через библиотеку Djoser.

1. **Регистрация пользователя:**

```bash
POST /api/users/
```
Content-Type: application/json
```bash
{
  "email": "user@example.com",
  "username": "username",
  "first_name": "firstname",
  "last_name": "lastname",
  "password": "your_password"
}
```
2. **Получение токена (вход):**

```bash
POST /api/auth/token/login/
```
Content-Type: application/json
```bash
{
  "email": "user@example.com",
  "password": "your_password"
}
```
Ответ:
```bash
{
  "auth_token": "your_token"
}
```
3. **Использование токена:**

Authorization: Token <your_token>
4. **Выход (удаление токена):**

```bash
POST /api/auth/token/logout/
```
Authorization: Token <your_token>
5. **Смена пароля:**

```bash
POST /api/auth/users/set_password/
```
Authorization: Token <your_token>
Content-Type: application/json
```bash
{
    "new_password": "new_password",
    "password": "current_password"
}
```

---

## Эндпоинты API

- **Рецепты (Recipes)**

Cписок всех рецептов (доступно всем):
```bash
GET /api/recipes/
```

Cоздание рецепта (авторизованные пользователи):
```bash
POST /api/recipes/
```

Получение детальной информации о рецепте (доступно всем):
```bash
GET /api/recipes/{id}/
```

Обновление рецепта (автор):
```bash
PATCH /api/recipes/{id}/
```

Удаление рецепта (автор):
```bash
DELETE /api/recipes/{id}/
```

Получение короткой ссылки на рецепт (доступно всем):
```bash
GET /api/recipes/{id}/get-link/
```

- **Список покупок (Shopping_cart)**

Скачивание списка покупок (авторизованные пользователи):
```bash
GET /api/recipes/download_shopping_cart/
```

Добавление рецепта в список покупок (авторизованные пользователи):
```bash
POST /api/recipes/{id}/shopping_cart/
```

Удаление рецепта из списка покупок (авторизованные пользователи):
```bash
DELETE /api/recipes/{id}/shopping_cart/
```

- **Избранное (Favorite)**

Добавление рецепта в избранное (авторизованные пользователи):
```bash
POST /api/recipes/{id}/favorite/
```

Удаление рецепта из избранного (авторизованные пользователи):
```bash
DELETE /api/recipes/{id}/favorite/
```

- **Подписки (Subscriptions)**


Список подписок пользователя (авторизованные пользователи):
```bash
GET /api/users/subscriptions/
```

Подписка на пользователя (авторизованные пользователи):
```bash
POST /api/users/{id}/subscribe/
```

Отписка от пользователя (авторизованные пользователи):
```bash
DELETE /api/users/{id}/subscribe/
```

- **Параметры фильтрации рецептов**

Фильтрация по тегам:
```bash
?tags=breakfast,lunch
```

Фильтрация по рецептам конткретного автора:
```bash
?author=1
```

Только избранные рецепты:
```bash
?is_favorited=1
```

Рецепты в списке покупок:
```bash
?is_in_shopping_cart=1
```

- **Теги (Tags)**

Cписок тегов (доступно всем):
```bash
GET /api/tags/
```

Получение тега (доступно всем):
```bash
GET /api/tags/{id}/
```

- **Ингредиенты (Ingredients)**

Список ингредиентов (доступно всем):
```bash
GET /api/ingredients/
```

Получение ингредиента (доступно всем):
```bash
GET /api/ingredients/{id}/
```

Поиск по ингредиентам (частичное вхождение в начале названия):
```bash
?name=сахар
```

- **Пользователи (Users)**

Список пользователей (доступно всем):
```bash
GET /api/users/
```

Профиль пользователя (доступно всем):
```bash
GET /api/users/{id}/
```

Текущий пользователь (авторизованные пользователи):
```bash
GET /api/users/me/
```

Загрузка аватара пользователя (авторизованные пользователи):
```bash
PUT /api/users/me/avatar/
```

Удаление аватара пользователя (авторизованные пользователи):
```bash
DELETE /api/users/me/avatar/
```

## Пользовательские роли и права доступа

- **Аноним:** 

Только чтение (GET-запросы).

- **User (аутентифицированный)**: 

Чтение + создание рецептов + добавление рецептов в избранное и в список покупок;
Загрузка списка покупок; 
Редактирование/удаление **своих** объектов.

- **Admin:**

Полные права на управление всем контентом + управление пользователями

- **Superuser:**

Всегда имеет права Admin (даже при смене роли)

---

## Импорт данных из CSV или JSON

Проект поддерживает автоматический импорт данных из CSV-файлов и JSON-файлов.

Файлы должны находиться в: /foodgram/data/

Доступные файлы:
- ingredients.csv — csv-файл с ингредиентами
- ingredients.json — json-файл с ингредиентами

Формат CSV:
```bash
сахар,г
молоко,мл
```

Формат JSON:
```bash
[
    {"name": "сахар", "measurement_unit": "г"},
    {"name": "молоко", "measurement_unit": "мл"}
]
```

**Команда для импорта:**

```bash
python manage.py load_ingredients
```

---

## Запуск через Docker

1. **Создание образов:**

```bash
docker build -t foodgram_backend ./backend
```
2. **Запуск контейнеров:**

```bash
docker-compose up -d
```
3. **Применение миграций (в контейнере):**

```bash
docker exec -it foodgram_backend_1 python manage.py migrate
```
4. **Загрузка ингредиентов:**

```bash
docker exec -it foodgram_backend_1 python manage.py load_ingredients
```

---

## Админ-панель

Доступна по адресу: http://127.0.0.1:8000/admin/

---

## Тестирование
Для тестирования всех эндпоинтов удобно использовать Postman.
В репозитории есть коллекция запросов: postman_collection.

---

## Примечания
✅ Рецепты сортируются по дате публикации (от новых к старым)

✅ Пагинация: 6 рецептов на странице, параметр limit для изменения

✅ Ингредиенты в списке покупок автоматически суммируются

✅ Короткие ссылки генерируются автоматически при запросе

✅ Изображения передаются в формате Base64

🗑️ Каскадное удаление:
- Удаление пользователя → удаляются его рецепты, подписки, избранное, список покупок;
- Удаление рецепта - удаляются записи в избранном и списке покупок, связанные с эти рецептом, связи с ингредиентами;
- Удаление тега не влияет на удаление рецептов;
- Удаление ингредиентов не влияет на удаление рецептов.

---

## Автор
Орленко Марина
GitHub: @Lima82