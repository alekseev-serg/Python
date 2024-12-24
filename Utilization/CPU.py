import os
import time
import threading
from multiprocessing import cpu_count

def busy_loop(duration):
    """Функция для нагружения процессора."""
    end_time = time.time() + duration
    while time.time() < end_time:
        pass  # Пустой цикл для нагрузки на процессор

def load_cpu(target_utilization=80, check_interval=1):
    """Функция для поддержания целевой загрузки процессора."""
    num_cores = cpu_count()
    utilization_per_core = target_utilization / 100.0

    while True:
        # Определяем текущую загрузку системы
        load_avg = os.getloadavg()[0]  # Средняя загрузка за последнюю минуту
        system_utilization = load_avg / num_cores

        # Если система перегружена, уменьшаем нагрузку
        if system_utilization > utilization_per_core:
            time.sleep(check_interval)
            continue

        # Вычисляем время активности и ожидания для достижения нужной загрузки
        active_time = check_interval * utilization_per_core
        idle_time = check_interval - active_time

        # Создаем потоки для нагрузки на процессор
        threads = []
        for _ in range(num_cores):
            thread = threading.Thread(target=busy_loop, args=(active_time,))
            threads.append(thread)
            thread.start()

        # Ждем завершения потоков
        for thread in threads:
            thread.join()

        # Период ожидания для достижения целевой загрузки
        time.sleep(idle_time)

if __name__ == "__main__":
    print("Запуск управления загрузкой процессора...")
    try:
        load_cpu(target_utilization=50)
    except KeyboardInterrupt:
        print("\nСкрипт завершен.")
