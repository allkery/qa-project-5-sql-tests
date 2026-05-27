"""
Веб-приложение магазина с SQLite базой данных.
Модуль разработан командой backend. Передан в QA для тестирования.
"""

import sqlite3
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")


def get_db():
    """Получить соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализировать базу данных и создать таблицы."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            stock INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    conn.commit()
    conn.close()


def _reset_db():
    """Сброс базы данных — используется в тестах."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM orders;
        DELETE FROM products;
        DELETE FROM users;
        DELETE FROM sqlite_sequence WHERE name IN ('users', 'products', 'orders');
    """)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────
# USERS
# ──────────────────────────────────────────

@app.route("/users", methods=["GET"])
def get_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users]), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404
    return jsonify(dict(user)), 200


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    age = data.get("age")

    if not name:
        return jsonify({"error": "Поле name обязательно"}), 400
    if not email:
        return jsonify({"error": "Поле email обязательно"}), 400
    if age is not None and (not isinstance(age, int) or age < 0 or age > 150):
        return jsonify({"error": "Поле age должно быть числом от 0 до 150"}), 400

    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            (name, email, age)
        )
        user_id = cursor.lastrowid
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.commit()
        return jsonify(dict(user)), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email уже существует"}), 409
    finally:
        conn.close()


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Пользователь не найден"}), 404
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Пользователь удалён"}), 200


# ──────────────────────────────────────────
# PRODUCTS
# ──────────────────────────────────────────

@app.route("/products", methods=["GET"])
def get_products():
    category = request.args.get("category")
    conn = get_db()
    if category:
        products = conn.execute(
            "SELECT * FROM products WHERE category = ?", (category,)
        ).fetchall()
    else:
        products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(p) for p in products]), 200


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое"}), 400

    name = data.get("name", "").strip()
    price = data.get("price")
    category = data.get("category", "").strip()
    stock = data.get("stock", 0)

    if not name:
        return jsonify({"error": "Поле name обязательно"}), 400
    if price is None or not isinstance(price, (int, float)) or price < 0:
        return jsonify({"error": "Поле price должно быть числом >= 0"}), 400
    if not category:
        return jsonify({"error": "Поле category обязательно"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)",
        (name, price, category, stock)
    )
    product_id = cursor.lastrowid
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify(dict(product)), 201


# ──────────────────────────────────────────
# ORDERS
# ──────────────────────────────────────────

@app.route("/orders", methods=["GET"])
def get_orders():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    return jsonify([dict(o) for o in orders]), 200


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое"}), 400

    user_id = data.get("user_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not user_id or not product_id:
        return jsonify({"error": "Поля user_id и product_id обязательны"}), 400
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "Поле quantity должно быть целым числом >= 1"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Пользователь не найден"}), 404

    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "Товар не найден"}), 404

    total_price = product["price"] * quantity

    cursor = conn.execute(
        "INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES (?, ?, ?, ?)",
        (user_id, product_id, quantity, total_price)
    )
    order_id = cursor.lastrowid
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify(dict(order)), 201


@app.route("/orders/<int:order_id>/status", methods=["PATCH"])
def update_order_status(order_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Тело запроса пустое"}), 400

    status = data.get("status", "").strip()
    allowed = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

    if status not in allowed:
        return jsonify({"error": f"Статус должен быть одним из: {', '.join(allowed)}"}), 400

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"error": "Заказ не найден"}), 404

    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify(dict(order)), 200


# ──────────────────────────────────────────
# STATS (только SQL запросы)
# ──────────────────────────────────────────

@app.route("/stats/top-products", methods=["GET"])
def top_products():
    """Топ товаров по количеству заказов."""
    conn = get_db()
    result = conn.execute("""
        SELECT p.name, COUNT(o.id) as order_count
        FROM products p
        LEFT JOIN orders o ON p.id = o.product_id
        GROUP BY p.id
        ORDER BY order_count DESC
        LIMIT 5
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in result]), 200


@app.route("/stats/revenue", methods=["GET"])
def revenue():
    """Общая выручка по всем заказам."""
    conn = get_db()
    result = conn.execute(
        "SELECT SUM(total_price) as total FROM orders WHERE status != 'cancelled'"
    ).fetchone()
    conn.close()
    return jsonify({"total_revenue": result["total"] or 0}), 200


@app.route("/stats/users-with-orders", methods=["GET"])
def users_with_orders():
    """Пользователи у которых есть хотя бы один заказ."""
    conn = get_db()
    result = conn.execute("""
        SELECT u.name, u.email, COUNT(o.id) as orders_count
        FROM users u
        JOIN orders o ON u.id = o.user_id
        GROUP BY u.id
        HAVING COUNT(o.id) > 0
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in result]), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
