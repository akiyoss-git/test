import argparse  # Для работы с аргументами командной строки
import multiprocessing  # Для работы с процессами и каналами (pipe)
import os  # Для работы с ОС (очистка экрана)
import time  # Для работы с временем
from tabulate import tabulate  # Для вывода таблицы
from colorama import Fore, Style, init  # Для раскраски текста

# Инициализация цветного вывода
init()

# Функция для форматирования времени
def format_time(seconds):
    return time.strftime("%H:%M:%S", time.localtime(seconds))

# Функция, которую выполняет каждый дочерний процесс
def worker(pipe, idx, job, duration):
    # Передаем родительскому процессу статус "Выполняется" и время начала
    pipe.send((idx, f"{Fore.YELLOW}Выполняется{Style.RESET_ALL}", format_time(time.time())))
    
    # Эмулируем выполнение задачи
    time.sleep(duration)
    
    # Передаем родительскому процессу статус "Выполнено" и время окончания
    pipe.send((idx, f"{Fore.GREEN}Выполнено{Style.RESET_ALL}", format_time(time.time())))

    # Закрываем канал после завершения работы
    pipe.close()

# Основная функция родительского процесса
def parent_process(tasks, num_processes):
    # Списки для хранения статусов, времени начала и конца
    status = [f"{Fore.RED}Не выполняется{Style.RESET_ALL}"] * len(tasks)
    start_times = ["--:--:--"] * len(tasks)
    end_times = ["--:--:--"] * len(tasks)

    # Список для хранения процессов и каналов
    pipes = []
    processes = []

    # Создаем процессы и каналы (pipe)
    for idx, task in enumerate(tasks):
        parent_conn, child_conn = multiprocessing.Pipe()  # Создаем двусторонний канал
        p = multiprocessing.Process(target=worker, args=(child_conn, idx, task[0], task[1]))
        p.start()  # Запускаем процесс
        processes.append(p)
        pipes.append(parent_conn)  # Сохраняем канал для взаимодействия с процессом

    # Пока все задачи не завершены, обновляем экран
    while True:
        # Проверяем, завершены ли все процессы
        if all(s == f"{Fore.GREEN}Выполнено{Style.RESET_ALL}" for s in status):
            break
        
        # Очищаем экран
        os.system('cls' if os.name == 'nt' else 'clear')

        # Проверяем, есть ли новые сообщения от дочерних процессов
        for pipe in pipes:
            if pipe.poll():  # Проверяем, есть ли данные в канале
                idx, new_status, timestamp = pipe.recv()  # Получаем данные от дочернего процесса
                if new_status == f"{Fore.YELLOW}Выполняется{Style.RESET_ALL}":
                    start_times[idx] = timestamp  # Устанавливаем время начала
                elif new_status == f"{Fore.GREEN}Выполнено{Style.RESET_ALL}":
                    end_times[idx] = timestamp  # Устанавливаем время завершения
                status[idx] = new_status  # Обновляем статус

        # Формируем таблицу и выводим её в консоль
        table = [[tasks[i][0], status[i], start_times[i], end_times[i]] for i in range(len(tasks))]
        print(tabulate(table, headers=["Задача", "Статус", "Начало", "Конец"]))

        time.sleep(1)  # Пауза перед обновлением

    # Ожидаем завершения всех процессов
    for p in processes:
        p.join()

    # Финальный вывод таблицы
    os.system('cls' if os.name == 'nt' else 'clear')
    table = [[tasks[i][0], status[i], start_times[i], end_times[i]] for i in range(len(tasks))]
    print(tabulate(table, headers=["Задача", "Статус", "Начало", "Конец"]))

# Функция для чтения задач из файла
def read_tasks(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [(line.split(': ')[0], int(line.split(': ')[1])) for line in f]

# Главная функция программы
def main():
    parser = argparse.ArgumentParser(description="Параллельное выполнение задач с использованием каналов pipe.")
    parser.add_argument('-p', type=int, required=True, help="Количество параллельных процессов.")
    parser.add_argument('-f', type=str, required=True, help="Файл с задачами.")
    args = parser.parse_args()

    tasks = read_tasks(args.f)
    parent_process(tasks, args.p)

# Точка входа в программу
if __name__ == "__main__":
    main()
