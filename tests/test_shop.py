import pytest
import sqlite3
from src.app import app, _reset_db, init_db, DB_PATH


# ==================================
#           Пользователи
# ==================================


def test_create_user_returns_201(client, user):
    """Создать пользователя — статус 201"""

    response = client.post("/users", json=user)
    assert response.status_code == 201


def test_create_user_persists_in_database(client, user, db):
    """После создания пользователь есть в БД"""

    client.post("/users", json=user)
    result = db.execute(
        "SELECT * FROM users"
    ).fetchone()
    assert result is not None
    assert result["name"] == user["name"]


def test_create_user_db_data_matches_api_response(client, user, db):
    """Данные в БД совпадают с данными из API"""

    client.post("/users", json=user)
    result = db.execute(
        "SELECT * FROM users"
    ).fetchone()

    assert result is not None
    assert result["id"] == 1
    assert result["name"] == user["name"]
    assert result["email"] == user["email"]
    assert result["age"] == user["age"]


def test_create_user_duplicate_email_returns_409(client):
    """Нельзя создать двух пользователей с одним email — статус 409"""

    client.post("/users", json={"name": "Иван", "email": "ivan@test.ru"})
    response = client.post("/users", json={"name": "Пётр", "email": "ivan@test.ru"})

    assert response.status_code == 409


def test_duplicate_email_not_saved_in_db(client, db):
    """В БД действительно только один такой email"""

    client.post("/users", json={"name": "Иван", "email": "ivan@test.ru", "age": 30})
    client.post("/users", json={"name": "Пётр", "email": "ivan@test.ru", "age": 40})

    count = db.execute(
        "SELECT COUNT(*) FROM users WHERE email = ?", ("ivan@test.ru",)
    ).fetchone()[0]

    assert count == 1


def test_create_user_missing_name_returns_400(client):
    """Создать без name — статус 400"""

    response = client.post("/users", json={"email": "ivan@test.ru", "age": 30})
    assert response.status_code == 400


def test_create_user_missing_email_returns_400(client):
    """Создать без email — статус 400"""

    response = client.post("/users", json={"name": "Пётр", "age": 40})
    assert response.status_code == 400


def test_create_user_string_age_returns_400(client):
    """Создать с некорректным age (строка) — статус 400"""

    response = client.post("/users", json={"name": "Пётр", "email": "ivan@test.ru", "age": "40"})
    assert response.status_code == 400


def test_get_user_by_id_returns_correct_data(client, user):
    """Получить пользователя по ID — данные совпадают"""

    client.post("/users", json=user)
    response = client.get("/users/1").get_json()

    assert response["id"] == 1
    assert response["name"] == user["name"]
    assert response["email"] == user["email"]
    assert response["age"] == user["age"]


def test_get_nonexistent_user_returns_404(client):
    """Получить несуществующего пользователя — статус 404"""

    response = client.get("/users/1")
    assert response.status_code == 404


def test_delete_user_returns_200(client, user):
    """Удалить пользователя — статус 200"""

    client.post("/users", json=user)
    response = client.delete("/users/1")
    assert response.status_code == 200


def test_delete_user_removes_record_from_db(client, db, user):
    """После удаления пользователя нет в БД"""

    client.post("/users", json=user)
    user = db.execute("SELECT * FROM users").fetchone()
    assert user is not None

    client.delete("/users/1")
    user = db.execute("SELECT * FROM users").fetchone()
    assert user is None


# ==================================
#             Товары
# ==================================


def test_create_product_returns_201(client, product):
    """Создать товар — статус 201"""

    response = client.post("/products", json=product)
    assert response.status_code == 201


def test_create_product_persists_in_database(client, product, db):
    """После создания товар есть в БД"""

    client.post("/products", json=product)
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count == 1


def test_get_products_by_category_filters_correctly_in_db(client, db):
    """Фильтр по категории возвращает только нужные товары"""

    client.post("/products", json={"name": "Macbook", "price": 75000, "category": "Laptops"})
    client.post("/products", json={"name": "iPhone", "price": 100000, "category": "Phones"})

    response = client.get("/products", query_string={"category": "Phones"}).get_json()
    data = db.execute("SELECT COUNT(*) FROM products WHERE category = ?", ('Phones',)).fetchone()[0]

    assert len(response) == 1
    assert data == 1


def test_create_product_missing_name_returns_400(client):
    """Создать товар без name — статус 400"""

    response = client.post("/products", json={"price": 75000, "category": "Laptops"})
    assert response.status_code == 400


def test_create_product_negative_price_returns_400(client):
    """Создать товар с отрицательной ценой — статус 400"""
    
    response = client.post("/products", json={"name": "Macbook", "price": -75000, "category": "Laptops"})
    assert response.status_code == 400


# ==================================
#             Заказы
# ==================================


def test_create_order_returns_201(client, user, product):
    """Создать заказ — статус 201"""

    client.post("/products", json=product)
    client.post("/users", json=user)
    response = client.post("/orders", json = {
        "user_id": 1,
        "product_id": 1,
        "quantity": 1
    })

    assert response.status_code == 201


def test_create_order_calculates_total_price_correctly_in_db(db, order, product):
    """При создании заказа total_price сохраняется в БД правильно"""

    price = db.execute("SELECT total_price FROM orders WHERE id = ?", (1,)).fetchone()[0]
    assert price == product["price"]


def test_create_order_nonexistent_user_id_returns_404(client, product):
    """Создать заказ с несуществующим user_id — статус 404"""

    client.post("/products", json=product)
    response = client.post("/orders", json={
        "user_id": 999,
        "product_id": 1,
        "quantity": 1
    })
    assert response.status_code == 404


def test_create_order_nonexistent_product_id_returns_404(client, user):
    """Создать заказ с несуществующим product_id — статус 404"""

    client.post("/users", json=user)
    response = client.post("/orders", json={
        "user_id": 1,
        "product_id": 999,
        "quantity": 1
    })
    assert response.status_code == 404


def test_create_order_zero_quantity_returns_400(client, product, user):
    """Создать заказ с quantity=0 — статус 400"""

    client.post("/products", json=product)
    client.post("/users", json=user)
    response = client.post("/orders", json={
        "user_id": 1,
        "product_id": 1,
        "quantity": 0
    })
    assert response.status_code == 400


def test_update_order_status_to_confirmed_returns_200(order, client):
    """Обновить статус заказа на "confirmed" — статус 200"""

    response = client.patch("/orders/1/status", json={"status": "confirmed"})
    assert response.status_code == 200


def test_update_order_status_updates_database(client, db, order):
    """	В БД статус действительно изменился"""

    db_result = db.execute("SELECT * FROM orders").fetchone()
    assert db_result["status"] == "pending"

    response = client.patch("/orders/1/status", json={"status": "confirmed"})
    db_result = db.execute("SELECT * FROM orders").fetchone()

    assert db_result["status"] == "confirmed"
    assert response.status_code == 200


def test_update_order_status_invalid_value_returns_400(client, order):
    """Обновить статус на недопустимое значение — статус 400"""
    
    response = client.patch("/orders/1/status", json={"status": "invalid_status"})
    assert response.status_code == 400


# ==================================
#           Статистика
# ==================================


def test_analytics_revenue_calculation_excludes_cancelled_orders(order, client, product):
    """Выручка без отменённых заказов считается правильно"""

    product_2 = {
        "name": "iPhone",
        "price": 100000,
        "category": "Phones"
    }
    client.post("/products", json=product_2)
    client.post("/orders", json={
    "user_id": 1,
    "product_id": 2,
    "quantity": 1
    })

    response = client.get("/stats/revenue")
    assert response.get_json()["total_revenue"] == product["price"] + product_2["price"]

    client.patch("/orders/2/status", json={"status": "cancelled"})

    response = client.get("/stats/revenue")
    assert response.get_json()["total_revenue"] == product["price"]


def test_analytics_get_users_with_orders_returns_correct_list(client, order):
    """Пользователи с заказами возвращаются корректно"""

    client.post("/users", json={"name": "Иван", "email": "ivan@test.ru"})
    client.post("/products", json={"name": "Laptop", "price": 50000, "category": "Laptops"})
    client.post("/orders", json={
        "user_id": 2, 
        "product_id": 2, 
        "quantity": 1
    })

    response = client.get("/stats/users-with-orders").get_json()
    assert len(response) == 2


def test_analytics_user_without_orders_is_excluded_from_list(client, user):
    """Пользователь без заказов не попадает в список"""

    client.post("/users", json=user)
    response = client.get("/stats/users-with-orders").get_json()
    assert len(response) == 0


def test_analytics_top_products_is_sorted_by_orders_count_desc(client, product, order):
    """Топ товаров — товар с большим количеством заказов идёт первым"""

    client.post("/users", json={"name": "Иван", "email": "ivan@test.ru"})
    product_2 = {"name": "Laptop", "price": 50000, "category": "Laptops"}
    client.post("/products", json=product_2)
    client.post("/orders", json={
        "user_id": 2, 
        "product_id": 1, 
        "quantity": 1
    })

    response = client.get("/stats/top-products").get_json()
    
    assert response[0]["name"] == product["name"]
    assert response[1]["name"] == product_2["name"]