import random
import string


def generate_short_code(length: int = 6) -> str:
    """Генерирует случайный код для короткой ссылки."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
