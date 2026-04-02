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

def get_cart():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT p.prod_name, c.quantity
    FROM Cart_Item c
    JOIN Product p
        ON c.product_id = p.product_id
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
    cart = get_cart()
    return render_template("cart.html", cart=cart)

@app.route("/customer")
def customer():
    return render_template("customer.html")

@app.route("/vendor")
def vendor():
    return render_template("vendor.html")

@app.route("/recommend")
def recommend():
    return render_template("recommend.html")

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
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO Review (rating, comments, user_id, product_id)
    VALUES (%s, %s, %s, %s)
    """

    values = (rating, comments, user_id, product_id)
    cursor.execute(query, values)
    conn.commit()

    cursor.close()
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
    price = request.form["price"]
    stock_quantity = request.form["stock_quantity"]

    add_product_to_db(prod_name, prod_description, price, stock_quantity)
    return redirect("/products")


@app.route("/write_review", methods=["POST"])
def write_review():
    rating = request.form["rating"]
    comments = request.form["comments"]
    user_id = request.form["user_id"]
    product_id = request.form["product_id"]

    add_review_to_db(rating, comments, user_id, product_id)
    return redirect("/customer")


@app.route("/add_cart", methods=["POST"])
def add_cart():
    cart_id = request.form["cart_id"]
    product_id = request.form["product_id"]
    quantity = request.form["quantity"]

    add_cart_to_db(cart_id, product_id, quantity)
    return redirect("/cart")

if __name__ == "__main__":
    app.run(debug=True)