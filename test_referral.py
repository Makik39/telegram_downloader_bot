import sqlite3
from database import Database
import config

print("🧪 ТЕСТИРОВАНИЕ РЕФЕРАЛЬНОЙ СИСТЕМЫ")
print("=" * 50)

# Создаем базу данных
db = Database()

# Тестовые ID (используйте свои реальные ID из Telegram)
test_referrer_id = 123456789  # ЗАМЕНИТЕ на свой ID
test_referred_id = 987654321   # ЗАМЕНИТЕ на ID друга

print(f"\n1️⃣ Добавляем пригласившего (ID: {test_referrer_id})...")
db.add_user(test_referrer_id, "test_referrer", "Тест Реферер", None)

print(f"\n2️⃣ Добавляем приглашенного с параметром referred_by={test_referrer_id}...")
db.add_user(test_referred_id, "test_referred", "Тест Реферал", test_referrer_id)

print(f"\n3️⃣ Проверяем количество рефералов у {test_referrer_id}:")
count = db.get_referral_count(test_referrer_id)
print(f"   Результат: {count}")

print(f"\n4️⃣ Проверяем детали рефералов:")
details = db.get_referral_details(test_referrer_id)
if details:
    for detail in details:
        print(f"   {detail}")
else:
    print("   ❌ Детали не найдены")

print("\n" + "=" * 50)
print("✅ Тест завершен")