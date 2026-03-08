import sqlite3
import os

print("🧹 ОЧИСТКА БАЗЫ ДАННЫХ")
print("=" * 50)

# Проверяем, существует ли база
if not os.path.exists('bot_database.db'):
    print("❌ Файл базы данных не найден!")
    exit()

# Подключаемся к базе
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Получаем список всех таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(f"📊 Найдено таблиц: {len(tables)}")

# Очищаем каждую таблицу
for table in tables:
    table_name = table[0]
    print(f"🧹 Очищаем таблицу: {table_name}")
    
    # Удаляем все записи из таблицы
    cursor.execute(f"DELETE FROM {table_name}")
    
    # Сбрасываем счетчик автоинкремента (чтобы ID начинались с 1)
    if table_name != 'users':  # Для users ID не автоинкремент
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
    
    print(f"   ✅ Удалено {cursor.rowcount} записей")

# Сохраняем изменения
conn.commit()
conn.close()

print("\n" + "=" * 50)
print("✅ База данных очищена!")
print("Теперь можно запустить бота: python bot.py")