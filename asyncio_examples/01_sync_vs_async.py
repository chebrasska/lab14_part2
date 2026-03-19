"""
Сравнение синхронного и асинхронного выполнения.

Демонстрирует разницу во времени между последовательным вызовом
блокирующих операций и асинхронным запуском через asyncio.gather().

Задание:
  TODO 5 — дописать асинхронную версию main_async() с asyncio.gather()

Запуск:
    python3 01_sync_vs_async.py
"""

import time
import asyncio


# ──────────────────────────────────────────────
# Синхронные версии (имитация IO-операций через sleep)
# ──────────────────────────────────────────────

def fetch_data_sync(source, delay):
    """Имитация синхронного сетевого запроса."""
    print(f"  [sync] Запрос к '{source}'...")
    time.sleep(delay)
    print(f"  [sync] Ответ от '{source}' получен")
    return f"данные из {source}"


def main_sync():
    """Последовательный вызов трёх «запросов»."""
    results = []
    results.append(fetch_data_sync("API сервер", 2))
    results.append(fetch_data_sync("База данных", 3))
    results.append(fetch_data_sync("Файловое хранилище", 1))
    return results


# ──────────────────────────────────────────────
# Асинхронные версии
# ──────────────────────────────────────────────

async def fetch_data_async(source, delay):
    """Имитация асинхронного сетевого запроса."""
    print(f"  [async] Запрос к '{source}'...")
    await asyncio.sleep(delay)
    print(f"  [async] Ответ от '{source}' получен")
    return f"данные из {source}"


async def main_async():
    """Асинхронное выполнение трёх запросов.
    
    TODO 5: Допишите асинхронную версию с использованием asyncio.gather()
    """
    print("АСИНХРОННО:")
    
    # Создаём корутины
    tasks = [
        fetch_data_async("API сервер", 2),
        fetch_data_async("База данных", 3),
        fetch_data_async("Файловое хранилище", 1)
    ]
    
    # Запускаем все корутины одновременно и ждём их завершения
    results = await asyncio.gather(*tasks)
    
    print(f"Результаты: {results}")
    return results



if __name__ == '__main__':
    # Синхронная версия
    print("=" * 50)
    print("СИНХРОННЫЙ режим")
    print("=" * 50)
    t1 = time.perf_counter()
    sync_results = main_sync()
    time_sync = time.perf_counter() - t1
    print(f"\nРезультаты: {sync_results}")
    print(f"Время: {time_sync:.2f} сек\n")

    # Асинхронная версия
    print("=" * 50)
    print("АСИНХРОННЫЙ режим")
    print("=" * 50)
    t2 = time.perf_counter()
    async_results = asyncio.run(main_async())
    time_async = time.perf_counter() - t2

    if async_results is None:
        print("\n[!] TODO 5 ещё не выполнен — main_async() вернула None.")
        print("    Допишите код и запустите снова.\n")
    else:
        print(f"\nРезультаты: {list(async_results)}")
        print(f"Время: {time_async:.2f} сек\n")

        # Сравнение
        print("=" * 50)
        print(f"Синхронно:  {time_sync:.2f} сек")
        print(f"Асинхронно: {time_async:.2f} сек")
        print(f"Ускорение:  {time_sync / time_async:.1f}x")
