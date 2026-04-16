from flask import Flask, render_template, request, redirect, session, url_for
import pyodbc

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=culturalfood-sql-server8291.database.windows.net;"
        "DATABASE=cultural-food-marketplace;"
        "UID=culturalfoodadmin;"
        "PWD=CulturalFood26;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
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

    base_query = """
        SELECT DISTINCT p.*, v.business_name, ct.cuisine_name
        FROM Product p
        JOIN Vendor v ON p.vendor_id = v.vendor_id
        JOIN Cuisine_Type ct ON p.cuisine_type_id = ct.cuisine_type_id
    """

    if dietary_tag:
        query = base_query + """
        JOIN Product_Dietary pd ON p.product_id = pd.product_id
        JOIN Dietary d ON pd.tag_id = d.tag_id
        WHERE d.tag_name = ?
        """
        cursor.execute(query, (dietary_tag,))
    else:
        cursor.execute(base_query)

    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

def get_cart(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.prod_name, ci.quantity
        FROM Cart_Item ci
        JOIN Product p ON ci.product_id = p.product_id
        JOIN Cart c ON ci.cart_id = c.cart_id
        WHERE c.user_id = ?
    """, (user_id,))

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
    products = get_products(dietary_tag)
    return render_template("products.html", products=products)

@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login")
    cart = get_cart(session["user_id"])
    return render_template("cart.html", cart=cart)

@app.route("/customer")
def customer():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("customer.html")

@app.route("/vendor")
def vendor():
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Cuisine_Type")
    cuisines = cursor.fetchall()
    cursor.execute("SELECT * FROM Dietary")
    dietary_tags = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("vendor.html", cuisines=cuisines, dietary_tags=dietary_tags)

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
    if "user_id" not in session:
        return redirect("/login")
    return render_template("review.html", product_id=product_id)

def add_product_to_db(vendor_id, cuisine_type_id, prod_name, prod_description, price, stock_quantity):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Product
        (vendor_id, cuisine_type_id, prod_name, prod_description, price, availability, stock_quantity, storytelling)
        OUTPUT INSERTED.product_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (vendor_id, cuisine_type_id, prod_name, prod_description, price, 1, stock_quantity, "Added from website"))

    product_id = cursor.fetchone()[0]
    conn.commit()

    cursor.close()
    conn.close()
    return product_id

def add_review_to_db(rating, comments, user_id, product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Review (rating, comments, user_id, product_id)
        VALUES (?, ?, ?, ?)
    """, (rating, comments, user_id, product_id))

    conn.commit()
    cursor.close()
    conn.close()

@app.route("/add_products", methods=["POST"])
def add_products():
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    product_id = add_product_to_db(
        session["vendor_id"],
        request.form["cuisine_type_id"],
        request.form["prod_name"],
        request.form["prod_description"],
        request.form["price"],
        request.form["stock_quantity"]
    )

    dietary_ids = request.form.getlist("dietary_tags")

    if dietary_ids:
        conn = get_connection()
        cursor = conn.cursor()
        for tag_id in dietary_ids:
            cursor.execute(
                "INSERT INTO Product_Dietary (product_id, tag_id) VALUES (?, ?)",
                (product_id, tag_id)
            )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect("/products")

@app.route("/write_review", methods=["POST"])
def write_review():
    add_review_to_db(
        int(request.form["rating"]),
        request.form["comments"],
        int(request.form["user_id"]),
        int(request.form["product_id"])
    )
    return redirect("/customer")

@app.route("/add_cart", methods=["POST"])
def add_cart():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT cart_id FROM Cart WHERE user_id = ?", (session["user_id"],))
    cart = cursor.fetchone()

    if not cart:
        cursor.execute("INSERT INTO Cart (user_id) VALUES (?)", (session["user_id"],))
        conn.commit()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        cart_id = cursor.fetchone()[0]
    else:
        cart_id = cart[0]

    cursor.execute("""
        INSERT INTO Cart_Item (cart_id, product_id, quantity)
        VALUES (?, ?, ?)
    """, (cart_id, request.form["product_id"], request.form["quantity"]))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/cart")

@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT cart_id FROM Cart WHERE user_id = ?", (session["user_id"],))
    cart = cursor.fetchone()
    if not cart:
        return redirect("/cart")

    cart_id = cart[0]

    cursor.execute("""
        SELECT p.product_id, ci.quantity, p.price
        FROM Cart_Item ci
        JOIN Product p ON ci.product_id = p.product_id
        WHERE ci.cart_id = ?
    """, (cart_id,))
    items = cursor.fetchall()

    total = sum(item[1] * item[2] for item in items)

    cursor.execute("""
        INSERT INTO Order_Info (order_date, total_amount, user_id)
        VALUES (GETDATE(), ?, ?)
    """, (total, session["user_id"]))
    conn.commit()

    cursor.execute("SELECT SCOPE_IDENTITY()")
    order_id = cursor.fetchone()[0]

    for item in items:
        cursor.execute("""
            INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase)
            VALUES (?, ?, ?, ?)
        """, (order_id, item[0], item[1], item[2]))

    cursor.execute("DELETE FROM Cart_Item WHERE cart_id = ?", (cart_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/payment/{order_id}")

@app.route("/payment/<int:order_id>")
def payment(order_id):
    return render_template("payment.html", order_id=order_id)

@app.route("/process_payment", methods=["POST"])
def process_payment():
    return redirect(f"/order_confirm/{request.form['order_id']}")

@app.route("/order_confirm/<int:order_id>")
def order_confirm(order_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.prod_name, oi.quantity, oi.price_at_purchase
        FROM Order_Item oi
        JOIN Product p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """, (order_id,))

    order_items = cursor.fetchall()
    total = sum(item[1] * item[2] for item in order_items)

    cursor.close()
    conn.close()

    return render_template("order.html", order_items=order_items, total=round(total, 2))

if __name__ == "__main__":
    app.run(debug=True)