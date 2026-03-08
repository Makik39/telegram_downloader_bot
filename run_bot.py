import os
import sys
import subprocess
import time

print("🚀 ЗАПУСК БОТА")
print("=" * 50)

# Завершаем все процессы python, связанные с ботом
print("🛑 Завершаем старые процессы...")
os.system("taskkill /f /im python.exe 2>nul")
time.sleep(2)

# Запускаем бота
print("✅ Запускаем бота...")
print("=" * 50)

# Запускаем bot.py в новом окне
subprocess.run([sys.executable, "bot.py"])