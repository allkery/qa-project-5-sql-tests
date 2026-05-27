# 📋 ЗАДАНИЕ ДЛЯ QA-ИНЖЕНЕРА
## Проект: Магазин с базой данных
## Таск: QA-105 | Приоритет: HIGH

---

### 🧑‍💻 Контекст

Команда backend разработала API магазина с реальной базой данных SQLite.
В отличие от прошлых проектов — данные теперь сохраняются в БД,
а не хранятся в памяти.

**Главное отличие этого проекта** — ты проверяешь не только ответы API,
но и то что данные корректно сохранились в базе данных.
Это стандартная практика в реальных командах.

У тебя два инструмента:
- `client` — делает HTTP запросы к API
- `db` — прямое подключение к SQLite, пишешь SQL запросы

---

### 🗄️ Структура базы данных

```sql
users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER,
    created_at TIMESTAMP
)

products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    stock INTEGER
)

orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP
)
```

---

### 📦 Что нужно протестировать

#### 👤 Пользователи

| # | Что тестируем | Инструмент |
|---|--------------|-----------|
| 1 | Создать пользователя — статус 201 | API |
| 2 | После создания пользователь есть в БД | API + DB |
| 3 | Данные в БД совпадают с данными из API | API + DB |
| 4 | Нельзя создать двух пользователей с одним email — статус 409 | API |
| 5 | В БД действительно только один такой email | API + DB |
| 6 | Создать без name — статус 400 | API |
| 7 | Создать без email — статус 400 | API |
| 8 | Создать с некорректным age (строка) — статус 400 | API |
| 9 | Получить пользователя по ID — данные совпадают | API |
| 10 | Получить несуществующего пользователя — статус 404 | API |
| 11 | Удалить пользователя — статус 200 | API |
| 12 | После удаления пользователя нет в БД | API + DB |

#### 📦 Товары

| # | Что тестируем | Инструмент |
|---|--------------|-----------|
| 13 | Создать товар — статус 201 | API |
| 14 | После создания товар есть в БД | API + DB |
| 15 | Фильтр по категории возвращает только нужные товары | API + DB |
| 16 | Создать товар без name — статус 400 | API |
| 17 | Создать товар с отрицательной ценой — статус 400 | API |

#### 🛒 Заказы

| # | Что тестируем | Инструмент |
|---|--------------|-----------|
| 18 | Создать заказ — статус 201 | API |
| 19 | total_price считается правильно (price * quantity) | API + DB |
| 20 | Заказ с несуществующим user_id — статус 404 | API |
| 21 | Заказ с несуществующим product_id — статус 404 | API |
| 22 | Заказ с quantity = 0 — статус 400 | API |
| 23 | Обновить статус заказа на "confirmed" — статус 200 | API |
| 24 | В БД статус действительно изменился | API + DB |
| 25 | Обновить статус на недопустимое значение — статус 400 | API |

#### 📊 Статистика (SQL запросы)

| # | Что тестируем | Инструмент |
|---|--------------|-----------|
| 26 | Выручка без отменённых заказов считается правильно | API |
| 27 | Пользователи с заказами возвращаются корректно | API |
| 28 | Пользователь без заказов не попадает в список | API |
| 29 | Топ товаров — товар с большим количеством заказов идёт первым | API |

---

### ✅ Критерии приёмки

- [ ] Все 29 тестов написаны
- [ ] В тестах 2, 3, 12, 14, 15, 19, 24 используется fixture `db`
- [ ] Все тесты проходят
- [ ] Сгенерирован HTML-отчёт

---

### 🚀 Запуск

```bash
pip install -r requirements.txt
pytest tests/ -v
pytest tests/ -v --html=report.html --self-contained-html
```

---

### 📁 Структура

```
sql_project/
├── src/
│   └── app.py           ← код от разработчика (не трогать)
├── tests/
│   └── test_shop.py     ← твой файл
├── requirements.txt
└── TASK.md
```

---

### 💡 Подсказки

**Как проверить данные в БД после API запроса:**
```python
def test_user_saved_in_db(client, db):
    client.post("/users", json={"name": "Иван", "email": "ivan@test.ru"})
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", ("ivan@test.ru",)
    ).fetchone()
    assert user is not None
    assert user["name"] == "Иван"
```

**Как проверить количество записей в таблице:**
```python
count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
assert count == 1
```

**Как проверить что запись удалена:**
```python
user = db.execute("SELECT * FROM users WHERE id = ?", (1,)).fetchone()
assert user is None
```

**Как проверить total_price:**
```python
order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
assert order["total_price"] == product_price * quantity
```
