"""
Перемножение матриц с использованием multiprocessing.Process и Queue.

Основа — функция element() из репозитория:
https://github.com/fa-python-network/3_Parallelism

Задания:
  TODO 1 — создать процесс для каждого элемента и собрать результаты через Queue
  TODO 2 — замерить время последовательного и параллельного вычисления

Запуск:
    python3 02_matrix_multiply.py
"""

import time
from multiprocessing import Process, Queue


def element(index, A, B):
    """Вычисляет один элемент произведения матриц A * B.

    Args:
        index: кортеж (i, j) — позиция элемента в результирующей матрице
        A: первая матрица (список списков)
        B: вторая матрица (список списков)

    Returns:
        Значение элемента C[i][j]
    """
    i, j = index
    res = 0
    N = len(A[0])
    for k in range(N):
        res += A[i][k] * B[k][j]
    return res


def element_to_queue(index, A, B, q):
    """Обёртка над element(), записывающая результат в Queue."""
    result = element(index, A, B)
    q.put((index, result))


# ──────────────────────────────────────────────
# Исходные матрицы (3x3)
# ──────────────────────────────────────────────
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
    """Последовательное перемножение матриц (для сравнения)."""
    rows = len(A)
    cols = len(B[0])
    result = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            result[i][j] = element((i, j), A, B)
    return result


def parallel_multiply(A, B):
    """Параллельное перемножение матриц: один процесс на каждый элемент."""
    rows = len(A)
    cols = len(B[0])
    result = [[0] * cols for _ in range(rows)]

    q = Queue()
    processes = []

    # TODO 1: Для каждого элемента (i, j) результирующей матрицы создайте
    # отдельный процесс, который вызовет element_to_queue(index, A, B, q).
    # Добавьте процесс в список processes и запустите его.
    
    # --- Ваш код здесь ---
    for i in range(rows):
        for j in range(cols):
            p = Process(target=element_to_queue, args=((i, j), A, B, q))
            processes.append(p)
            p.start()
    # --- Конец вашего кода ---

    for p in processes:
        p.join()

    while not q.empty():
        (i, j), value = q.get()
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

    # Последовательное вычисление
    t1 = time.time()
    result_seq = sequential_multiply(matrix_a, matrix_b)
    time_seq = time.time() - t1

    print("Результат (последовательно):")
    for row in result_seq:
        print(f"  {row}")
    print(f"Время: {time_seq:.6f} сек\n")

    # TODO 2: Замерьте время параллельного вычисления аналогично
    # последовательному. Выведите результат и время. Сравните.
    
    # --- Ваш код здесь ---
    t2 = time.time()
    result_par = parallel_multiply(matrix_a, matrix_b)
    time_par = time.time() - t2
    
    print("Результат (параллельно):")
    for row in result_par:
        print(f"  {row}")
    print(f"Время: {time_par:.6f} сек\n")
    
    # Проверка, что результаты совпадают
    if result_seq == result_par:
        print("✅ Результаты совпадают!")
    else:
        print("❌ Результаты различаются!")
    
    # Сравнение времени
    if time_par > 0:
        print(f"Ускорение: {time_seq / time_par:.2f}x")
    # --- Конец вашего кода ---