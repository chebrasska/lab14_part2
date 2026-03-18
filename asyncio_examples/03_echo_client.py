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

HOST = '127.0.0.1'
PORT = 9095


async def tcp_echo_client(message, host, port):
    """Отправляет сообщение серверу и выводит ответ.

    Args:
        message: текст сообщения для отправки
        host: адрес сервера
        port: порт сервера
    """
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
    pass
    # --- Конец вашего кода ---


async def main():
    """Запуск одного клиента."""
    await tcp_echo_client("Hello, asyncio!", HOST, PORT)


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
    pass
    # --- Конец вашего кода ---


if __name__ == '__main__':
    try:
        print("--- Один клиент ---")
        asyncio.run(main())

        print("\n--- Несколько клиентов одновременно ---")
        asyncio.run(main_multiple())
    except ConnectionRefusedError:
        print("\nОшибка: не удалось подключиться к серверу.")
        print("Убедитесь, что сервер 02_echo_server.py запущен в другом терминале.")
