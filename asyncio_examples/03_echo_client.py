"""
Асинхронный TCP эхо-клиент на базе asyncio.

Основа — репозиторий: https://github.com/fa-python-network/4_asyncio_server
Обновлено для Python 3.8+ (asyncio.run, без deprecated loop параметра).

Задания:
  TODO 7 — дописать отправку сообщения и получение ответа
  TODO 8 — запустить несколько клиентов одновременно через asyncio.gather()

Запуск (сервер 02_echo_server.py должен быть запущен в другом терминале):
    python3 03_echo_client.py

═══════════════════════════════════════════════════════════════════════
СПРАВКА: Оригинальный код клиента из репозитория 4_asyncio_server
═══════════════════════════════════════════════════════════════════════

Оригинальный клиент (Python 3.6 стиль):

    import asyncio

    async def tcp_echo_client(host, port):
        reader, writer = await asyncio.open_connection(host, port)
        message = 'Hello, world'

        writer.write(message.encode())
        await writer.drain()

        data = await reader.read(100)
        writer.close()

    loop = asyncio.get_event_loop()
    task = loop.create_task(tcp_echo_client('localhost', 9095))
    loop.run_until_complete(task)

Что изменилось в нашей версии (Python 3.8+):
  1. asyncio.run(main()) заменяет ручное создание event loop и task
  2. await writer.wait_closed() — корректное ожидание закрытия
  3. Добавлен asyncio.gather() для запуска нескольких клиентов (TODO 8)
  4. Добавлена обработка ConnectionRefusedError
═══════════════════════════════════════════════════════════════════════
"""

import asyncio
import time

HOST = '127.0.0.1'
PORT = 9095


async def tcp_echo_client(message, host, port):
    """Отправляет сообщение серверу и выводит ответ.

    Args:
        message: текст сообщения для отправки
        host: адрес сервера
        port: порт сервера
    """
    # Подключаемся к серверу
    reader, writer = await asyncio.open_connection(host, port)

    # TODO 7: Отправьте сообщение серверу и получите ответ.
    #
    # 1. Закодируйте и отправьте:
    #        writer.write(message.encode())
    #        await writer.drain()
    #
    # 2. Прочитайте ответ:
    #        data = await reader.read(1024)
    #
    # 3. Выведите результат:
    #        print(f"Отправлено: '{message}' -> Получено: '{data.decode()}'")
    #
    # 4. Закройте соединение:
    #        writer.close()
    #        await writer.wait_closed()

    # --- Ваш код здесь ---
    
    # Получаем информацию о клиенте (для отладки)
    client_info = writer.get_extra_info('peername')
    
    print(f"[Клиент {client_info}] Отправка: '{message}'")
    
    # 1. Отправляем сообщение (кодируем строку в байты)
    writer.write(message.encode())
    await writer.drain()  # гарантирует, что все данные отправлены
    
    # 2. Получаем ответ от сервера
    data = await reader.read(1024)
    response = data.decode()
    
    # 3. Выводим результат
    print(f"[Клиент {client_info}] Отправлено: '{message}' -> Получено: '{response}'")
    
    # Проверяем, что сервер вернул то же сообщение (эхо)
    if response == message:
        print(f"[Клиент {client_info}] ✓ Эхо-проверка пройдена")
    else:
        print(f"[Клиент {client_info}] ✗ Ошибка: получено '{response}', ожидалось '{message}'")
    
    # 4. Закрываем соединение
    writer.close()
    await writer.wait_closed()
    
    # --- Конец вашего кода ---


async def main():
    """Запуск одного клиента."""
    print("=" * 60)
    print("ЗАПУСК ОДНОГО КЛИЕНТА")
    print("=" * 60)
    
    start_time = time.time()
    await tcp_echo_client("Hello, asyncio!", HOST, PORT)
    elapsed = time.time() - start_time
    
    print(f"Время выполнения: {elapsed:.3f} сек")
    print("=" * 60)


async def main_multiple():
    """Запуск нескольких клиентов одновременно."""
    
    # TODO 8: Запустите 5 клиентов одновременно через asyncio.gather().
    # Каждый клиент отправляет своё сообщение. Проанализируйте порядок
    # вывода — будет ли он совпадать с порядком создания?
    #
    # Подсказка:
    #   messages = [f"Сообщение {i}" for i in range(1, 6)]
    #   await asyncio.gather(
    #       *(tcp_echo_client(msg, HOST, PORT) for msg in messages)
    #   )

    # --- Ваш код здесь ---
    
    print("=" * 60)
    print("ЗАПУСК НЕСКОЛЬКИХ КЛИЕНТОВ ПАРАЛЛЕЛЬНО")
    print("=" * 60)
    
    # Создаём список сообщений для разных клиентов
    messages = [
        "Сообщение 1", 
        "Сообщение 2", 
        "Сообщение 3", 
        "Сообщение 4", 
        "Сообщение 5"
    ]
    
    # ========== ВАРИАНТ 1: Создание списка задач ==========
    # Создаём список корутин для каждого сообщения
    tasks = [tcp_echo_client(msg, HOST, PORT) for msg in messages]
    
    # Запускаем все задачи ПАРАЛЛЕЛЬНО
    # asyncio.gather() запускает все корутины одновременно
    # и ждёт их завершения
    start_time = time.time()
    await asyncio.gather(*tasks)  # * распаковывает список
    elapsed = time.time() - start_time
    
    # ========== ВАРИАНТ 2: Более компактная запись ==========
    # Можно записать ещё короче:
    # await asyncio.gather(*(tcp_echo_client(msg, HOST, PORT) for msg in messages))
    
    # ========== ВАРИАНТ 3: С разными сообщениями ==========
    # Ещё вариант с разными типами сообщений:
    """
    await asyncio.gather(
        tcp_echo_client("Привет от клиента 1", HOST, PORT),
        tcp_echo_client("Hello from client 2", HOST, PORT),
        tcp_echo_client("Bonjour client 3", HOST, PORT),
        tcp_echo_client("Hola cliente 4", HOST, PORT),
        tcp_echo_client("Ciao cliente 5", HOST, PORT)
    )
    """
    
    print("=" * 60)
    print(f"ВСЕ КЛИЕНТЫ ЗАВЕРШИЛИ РАБОТУ")
    print(f"Общее время выполнения: {elapsed:.3f} сек")
    print(f"Среднее время на клиента: {elapsed/5:.3f} сек")
    print("=" * 60)
    
    # --- Конец вашего кода ---


# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ДЕМОНСТРАЦИИ ==========

async def main_with_different_messages():
    """Запуск клиентов с разными сообщениями."""
    
    messages = [
        "Короткое",
        "Более длинное сообщение для проверки",
        "12345",
        "Специальные символы: !@#$%^&*()",
        "Последнее сообщение"
    ]
    
    print("=" * 60)
    print("ЗАПУСК КЛИЕНТОВ С РАЗНЫМИ СООБЩЕНИЯМИ")
    print("=" * 60)
    
    # Запускаем все клиенты параллельно
    await asyncio.gather(*(tcp_echo_client(msg, HOST, PORT) for msg in messages))
    
    print("=" * 60)
    print("ВСЕ КЛИЕНТЫ ЗАВЕРШИЛИ РАБОТУ")
    print("=" * 60)


async def main_with_delays():
    """Демонстрация того, что клиенты действительно работают параллельно."""
    
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ ПАРАЛЛЕЛЬНОЙ РАБОТЫ")
    print("=" * 60)
    print("Клиенты с разными задержками (имитация)")
    
    # Функция-обёртка для имитации разной длительности
    async def client_with_delay(name, delay):
        print(f"[{time.time():.1f}] Клиент {name}: начинаю работу (задержка {delay} сек)")
        await asyncio.sleep(delay)  # имитация какой-то работы
        await tcp_echo_client(f"Сообщение от клиента {name}", HOST, PORT)
        print(f"[{time.time():.1f}] Клиент {name}: завершил работу")
    
    # Запускаем клиентов с разными задержками
    await asyncio.gather(
        client_with_delay("A", 0.5),
        client_with_delay("B", 0.1),
        client_with_delay("C", 0.3),
        client_with_delay("D", 0.0),
        client_with_delay("E", 0.2)
    )
    
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)


if __name__ == '__main__':
    try:
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║         АСИНХРОННЫЙ ЭХО-КЛИЕНТ              ║")
        print("╚" + "═" * 58 + "╝")
        print()
        
        # Запуск одного клиента
        asyncio.run(main())
        
        print("\n" + "─" * 60 + "\n")
        
        # Запуск нескольких клиентов
        asyncio.run(main_multiple())
        
        print("\n" + "─" * 60 + "\n")
        
        # Дополнительная демонстрация (можно закомментировать)
        # asyncio.run(main_with_different_messages())
        # asyncio.run(main_with_delays())
        
    except ConnectionRefusedError:
        print("\n" + "!" * 60)
        print("ОШИБКА: не удалось подключиться к серверу!")
        print("!" * 60)
        print("\nУбедитесь, что сервер 02_echo_server.py запущен в другом терминале:")
        print("  cd ~/lab14_part2")
        print("  python3 asyncio_examples/02_echo_server.py")
        print()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")