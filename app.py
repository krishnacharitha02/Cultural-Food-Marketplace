from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "your_secret_key"

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

def get_products(dietary_tag=None):
    conn = get_connection()
    cursor = conn.cursor()

    if dietary_tag:
        query = """
        SELECT DISTINCT p.*
        FROM PRoduct p
        JOIN Product_Dietary pd ON p.product_id = pd.product_id
        JOIN Dietary d ON pd.tag_id = d.tag_id
        WHERE d.tag_name = %s
        """
        cursor.execute(query, (dietary_tag,))
    else:
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

    cursor.execute(query, (user_id,))
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
    dietary_tag = request.args.get("dietary")
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

def add_product_to_db(vendor_id, cuisine_type_id, prod_name, prod_description, price, stock_quantity):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO Product
    (vendor_id, cuisine_type_id, prod_name, prod_description, price, availability, stock_quantity, storytelling)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (vendor_id, cuisine_type_id, prod_name, prod_description, price, True, stock_quantity, "Added from website")
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
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    prod_name = request.form["prod_name"]
    prod_description = request.form["prod_description"]
    price = request.form["price"]
    stock_quantity = request.form["stock_quantity"]
    cuisine_type_id = request.form["cuisine_type_id"]

    add_product_to_db(
        session["vendor_id"],
        cuisine_type_id,
        prod_name,
        prod_description,
        price,
        stock_quantity
    )
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
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    product_id = request.form["product_id"]
    quantity = request.form["quantity"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT cart_id FROM Cart WHERE user_id = %s", (user_id,))
    cart = cursor.fetchone()

    if not cart:
        cursor.execute("INSERT INTO Cart (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        cart_id = cursor.lastrowid
    else:
        cart_id = cart[0]

    cursor.execute("""
        INSERT INTO Cart_Item (cart_id, product_id, quantity)
        VALUES (%s, %s, %s)
    """, (cart_id, product_id, quantity))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/cart")

@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
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
    cursor.close()
    conn.close()

    return redirect(f"/order_confirm/{order_id}")

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

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    user_name = request.form["user_name"]
    email = request.form["email"]
    password = request.form["password"]
    address = request.form["address"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Users (user_name, email, acc_password, address)
        VALUES (%s, %s, %s, %s)
    """, (user_name, email, password, address))
    conn.commit()

    user_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO Cart (user_id)
        VALUES (%s)
    """, (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/login")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login_user", methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, user_name
        FROM Users
        WHERE email = %s AND acc_password = %s
    """, (email, password))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        session["user_id"] = user[0]
        session["user_name"] = user[1]
        session["role"] = "customer"
        return redirect("/customer")
    else:
        return "Invalid email or password"
    
@app.route("/logout")
def logout():
    return redirect("/")

@app.route("/vendor_register")
def vendor_register():
    return render_template("vendor_register.html")

@app.route("/register_vendor", methods=["POST"])
def register_vendor():
    business_name = request.form["business_name"]
    cuisine_type_id = request.form["cuisine_type_id"]
    location = request.form["location"]
    phone = request.form["contact_info_phone"]
    email = request.form["contact_info_email"]
    password = request.form["vendor_password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Vendor
        (business_name, cuisine_type_id, location, contact_info_phone, contact_info_email, vendor_password)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (business_name, cuisine_type_id, location, phone, email, password))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/vendor_login")

@app.route("/vendor_login")
def vendor_login():
    return render_template("vendor_login.html")

@app.route("/login_vendor", methods=["POST"])
def login_vendor():
    email = request.form["contact_info_email"]
    password = request.form["vendor_password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT vendor_id, business_name
        FROM Vendor
        WHERE contact_info_email = %s AND vendor_password = %s
    """, (email, password))

    vendor = cursor.fetchone()

    cursor.close()
    conn.close()

    if vendor:
        session["vendor_id"] = vendor[0]
        session["vendor_name"] = vendor[1]
        session["role"] = "vendor"
        return redirect("/vendor")
    else:
        return "Invalid vendor login"
    
@app.route("/delete_product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    vendor_id = session["vendor_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Product
        WHERE product_id = %s AND vendor_id = %s
    """, (product_id, vendor_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/products")

@app.route("/delete_review/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Review
        WHERE review_id = %s AND user_id = %s
    """, (review_id, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/customer")

