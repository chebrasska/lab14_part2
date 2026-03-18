# Лабораторная работа 14 (часть 2): Многопроцессность и асинхронное программирование

## Цель работы

Изучить механизмы многопроцессного (`multiprocessing`) и асинхронного (`asyncio`) программирования в Python. Понять, когда и зачем применяется каждый из подходов, научиться использовать их на практике.

## Теоретические сведения

### Классификация задач

Все алгоритмы можно условно разделить на два типа в зависимости от того, что ограничивает скорость их выполнения:

- **CPU-bound** (ограничены процессором) — вычислительные задачи, которые постоянно нагружают ЦП: математические расчёты, обработка данных, перемножение матриц.
- **IO-bound** (ограничены вводом-выводом) — задачи, которые большую часть времени ожидают внешних событий: сетевые запросы, чтение файлов, ввод пользователя.

От типа задачи зависит выбор инструмента для ускорения:

```mermaid
flowchart TD
    Task["Задача"] --> Question{"Тип задачи?"}
    Question -->|"CPU-bound (вычисления)"| MP["multiprocessing"]
    Question -->|"IO-bound (сеть, файлы)"| AS["asyncio"]
    MP --> Parallel["Параллельное выполнение\nна нескольких ядрах CPU"]
    AS --> EventLoop["Кооперативное переключение\nзадач в event loop"]
```

### Многопроцессность (multiprocessing)

Модуль `multiprocessing` создаёт настоящие процессы операционной системы. Каждый процесс получает собственную копию интерпретатора Python и всех данных. Это единственный способ в Python обойти GIL и задействовать несколько ядер процессора для CPU-bound задач.

```mermaid
flowchart LR
    Main["Главный процесс\n(main)"] -->|"fork"| P1["Процесс 1\nPython + копия данных"]
    Main -->|"fork"| P2["Процесс 2\nPython + копия данных"]
    Main -->|"fork"| P3["Процесс 3\nPython + копия данных"]
    P1 -->|"результат"| Main
    P2 -->|"результат"| Main
    P3 -->|"результат"| Main
```

**Пример создания процесса** (файл `01_basic_process.py`):

```python
from multiprocessing import Process, current_process
import os, time

def worker(task_name, duration):
    """Функция, выполняемая в отдельном процессе."""
    print(f"[{current_process().name}] Начало задачи '{task_name}' "
          f"(PID={os.getpid()}, родитель={os.getppid()})")
    time.sleep(duration)
    print(f"[{current_process().name}] Задача '{task_name}' завершена")

if __name__ == '__main__':
    print(f"Главный процесс: PID={os.getpid()}")
    tasks = [("Загрузка", 2), ("Обработка", 3), ("Сохранение", 1)]

    processes = []
    for name, dur in tasks:
        p = Process(target=worker, args=(name, dur))  # создаём процесс
        processes.append(p)

    for p in processes:
        p.start()   # запускаем все процессы

    for p in processes:
        p.join()     # ждём завершения всех
```

- `Process(target=..., args=...)` — создаёт новый процесс. Функция `worker` будет выполнена в отдельном процессе ОС.
- `p.start()` — запускает процесс (ОС создаёт новый PID).
- `p.join()` — главный процесс ожидает завершения дочернего.
- `os.getpid()` — PID текущего процесса, `os.getppid()` — PID родительского.
- Три задачи с `time.sleep(2, 3, 1)` последовательно заняли бы 6 сек, но параллельно — ~3 сек (время самой длинной).

**Передача данных между процессами** (файл `02_matrix_multiply.py`):

Каждый процесс работает с копией данных. Обычные переменные **не передают** результат обратно в главный процесс. Для этого используется `Queue`:

```python
from multiprocessing import Process, Queue

def element_to_queue(index, A, B, q):
    i, j = index
    res = sum(A[i][k] * B[k][j] for k in range(len(A[0])))
    q.put((index, res))  # отправляем результат в очередь

q = Queue()
p = Process(target=element_to_queue, args=((0, 0), A, B, q))
p.start()
p.join()
(i, j), value = q.get()  # получаем результат из очереди
```

**Межпроцессное взаимодействие (IPC)**

Так как каждый процесс изолирован в своём адресном пространстве, для обмена данными между ними используются специальные механизмы IPC (Inter-Process Communication):

| Механизм | Описание | Когда использовать |
|---|---|---|
| `Queue` | Потокобезопасная очередь FIFO | Много процессов → один сборщик |
| `Pipe` | Двусторонний канал между двумя процессами | Прямая связь «родитель ↔ потомок» |
| `Pool.map/starmap` | Возвращаемые значения через пул | Распределение однотипных задач |

`Pipe()` создаёт пару связанных объектов-соединений. Данные, отправленные в один конец, появляются в другом:

```python
from multiprocessing import Process, Pipe

def child(conn):
    conn.send("Привет от дочернего процесса!")  # отправляем
    conn.close()

parent_conn, child_conn = Pipe()       # два конца канала
p = Process(target=child, args=(child_conn,))
p.start()
msg = parent_conn.recv()               # получаем
print(msg)  # "Привет от дочернего процесса!"
p.join()
```

- `Pipe()` — возвращает два конца: `(conn1, conn2)`. Что отправлено через `conn1.send()`, получается через `conn2.recv()`, и наоборот.
- `Queue` удобнее, когда много процессов пишут в одну очередь. `Pipe` быстрее для связи двух процессов.

**Пул процессов** (файл `03_pool_matrix.py`):

Создавать отдельный процесс на каждую маленькую задачу неэффективно. `Pool` создаёт фиксированное число процессов и распределяет задачи между ними:

```python
from multiprocessing import Pool

def element(i, j, A, B):
    res = sum(A[i][k] * B[k][j] for k in range(len(A[0])))
    return (i, j, res)

args = [(i, j, A, B) for i in range(rows) for j in range(cols)]
with Pool(processes=4) as pool:
    results = pool.starmap(element, args)  # 4 процесса делят все задачи
```

### Асинхронное программирование (asyncio)

Модуль `asyncio` реализует кооперативную многозадачность: программист сам определяет точки переключения между задачами с помощью `await`. Все корутины выполняются в одном потоке и одном процессоре, но за счёт переключений во время ожидания IO достигается значительное ускорение IO-bound задач.

```mermaid
sequenceDiagram
    participant EL as Event Loop
    participant C1 as Корутина 1
    participant C2 as Корутина 2
    EL->>C1: запуск
    C1->>EL: await — ожидание IO
    EL->>C2: запуск
    C2->>EL: await — ожидание IO
    EL->>C1: IO завершён, возобновление
    C1->>EL: завершение
    EL->>C2: IO завершён, возобновление
    C2->>EL: завершение
```

**Пример: синхронный vs асинхронный подход** (файл `01_sync_vs_async.py`):

Синхронно — три запроса выполняются последовательно (2 + 3 + 1 = 6 сек):

```python
import time

def fetch_data_sync(source, delay):
    print(f"  Запрос к '{source}'...")
    time.sleep(delay)        # блокирует весь поток на delay секунд
    return f"данные из {source}"

results = []
results.append(fetch_data_sync("API сервер", 2))
results.append(fetch_data_sync("База данных", 3))
results.append(fetch_data_sync("Файловое хранилище", 1))
# Общее время: ~6 сек
```

Асинхронно — три запроса выполняются «одновременно» (max(2, 3, 1) = 3 сек):

```python
import asyncio

async def fetch_data_async(source, delay):
    print(f"  Запрос к '{source}'...")
    await asyncio.sleep(delay)  # отпускает управление event loop-у
    return f"данные из {source}"

async def main_async():
    results = await asyncio.gather(
        fetch_data_async("API сервер", 2),
        fetch_data_async("База данных", 3),
        fetch_data_async("Файловое хранилище", 1),
    )
    return results

asyncio.run(main_async())
# Общее время: ~3 сек
```

- `async def` — определяет корутину (асинхронную функцию).
- `await asyncio.sleep(delay)` — приостанавливает текущую корутину и передаёт управление event loop, который может выполнить другие корутины. В отличие от `time.sleep()`, не блокирует весь поток.
- `asyncio.gather(...)` — запускает несколько корутин параллельно и ждёт завершения всех.
- `asyncio.run(main())` — создаёт event loop и запускает корутину (Python 3.7+).

**Асинхронный TCP-сервер** (файл `02_echo_server.py`):

```python
import asyncio

async def handle_echo(reader, writer):
    data = await reader.read(1024)       # неблокирующее чтение
    addr = writer.get_extra_info('peername')
    print(f"Подключение от {addr}: '{data.decode()}'")
    writer.write(data)                    # отправка обратно
    await writer.drain()                  # ожидание отправки
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 9095)
    async with server:
        await server.serve_forever()

asyncio.run(main())
```

- `asyncio.start_server(callback, host, port)` — создаёт TCP-сервер. При каждом подключении вызывается корутина `handle_echo`.
- `reader` / `writer` — асинхронные потоки для чтения и записи данных.
- Сервер обслуживает много клиентов в одном потоке — переключение происходит в точках `await`.

### Сравнительная таблица

| Характеристика | multiprocessing | asyncio |
|---|---|---|
| Тип задач | CPU-bound | IO-bound |
| Механизм | Отдельные процессы ОС | Корутины в event loop |
| Многозадачность | Вытесняющая | Кооперативная |
| Использование ядер CPU | Да (несколько) | Нет (одно) |
| Масштабируемость | Низкая (единицы–десятки) | Высокая (тысячи) |
| Обмен данными | Queue, Pipe, Pool | Общая память (один поток) |
| Блокирующие операции | Стандартные | Только асинхронные |

---

## Подготовка

### 1. Форк репозитория (на GitHub)

1. Откройте репозиторий преподавателя: [github.com/Mohanad0101/lab14_part2](https://github.com/Mohanad0101/lab14_part2)
2. Нажмите кнопку **"Fork"** в правом верхнем углу.
3. GitHub создаст копию репозитория в вашем аккаунте: `https://github.com/<ВАШ_ЛОГИН>/lab14_part2`

### 2. Клонирование вашего форка

```bash
cd ~
rm -rf lab14_part2
git clone https://github.com/<ВАШ_ЛОГИН>/lab14_part2.git lab14_part2
cd lab14_part2
```

> Замените `<ВАШ_ЛОГИН>` на ваш логин GitHub. Команда `rm -rf lab14_part2` удаляет старую папку, если она существует.

### 3. Проверка версии Python

```bash
python3 --version
```

Требуется Python 3.8 или выше.

### 4. Структура репозитория

```
lab14_part2/
├── README.md
├── RESULTS.md                         # Шаблон для результатов (заполнить)
├── multiprocessing_examples/
│   ├── 01_basic_process.py            # Справочный пример (готовый)
│   ├── 02_matrix_multiply.py         # Перемножение матриц — TODO
│   ├── 03_pool_matrix.py             # Пул процессов — TODO
│   ├── 04_mp_echo_server.py          # Многопроцессный сервер — TODO
│   └── 05_mp_echo_client.py          # Клиент для сервера (готовый)
└── asyncio_examples/
    ├── 01_sync_vs_async.py            # Сравнение sync/async — TODO
    ├── 02_echo_server.py              # Эхо-сервер — TODO
    └── 03_echo_client.py              # Эхо-клиент — TODO
```

### 5. Редактирование кода (Sublime Text)

Для редактирования файлов используйте **Sublime Text**. Откройте файл командой `subl`:

```bash
subl multiprocessing_examples/02_matrix_multiply.py
```

Или откройте весь проект сразу:

```bash
subl ~/lab14_part2
```

> Если команда `subl` не найдена, используйте `nano` или `vim`:
> ```bash
> nano multiprocessing_examples/02_matrix_multiply.py
> ```

**Совет:** в Sublime Text нажмите `Ctrl+G`, чтобы перейти к нужной строке, или `Ctrl+F` и введите `TODO`, чтобы найти все места для заполнения.

### 6. Как работать с файлами

В файлах с заданиями вы найдёте:

**Справка (СПРАВКА)** — в файлах, основанных на курсовых репозиториях ([3_Parallelism](https://github.com/fa-python-network/3_Parallelism), [4_asyncio_server](https://github.com/fa-python-network/4_asyncio_server), [2_threaded_server](https://github.com/fa-python-network/2_threaded_server)), в начале docstring приведён оригинальный код из этих репозиториев. Изучите его, чтобы понять, как работает исходный пример и что изменилось в нашей версии.

**TODO** — помеченные места вида:

```python
# TODO 1: Описание задания
# Подсказка: ...
```

Вам нужно дописать код в этих местах. Не удаляйте комментарии — они помогут преподавателю проверить работу.

### 7. Рабочий цикл: редактирование → запуск → проверка

1. Откройте файл в Sublime Text:

```bash
subl multiprocessing_examples/02_matrix_multiply.py
```

2. Найдите `TODO` (`Ctrl+F` → `TODO`), допишите код, сохраните (`Ctrl+S`).

3. Переключитесь в терминал и запустите:

```bash
python3 multiprocessing_examples/02_matrix_multiply.py
```

4. Если есть ошибка — вернитесь в Sublime Text, исправьте, сохраните, запустите снова.

---

## Часть A: Многопроцессность (multiprocessing)

### Задание A0: Знакомство с процессами (справочный пример)

Файл: `multiprocessing_examples/01_basic_process.py`

Запустите и изучите пример:

```bash
cd ~/lab14_part2
python3 multiprocessing_examples/01_basic_process.py
```

Обратите внимание на:
- Как создаётся и запускается процесс.
- Что выводят `os.getpid()` и `os.getppid()`.
- Как `join()` заставляет главный процесс ждать дочерний.

### Задание A1: Перемножение матриц в нескольких процессах

Файл: `multiprocessing_examples/02_matrix_multiply.py`

Этот файл содержит функцию вычисления одного элемента произведения матриц (из репозитория [3_Parallelism](https://github.com/fa-python-network/3_Parallelism)). Ваша задача — распараллелить вычисление всех элементов по процессам.

**Что нужно сделать:**
1. **TODO 1**: Создать процесс для каждого элемента результирующей матрицы и передать результат через `Queue`.
2. **TODO 2**: Замерить время последовательного и параллельного вычисления, вывести результат.

```bash
subl multiprocessing_examples/02_matrix_multiply.py
python3 multiprocessing_examples/02_matrix_multiply.py
```

### Задание A2: Пул процессов

Файл: `multiprocessing_examples/03_pool_matrix.py`

Используйте `Pool` для более эффективного распределения задач между фиксированным числом процессов.

**Что нужно сделать:**
1. **TODO 3**: Использовать `Pool.starmap()` для параллельного вычисления элементов матрицы.
2. **TODO 4**: Запустить программу с разным числом процессов в пуле (1, 2, 4) и сравнить время.

```bash
subl multiprocessing_examples/03_pool_matrix.py
python3 multiprocessing_examples/03_pool_matrix.py
```

---

## Часть B: Асинхронное программирование (asyncio)

### Задание B1: Синхронный vs асинхронный подход

Файл: `asyncio_examples/01_sync_vs_async.py`

Сравните время выполнения одинаковой задачи в синхронном и асинхронном режимах.

**Что нужно сделать:**
1. **TODO 5**: Допишите асинхронную версию функции `main_async()` с использованием `asyncio.gather()`.

```bash
subl asyncio_examples/01_sync_vs_async.py
python3 asyncio_examples/01_sync_vs_async.py
```

### Задание B2: Асинхронный эхо-сервер

Файл: `asyncio_examples/02_echo_server.py`

Реализуйте асинхронный TCP эхо-сервер на базе `asyncio` (по мотивам [4_asyncio_server](https://github.com/fa-python-network/4_asyncio_server)).

**Что нужно сделать:**
1. **TODO 6**: Реализовать тело корутины `handle_echo` — прочитать данные, залогировать адрес клиента и сообщение, отправить данные обратно, закрыть соединение.

```bash
subl asyncio_examples/02_echo_server.py
python3 asyncio_examples/02_echo_server.py
```

### Задание B3: Асинхронный эхо-клиент

Файл: `asyncio_examples/03_echo_client.py`

Реализуйте клиент, который подключается к серверу из задания B2.

**Что нужно сделать:**
1. **TODO 7**: Дописать отправку сообщения и получение ответа от сервера.
2. **TODO 8**: Запустить несколько клиентов одновременно через `asyncio.gather()` и проанализировать порядок вывода.

Запуск (в отдельном терминале, пока работает сервер):

```bash
subl asyncio_examples/03_echo_client.py
python3 asyncio_examples/03_echo_client.py
```

---

## Часть C: Многопроцессный TCP-сервер

В лабораторной работе 2 вы создавали многопоточный сервер с помощью `threading.Thread` ([2_threaded_server](https://github.com/fa-python-network/2_threaded_server)). Теперь реализуем аналогичный сервер, но с использованием `multiprocessing.Process` — каждый клиент обслуживается в отдельном процессе ОС.

### Задание C1: Многопроцессный эхо-сервер

Файл: `multiprocessing_examples/04_mp_echo_server.py`

Цикл приёма подключений и создание процессов уже реализованы. Ваша задача — дописать функцию обработки клиента.

**Что нужно сделать:**
1. **TODO 9**: Реализовать тело `handle_client` — принять данные, залогировать PID и сообщение, отправить обратно, закрыть соединение.

```bash
subl multiprocessing_examples/04_mp_echo_server.py
python3 multiprocessing_examples/04_mp_echo_server.py
```

### Тестирование

1. Запустите сервер в одном терминале.
2. Откройте 2–3 дополнительных терминала и в каждом запустите клиент:

```bash
python3 multiprocessing_examples/05_mp_echo_client.py
```

3. Обратите внимание на вывод сервера — **PID каждого обработчика будет разным**, в отличие от многопоточного сервера из lab 2, где PID одинаковый.

---

## Вопросы для анализа результатов

После выполнения всех заданий ответьте на следующие вопросы (впишите ответы в файл **`RESULTS.md`**):

### По multiprocessing:

1. Во сколько раз параллельное перемножение матриц быстрее последовательного? Совпадает ли ускорение с количеством ядер CPU? Почему?
2. Как изменяется время выполнения при увеличении числа процессов в `Pool`? Есть ли предел, после которого увеличение числа процессов не даёт ускорения?
3. Почему для передачи результатов из процессов нельзя использовать обычные глобальные переменные?

### По asyncio:

4. Почему асинхронная версия в `01_sync_vs_async.py` выполняется быстрее синхронной, хотя использует только одно ядро?
5. В каком порядке выводятся сообщения при запуске нескольких клиентов через `asyncio.gather()`? Является ли этот порядок детерминированным?
6. Что произойдёт, если в асинхронном сервере использовать `time.sleep()` вместо `await asyncio.sleep()`? Почему?

### По многопроцессному серверу:

7. Сравните вывод PID в многопроцессном сервере (`04_mp_echo_server.py`) с многопоточным сервером из лабораторной 2. Почему в multiprocessing PID разные, а в threading — одинаковые?

---

## Проверьте свои знания

После выполнения всех заданий пройдите тест из 20 вопросов по материалам лабораторной работы:

**[Открыть тест (questions.html)](questions.html)**

---

## Сдача работы: пошаговая инструкция Git и GitHub

> Вы уже сделали **Fork** и **Clone** в разделе «Подготовка». Ваш форк — это ваш личный репозиторий, куда вы можете отправлять (push) свою работу.

### Шаг 1. Настройка Git (выполняется один раз)

Укажите ваше имя и email — они будут записываться в каждый коммит:

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "your.email@example.com"
```

### Шаг 2. Настройка аутентификации

GitHub не принимает обычный пароль для push. Настройте один из двух способов: **Personal Access Token** (проще) или **SSH-ключ** (удобнее для постоянной работы).

---

#### Способ A: Personal Access Token (HTTPS)

**A.1. Создайте токен на GitHub:**

1. Перейдите: **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**.
   Прямая ссылка: [github.com/settings/tokens](https://github.com/settings/tokens)
2. Нажмите **"Generate new token"** → **"Generate new token (classic)"**.
3. Заполните:
   - **Note**: `lab14-vm` (произвольное описание)
   - **Expiration**: 30 days (достаточно для сдачи)
   - **Scopes**: поставьте галочку **`repo`** (полный доступ к репозиториям)
4. Нажмите **"Generate token"**.
5. **Скопируйте токен сейчас** — он показывается только один раз! Он выглядит примерно так:
   ```
   ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

**A.2. Сохраните токен на время работы:**

```bash
git config --global credential.helper 'cache --timeout=3600'
```

При первом `git push` Git спросит логин и пароль. Вместо пароля вставьте токен. Он сохранится в памяти на 1 час (3600 секунд) и повторно запрашиваться не будет.

> **Безопасность:** не используйте `credential.helper store` — он сохраняет токен в открытом виде в файле `~/.git-credentials`. Вариант `cache` хранит токен только в оперативной памяти и автоматически удаляет его после истечения таймаута.

---

#### Способ B: SSH-ключ

**B.1. Проверьте, есть ли уже SSH-ключ:**

```bash
ls -la ~/.ssh/
```

Если вы видите файлы `id_ed25519` и `id_ed25519.pub` (или `id_rsa` / `id_rsa.pub`) — ключ уже есть, переходите к шагу B.3.

**B.2. Сгенерируйте новый SSH-ключ:**

```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
```

На все вопросы нажимайте **Enter** (путь по умолчанию, без пароля):

```
Enter file in which to save the key (/home/user/.ssh/id_ed25519): [Enter]
Enter passphrase (empty for no passphrase): [Enter]
Enter same passphrase again: [Enter]
```

**B.3. Скопируйте публичный ключ:**

```bash
cat ~/.ssh/id_ed25519.pub
```

Скопируйте **весь** вывод (он начинается с `ssh-ed25519 ...`).

**B.4. Добавьте ключ на GitHub:**

1. Перейдите: **GitHub → Settings → SSH and GPG keys**.
   Прямая ссылка: [github.com/settings/keys](https://github.com/settings/keys)
2. Нажмите **"New SSH key"**.
3. Заполните:
   - **Title**: `Lab VM` (произвольное описание)
   - **Key**: вставьте скопированный публичный ключ
4. Нажмите **"Add SSH key"**.

**B.5. Проверьте подключение:**

```bash
ssh -T git@github.com
```

Ожидаемый ответ:

```
Hi <ВАШ_ЛОГИН>! You've successfully authenticated, but GitHub does not provide shell access.
```

**B.6. (Только для SSH) Смените remote URL на SSH:**

```bash
cd ~/lab14_part2
git remote set-url origin git@github.com:<ВАШ_ЛОГИН>/lab14_part2.git
```

> Если вы используете **HTTPS + токен**, этот шаг не нужен — remote URL уже настроен при клонировании.

---

### Шаг 3. Проверка текущего состояния

Убедитесь, что все TODO выполнены и код запускается без ошибок. Заполните файл **`RESULTS.md`** — вставьте вывод каждой программы, заполните сравнительную таблицу и впишите ответы на вопросы. Затем проверьте, какие файлы были изменены:

```bash
cd ~/lab14_part2
git status
```

Пример вывода:

```
On branch main
Changes not staged for commit:
  modified:   RESULTS.md
  modified:   multiprocessing_examples/02_matrix_multiply.py
  modified:   multiprocessing_examples/03_pool_matrix.py
  modified:   multiprocessing_examples/04_mp_echo_server.py
  modified:   asyncio_examples/01_sync_vs_async.py
  modified:   asyncio_examples/02_echo_server.py
  modified:   asyncio_examples/03_echo_client.py
```

### Шаг 4. Добавление файлов в индекс (staging)

Добавьте все изменённые файлы:

```bash
git add .
```

Или добавьте конкретные файлы по одному:

```bash
git add multiprocessing_examples/02_matrix_multiply.py
git add asyncio_examples/02_echo_server.py
```

Проверьте, что файлы добавлены:

```bash
git status
```

Теперь файлы должны быть в секции `Changes to be committed` (зелёным цветом).

### Шаг 5. Создание коммита

```bash
git commit -m "lab14 part2: выполнены TODO — multiprocessing и asyncio"
```

Коммит — это «снимок» вашей работы. Сообщение после `-m` кратко описывает, что было сделано.

Проверьте, что коммит создан:

```bash
git log --oneline -3
```

### Шаг 6. Отправка на GitHub (push)

Вы клонировали **свой форк** — вы единственный, кто в него пишет. Поэтому push должен пройти без проблем:

```bash
git push -u origin main
```

Флаг `-u` привязывает локальную ветку `main` к удалённой. В дальнейшем можно просто писать `git push`.

> **Если push отклонён** (ошибка `rejected — non-fast-forward`), значит в вашем форке на GitHub есть изменения, которых нет локально (например, вы редактировали файл через веб-интерфейс). В этом случае сначала синхронизируйте:
>
> ```bash
> git pull origin main --rebase
> ```
>
> Эта команда скачает изменения с GitHub и поставит ваши коммиты **поверх** них. Если возникнет конфликт — Git покажет, в каких файлах проблема. Исправьте их, затем:
>
> ```bash
> git add .
> git rebase --continue
> ```
>
> После этого повторите `git push origin main`.

**Если ветка называется `master`** (а не `main`):

```bash
git branch
```

Если текущая ветка — `master`, используйте `git push -u origin master`.

**Если при push возникает ошибка аутентификации:**
- Для HTTPS: убедитесь, что ввели токен (не пароль) и у токена есть scope `repo`.
- Для SSH: проверьте `ssh -T git@github.com` и убедитесь, что публичный ключ добавлен на GitHub.

### Шаг 7. Проверка результата

1. Откройте в браузере: `https://github.com/<ВАШ_ЛОГИН>/lab14_part2`
2. Убедитесь, что все файлы загружены и содержат ваш код.
3. Проверьте, что `RESULTS.md` заполнен: вывод программ, таблица сравнения и ответы на вопросы.
4. Продемонстрируйте работающий код и результаты преподавателю.

### Схема рабочего процесса

```mermaid
flowchart LR
    A["git add ."] --> B["git commit -m '...'"]
    B --> C["git push origin main"]
    C --> D["GitHub\n(ваш форк)"]
```

---

## Ссылки

- [Лекция: Асинхронное программирование](https://koroteev.site/os/3/4-threading/)
- [Репозиторий: Многопоточный сервер](https://github.com/fa-python-network/2_threaded_server)
- [Репозиторий: Многопроцессность](https://github.com/fa-python-network/3_Parallelism)
- [Репозиторий: Asyncio сервер](https://github.com/fa-python-network/4_asyncio_server)
- [Документация: multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
- [Документация: asyncio](https://docs.python.org/3/library/asyncio.html)
