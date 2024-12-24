import os
import time
from multiprocessing import cpu_count

def get_cpu_usage():
    """Функция для получения средней загрузки процессора."""
    load_avg = os.getloadavg()[0]  # Средняя загрузка за последнюю минуту
    num_cores = cpu_count()
    return (load_avg / num_cores) * 100  # Процент использования процессора

def maintain_active_time(target_utilization=80, check_interval=1):
    """Поддерживает активную работу процессора на уровне 80%, оставляя 20% idle time."""
    while True:
        current_usage = get_cpu_usage()
        # print(f"Текущая загрузка процессора: {current_usage:.2f}%")

        if current_usage < target_utilization:
            # Если загрузка процессора ниже целевого уровня, активируем процессор
            active_time = check_interval * (target_utilization / 100)
            idle_time = check_interval - active_time

            # Выполняем активную нагрузку
            end_time = time.time() + active_time
            while time.time() < end_time:
                pass  # Интенсивная нагрузка на процессор

            # Период ожидания для оставшихся idle времени
            time.sleep(idle_time)
        else:
            # Если загрузка процессора уже на целевом уровне или выше, минимизируем idle time
            # print("Процессор работает, уменьшаем idle time...")
            time.sleep(check_interval)

if __name__ == "__main__":
    print("Запуск управления загрузкой процессора...")
    try:
        maintain_active_time(target_utilization=80, check_interval=1)
    except KeyboardInterrupt:
        print("\nСкрипт завершен.")
