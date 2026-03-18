"""
Асинхронный TCP эхо-сервер на базе asyncio.

Основа — репозиторий: https://github.com/fa-python-network/4_asyncio_server
Обновлено для Python 3.8+ (asyncio.run, без deprecated loop параметра).

Задания:
  TODO 6 — реализовать тело handle_echo (чтение, логирование, отправка, закрытие)

Запуск:
    python3 02_echo_server.py

Для проверки используйте клиент из 03_echo_client.py (в другом терминале).

═══════════════════════════════════════════════════════════════════════
СПРАВКА: Оригинальный код сервера из репозитория 4_asyncio_server
═══════════════════════════════════════════════════════════════════════

Оригинальный сервер (Python 3.6 стиль с устаревшим API):

    import asyncio

    async def handle_echo(reader, writer):
        data = await reader.read(100)
        message = data.decode()
        writer.write(data)
        await writer.drain()
        writer.close()

    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_echo, 'localhost', 9095, loop=loop)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

Что изменилось в нашей версии (Python 3.8+):
  1. asyncio.run(main()) заменяет ручное создание event loop
  2. async with server: заменяет ручное закрытие сервера
  3. await writer.wait_closed() — корректное ожидание закрытия (Python 3.7+)
  4. Параметр loop= убран — он deprecated с Python 3.8 и удалён в 3.10
═══════════════════════════════════════════════════════════════════════
"""

import asyncio

HOST = '127.0.0.1'
PORT = 9095


async def handle_echo(reader, writer):
    """Обработчик подключения клиента.

    Эта корутина вызывается автоматически при каждом новом подключении.
    Аргументы reader и writer — это асинхронные потоки ввода-вывода.
    """

    # TODO 6: Реализуйте эхо-сервер. Выполните следующие шаги по порядку:
    #
    # 1. Прочитайте данные от клиента:
    #        data = await reader.read(1024)
    #
    # 2. Декодируйте байты в строку:
    #        message = data.decode()
    #
    # 3. Получите адрес клиента и выведите лог:
    #        addr = writer.get_extra_info('peername')
    #        print(f"Подключение от {addr}, сообщение: '{message}'")
    #
    # 4. Отправьте данные обратно клиенту (эхо):
    #        writer.write(data)
    #        await writer.drain()
    #
    # 5. Закройте соединение:
    #        writer.close()
    #        await writer.wait_closed()

    # --- Ваш код здесь ---
    pass
    # --- Конец вашего кода ---


async def main():
    """Запуск сервера."""
    server = await asyncio.start_server(handle_echo, HOST, PORT)

    addr = server.sockets[0].getsockname()
    print(f"Сервер запущен на {addr[0]}:{addr[1]}")
    print("Ожидание подключений... (Ctrl+C для остановки)\n")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
