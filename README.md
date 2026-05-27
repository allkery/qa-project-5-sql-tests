# 🗄️ Shop API — SQL Testing Project

![Python](https://img.shields.io/badge/Python-3.11-blue)
![pytest](https://img.shields.io/badge/pytest-passing-brightgreen)
![SQLite](https://img.shields.io/badge/database-SQLite-lightblue)
![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen)

Пятый учебный проект по QA-автоматизации.
QA-автоматизация REST API магазина с реальной базой данных SQLite.  

---

## 📌 Что тестируется

Проект покрывает 29 тест-кейсов по четырём сущностям:

| Сущность | Кол-во тестов | Что проверяется |
|----------|:---:|---|
| 👤 Пользователи | 12 | CRUD, валидация полей, дубликат email, проверка через DB |
| 📦 Товары | 5 | Создание, фильтрация по категории, валидация цены |
| 🛒 Заказы | 8 | Создание, расчёт суммы, статусы, проверка через DB |
| 📊 Статистика | 4 | SQL-аналитика: выручка, топ товаров, активные пользователи |

---

## 🛠️ Стек

- **Python 3.11**
- **Flask** — веб-фреймворк (тестируемое приложение)
- **SQLite** — реляционная база данных
- **pytest** — тестовый фреймворк
- **pytest-html** — HTML-отчёт о прогоне тестов
- **GitHub Actions** — CI/CD пайплайн

---

## 🗂️ Структура проекта

```
sql_project/
├── src/
│   └── app.py              # Flask API + SQLite (код приложения)
├── tests/
│   └── test_shop.py        # 29 тест-кейсов
├── conftest.py             # Фикстуры: client, db, user, product, order
├── requirements.txt
├── .github/
│   └── workflows/
│       └── tests.yml       # CI пайплайн
└── README.md
```

---

## 🗄️ Схема базы данных

```sql
users (id, name, email UNIQUE, age, created_at)

products (id, name, price, category, stock)

orders (
  id, user_id → users(id),
  product_id → products(id),
  quantity, total_price,
  status: pending | confirmed | shipped | delivered | cancelled,
  created_at
)
```

---

## 🚀 Запуск

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить тесты
pytest tests/ -v

# Запустить с HTML-отчётом
pytest tests/ -v --html=report.html --self-contained-html
```

---

## 🔍 Ключевые техники

### Проверка через API + DB

Тесты используют два инструмента одновременно: HTTP-клиент и прямое подключение к SQLite. Это позволяет убедиться, что данные не просто возвращаются в ответе API, но реально сохраняются в базе.

```python
def test_create_user_persists_in_database(client, db):
    client.post("/users", json={"name": "Alex", "email": "alex@test.ru"})

    result = db.execute("SELECT * FROM users").fetchone()
    assert result is not None
    assert result["name"] == "Alex"
```

### Изоляция тестов

Каждый тест начинается с чистой базы данных — фикстуры `client` и `db` вызывают `_reset_db()` перед каждым тестом. Тесты не зависят друг от друга.

### SQL-аналитика

Проект включает тесты для SQL-запросов с агрегацией: `SUM`, `COUNT`.

```python
def test_analytics_revenue_excludes_cancelled_orders(order, client, product):
    client.patch("/orders/2/status", json={"status": "cancelled"})
    response = client.get("/stats/revenue")
    assert response.get_json()["total_revenue"] == product["price"]
```

---

## ✅ CI/CD

GitHub Actions автоматически запускает все тесты при каждом пуше и сохраняет HTML-отчёт как артефакт сборки.

```yaml
on: [push]
runs-on: ubuntu-latest
python-version: '3.11'
```
