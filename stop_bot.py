import os
import signal
import subprocess
import time

print("🛑 ОСТАНОВКА БОТА")
print("=" * 50)

# Находим все процессы python
result = subprocess.run(['tasklist', '/fi', 'imagename eq python.exe'], 
                       capture_output=True, text=True)

# Завершаем процессы
os.system("taskkill /f /im python.exe 2>nul")
time.sleep(1)

print("✅ Бот остановлен!")