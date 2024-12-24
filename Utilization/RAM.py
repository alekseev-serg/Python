import os
import time

def get_memory_info():
    """
    Получает информацию о памяти из /proc/meminfo.
    Возвращает общий объем и объем используемой памяти в байтах.
    """
    with open("/proc/meminfo", "r") as f:
        meminfo = f.readlines()

    meminfo_dict = {}
    for line in meminfo:
        key, value = line.split(":")
        meminfo_dict[key.strip()] = int(value.split()[0]) * 1024  # Преобразуем к байтам

    total_memory = meminfo_dict["MemTotal"]
    available_memory = meminfo_dict["MemAvailable"]
    used_memory = total_memory - available_memory

    return total_memory, used_memory

def maintain_memory_load(target_usage=60, check_interval=1):
    """
    Поддерживает загрузку оперативной памяти на заданном уровне.

    :param target_usage: Целевой процент использования оперативной памяти (например, 60).
    :param check_interval: Интервал проверки текущего состояния памяти в секундах.
    """
    allocated_memory = []  # Список для хранения выделенных блоков памяти

    total_memory, _ = get_memory_info()
    target_memory = total_memory * (target_usage / 100)  # Целевой объем используемой памяти

    print(f"Общий объем оперативной памяти: {total_memory / (1024**3):.2f} ГБ")
    print(f"Целевая загрузка памяти: {target_usage}% (~{target_memory / (1024**3):.2f} ГБ)\n")

    try:
        while True:
            _, used_memory = get_memory_info()
            current_allocation = sum(len(block) for block in allocated_memory)  # Сколько памяти выделено скриптом

            total_used = used_memory + current_allocation  # Общая используемая память

            if total_used < target_memory:
                # Если текущая загрузка меньше целевой, выделяем недостающую память
                to_allocate = int(target_memory - total_used)
                print(f"Добавляем {to_allocate / (1024**2):.2f} МБ памяти...")
                allocated_memory.append(bytearray(to_allocate))  # Выделяем память

            elif total_used > target_memory:
                # Если загрузка выше целевой, освобождаем память
                print(f"Освобождаем часть памяти...")
                while total_used > target_memory and allocated_memory:
                    freed_block = allocated_memory.pop()  # Удаляем последний выделенный блок памяти
                    total_used -= len(freed_block)

            # Печать текущей информации
            print(f"Используемая память: {total_used / total_memory * 100:.2f}%\n")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\nСкрипт завершен. Освобождаем всю выделенную память...")
        allocated_memory.clear()

if __name__ == "__main__":
    maintain_memory_load(target_usage=60)
