import pytest
from src.app import app, _reset_db, init_db, DB_PATH
import sqlite3


@pytest.fixture
def client():
    """
    Тестовый клиент Flask.
    Перед каждым тестом сбрасывает и пересоздаёт базу данных.
    """
    app.config["TESTING"] = True
    init_db()
    _reset_db()
    with app.test_client() as client:
        yield client


@pytest.fixture
def db():
    """
    Прямое подключение к SQLite базе данных.
    Используй когда нужно проверить данные напрямую в БД,
    а не через API.
    """
    init_db()
    _reset_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def user():
    return {
        "name": "Alex",
        "email": "example@example.com",
        "age": 16
    }


@pytest.fixture
def product():
    return {
        "name": "Macbook",
        "price": 75000,
        "category": "Laptops"
    }


@pytest.fixture
def order(client, user, product):
    client.post("/users", json=user)
    client.post("/products", json=product)
    client.post("/orders", json={
        "user_id": 1,
        "product_id": 1,
        "quantity": 1
    })