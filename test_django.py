#!/usr/bin/env python
"""
Скрипт для проверки, может ли Django загрузиться без ошибок.
Запускать из директории проекта с активированным venv.
"""
import os
import sys
import django
from pathlib import Path

# Добавить путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Установить переменные окружения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

print("=" * 60)
print("Тест загрузки Django")
print("=" * 60)

try:
    print("\n1. Импорт Django...")
    django.setup()
    print("   ✓ Django успешно импортирован")
except Exception as e:
    print(f"   ✗ Ошибка импорта Django: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Проверка подключения к базе данных...")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print(f"   ✓ Подключение к БД успешно: {result}")
except Exception as e:
    print(f"   ✗ Ошибка подключения к БД: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Проверка моделей...")
    from screener.models import Symbol, ScreenerSnapshot
    symbol_count = Symbol.objects.count()
    snapshot_count = ScreenerSnapshot.objects.count()
    print(f"   ✓ Модели работают: {symbol_count} символов, {snapshot_count} снимков")
except Exception as e:
    print(f"   ✗ Ошибка работы с моделями: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n4. Проверка URL конфигурации...")
    from django.urls import get_resolver
    resolver = get_resolver()
    print(f"   ✓ URL конфигурация загружена: {len(resolver.url_patterns)} паттернов")
except Exception as e:
    print(f"   ✗ Ошибка URL конфигурации: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Все проверки пройдены успешно!")
print("=" * 60)

