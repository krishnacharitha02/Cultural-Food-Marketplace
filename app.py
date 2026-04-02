from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        passwd="USG26@ohcwy11",
        database="cultural_food_marketplace"
    )

def get_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

def get_cart(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT p.prod_name, ci.quantity
    FROM Cart_Item ci
    JOIN Product p ON ci.product_id = p.product_id
    JOIN Cart c On ci.cart_id = c.cart_id
    WHERE c.user_id = %s
    """

    cursor.execute(query)
    cart = cursor.fetchall()
    cursor.close()
    conn.close()
    return cart

@app.route("/")
def home():
    users = get_users()
    return render_template("index.html", users=users)

@app.route("/products")
def products():
    products = get_products()
    return render_template("products.html", products=products)

@app.route("/cart")
def cart():
    user_id = 1
    cart = get_cart(user_id)
    return render_template("cart.html", cart=cart)

@app.route("/customer")
def customer():
    return render_template("customer.html")

@app.route("/vendor")
def vendor():
    return render_template("vendor.html")

@app.route("/recommend")
def recommend():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.prod_name, SUM(oi.quantity) AS total_orders
        FROM Order_Item oi
        JOIN Product p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.prod_name
        ORDER BY total_orders DESC
    """)
    recs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("recommend.html", recs=recs)

@app.route("/review/<int:product_id>")
def review(product_id):
    return render_template("review.html", product_id=product_id)

def add_product_to_db(prod_name, prod_description, price, stock_quantity):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO Product
    (vendor_id, cuisine_type_id, prod_name, prod_description, price, availability, stock_quantity, storytelling)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (1, 1, prod_name, prod_description, price, True, stock_quantity, "Added from website")
    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

def add_review_to_db(rating, comments, user_id, product_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO Review (rating, comments, user_id, product_id)
        VALUES (%s, %s, %s, %s)
        """
        values = (rating, comments, user_id, product_id)

        cursor.execute(query, values)
        conn.commit()

    except mysql.connector.Error as err:
        print("Database error:", err)
        if conn:
            conn.rollback()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_cart_to_db(cart_id, product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO Cart_Item (cart_id, product_id, quantity)
    VALUES (%s, %s, %s)
    """

    values = (cart_id, product_id, quantity)
    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

@app.route("/add_products", methods=["POST"])
def add_products():
    prod_name = request.form["prod_name"]
    prod_description = request.form["prod_description"]
    price = float(request.form["price"])
    stock_quantity = int(request.form["stock_quantity"])

    add_product_to_db(prod_name, prod_description, price, stock_quantity)
    return redirect("/products")

@app.route("/write_review", methods=["POST"])
def write_review():
    rating = int(request.form["rating"])
    comments = request.form["comments"]
    user_id = int(request.form["user_id"])
    product_id = int(request.form["product_id"])

    add_review_to_db(rating, comments, user_id, product_id)
    return redirect("/customer")

@app.route("/add_cart", methods=["POST"])
def add_cart():
    cart_id = int(request.form["cart_id"])
    product_id = int(request.form["product_id"])
    quantity = int(request.form["quantity"])

    add_cart_to_db(cart_id, product_id, quantity)
    return redirect("/cart")

@app.route("/place_order", methods=["POST"])
def place_order():
    user_id = 1
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT cart_id FROM Cart WHERE user_id = %s", (user_id,))
        cart = cursor.fetchone()

        if not cart:
            return redirect("/cart")

        cart_id = cart[0]

        cursor.execute("""
            SELECT p.product_id, p.prod_name, ci.quantity, p.price
            FROM Cart_Item ci
            JOIN Product p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        items = cursor.fetchall()

        if not items:
            return redirect("/cart")

        total = sum(item[2] * item[3] for item in items)

        cursor.execute(
            "INSERT INTO Order_Info (order_date, total_amount, user_id) VALUES (CURDATE(), %s, %s)",
            (total, user_id)
        )
        order_id = cursor.lastrowid

        for item in items:
            cursor.execute(
                "INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase) VALUES (%s, %s, %s, %s)",
                (order_id, item[0], item[2], item[3])
            )

        cursor.execute("DELETE FROM Cart_Item WHERE cart_id = %s", (cart_id,))
        conn.commit()

        return redirect(f"/order_confirm/{order_id}")

    except mysql.connector.Error as err:
        print("Database error:", err)
        if conn:
            conn.rollback()
        return "An error occurred while placing the order."

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/order_confirm/<int:order_id>")
def order_confirm(order_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.prod_name, oi.quantity, oi.price_at_purchase
        FROM Order_Item oi
        JOIN Product p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """, (order_id,))
    order_items = cursor.fetchall()

    total = sum(item[1] * item[2] for item in order_items)

    cursor.close()
    conn.close()

    return render_template("order.html", order_items=order_items, total=round(total, 2))

if __name__ == "__main__":
    app.run(debug=True)