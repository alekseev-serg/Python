import os
import time


def get_cpu_usage():
    # Число ядер
    print(os.cpu_count())
    # Получаем загрузку CPU в процентах
    return float(os.popen("grep 'cpu ' /proc/stat").readline().split()[1]) / (os.cpu_count() * 100000)


def cpu_load(target_load=60, tolerance=5):
    while True:
        current_load = get_cpu_usage()
        print(f"Текущая загрузка CPU: {current_load:.2f}%")

        if current_load < target_load - tolerance:
            # Увеличиваем нагрузку
            print("Увеличиваем нагрузку на CPU")
            start_time = time.time()
            while time.time() - start_time < 0.1:  # Нагрузка в течение 0.1 секунды
                pass  # Нагрузка на CPU
        elif current_load > target_load + tolerance:
            # Уменьшаем нагрузку
            print("Уменьшаем нагрузку на CPU")
            time.sleep(0.5)  # Уменьшаем нагрузку, просто ждем

        time.sleep(1)  # Пауза перед следующей проверкой


if __name__ == "__main__":
    cpu_load()
