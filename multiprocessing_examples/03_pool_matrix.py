"""
Перемножение матриц с использованием multiprocessing.Pool.

Пул процессов позволяет эффективно распределить задачи между фиксированным
числом процессов, что снижает накладные расходы на создание процессов.
"""

import time
from multiprocessing import Pool
import itertools


def element(args):
    """Вычисляет один элемент произведения матриц A * B.
    
    Args:
        args: кортеж (i, j, A, B) — позиция элемента и матрицы
    
    Returns:
        (i, j, value) — индексы элемента и его значение
    """
    i, j, A, B = args
    res = 0
    N = len(A[0])  # количество столбцов A = количество строк B
    for k in range(N):
        res += A[i][k] * B[k][j]
    return (i, j, res)


# Исходные матрицы (3x3)
matrix_a = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]

matrix_b = [
    [9, 8, 7],
    [6, 5, 4],
    [3, 2, 1],
]


def sequential_multiply(A, B):
    """Последовательное перемножение матриц."""
    rows = len(A)
    cols = len(B[0])
    result = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            # Вызываем element и берём только значение (третий элемент кортежа)
            result[i][j] = element((i, j, A, B))[2]
    return result


def pool_multiply(A, B, num_processes):
    """Параллельное перемножение матриц с использованием пула процессов.
    
    Args:
        A, B: матрицы
        num_processes: количество процессов в пуле
    
    Returns:
        Результирующая матрица
    """
    rows = len(A)
    cols = len(B[0])
    result = [[0] * cols for _ in range(rows)]
    
    # TODO 3: Использовать Pool.map() для параллельного вычисления
    
    # Подготовка аргументов для всех элементов матрицы
    # Создаём список кортежей (i, j, A, B) для каждого элемента
    args = [(i, j, A, B) for i in range(rows) for j in range(cols)]
    
    # Создание пула процессов и выполнение задач
    # Контекстный менеджер with автоматически закрывает пул после использования
    with Pool(processes=num_processes) as pool:
        # pool.map применяет функцию element к каждому набору аргументов
        # и возвращает список результатов в том же порядке
        results = pool.map(element, args)
    
    # Заполнение результирующей матрицы
    for i, j, value in results:
        result[i][j] = value
    
    return result


if __name__ == '__main__':
    print("Матрица A:")
    for row in matrix_a:
        print(f"  {row}")
    print("Матрица B:")
    for row in matrix_b:
        print(f"  {row}")
    print()

    # Последовательное вычисление (для сравнения)
    t1 = time.time()
    result_seq = sequential_multiply(matrix_a, matrix_b)
    time_seq = time.time() - t1
    
    print("Результат (последовательно):")
    for row in result_seq:
        print(f"  {row}")
    print(f"Время: {time_seq:.6f} сек\n")
    
    # TODO 4: Запустить с разным числом процессов и сравнить время
    
    # Массив с разным количеством процессов для тестирования
    process_counts = [1, 2, 4]
    
    print("Параллельное вычисление с разным числом процессов:")
    print("-" * 60)
    print(f"{'Процессов':<10} {'Время (сек)':<15} {'Ускорение':<12} {'Результат'}")
    print("-" * 60)
    
    for num_proc in process_counts:
        # Замер времени для данного количества процессов
        t2 = time.time()
        result_pool = pool_multiply(matrix_a, matrix_b, num_proc)
        time_pool = time.time() - t2
        
        # Проверка правильности результата
        if result_seq == result_pool:
            check = "✅ Совпадает"
        else:
            check = "❌ Ошибка!"
        
        # Вычисляем ускорение относительно последовательной версии
        speedup = time_seq / time_pool if time_pool > 0 else 0
        
        # Выводим результаты в табличном виде
        print(f"{num_proc:<10} {time_pool:<15.6f} {speedup:<12.2f}x {check}")
    
