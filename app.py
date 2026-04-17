from flask import Flask, render_template, request, redirect, session, url_for, flash
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


def get_products(dietary_tag=None, cuisine_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT DISTINCT p.*, v.business_name, ct.cuisine_name
    FROM Product p
    JOIN Vendor v ON p.vendor_id = v.vendor_id
    JOIN Cuisine_Type ct ON p.cuisine_type_id = ct.cuisine_type_id
    """

    conditions = []
    params = []

    if dietary_tag:
        query += """
        JOIN Product_Dietary pd ON p.product_id = pd.product_id
        JOIN Dietary d ON pd.tag_id = d.tag_id
        """
        conditions.append("d.tag_name = ?")
        params.append(dietary_tag)

    if cuisine_id:
        conditions.append("p.cuisine_type_id = ?")
        params.append(cuisine_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)

    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products


def get_cart(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.prod_name, ci.quantity, ci.cart_item_id
    FROM Cart_Item ci
    JOIN Product p ON ci.product_id = p.product_id
    JOIN Cart c ON ci.cart_id = c.cart_id
    WHERE c.user_id = ?
    """
    cursor.execute(query, (user_id,))
    cart = cursor.fetchall()
    cursor.close()
    conn.close()
    return cart


def get_reviews(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.rating, r.comments, u.user_name, r.review_id, r.user_id
        FROM Review r
        JOIN Users u ON r.user_id = u.user_id
        WHERE r.product_id = ?
        ORDER BY r.review_id DESC
    """, (product_id,))
    reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    return reviews


def add_product_to_db(vendor_id, cuisine_type_id, prod_name, prod_description, price, stock_quantity, storytelling):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Product
        (vendor_id, cuisine_type_id, prod_name, prod_description, price, availability, stock_quantity, storytelling)
        OUTPUT INSERTED.product_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (vendor_id, cuisine_type_id, prod_name, prod_description, price, 1, stock_quantity, "Added from website"))

    row = cursor.fetchone()   
    product_id = row[0] if row else None

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


def add_cart_to_db(cart_id, product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Cart_Item (cart_id, product_id, quantity)
        VALUES (?, ?, ?)
    """, (cart_id, product_id, quantity))

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def home():
    try:
        users = get_users()
    except Exception:
        users = []
    return render_template("index.html", users=users)


@app.route("/products")
def products():
    dietary_tag = request.args.get("dietary")
    cuisine_id = request.args.get("cuisine")

    conn = get_connection()
    cursor = conn.cursor()

    if "vendor_id" in session:
        vendor_id = session["vendor_id"]

        query = """
        SELECT p.*, v.business_name, ct.cuisine_name
        FROM Product p
        JOIN Vendor v ON p.vendor_id = v.vendor_id
        JOIN Cuisine_Type ct ON p.cuisine_type_id = ct.cuisine_type_id
        WHERE p.vendor_id = ?
        """
        cursor.execute(query, (vendor_id,))

    else:
        if dietary_tag:
            query = """
            SELECT DISTINCT p.*, v.business_name, ct.cuisine_name
            FROM Product p
            JOIN Vendor v ON p.vendor_id = v.vendor_id
            JOIN Cuisine_Type ct ON p.cuisine_type_id = ct.cuisine_type_id
            JOIN Product_Dietary pd ON p.product_id = pd.product_id
            JOIN Dietary d ON pd.tag_id = d.tag_id
            WHERE d.tag_name = ?
            """
            cursor.execute(query, (dietary_tag,))

        elif cuisine_id:
            query = """
            SELECT DISTINCT p.*, v.business_name, ct.cuisine_name
            FROM Product p
            JOIN Vendor v ON p.vendor_id = v.vendor_id
            JOIN Cuisine_Type ct ON p.cuisine_type_id = ct.cuisine_type_id
            WHERE p.cuisine_type_id = ?
            """
            cursor.execute(query, (cuisine_id,))

        else:
            query = """
            SELECT p.*, v.business_name, ct.cuisine_name
            FROM Product p
            JOIN Vendor v ON p.vendor_id = v.vendor_id
            JOIN Cuisine_Type ct ON p.cuisine_type_id = ct.cuisine_type_id
            """
            cursor.execute(query)

    products = cursor.fetchall()

    cursor.execute("SELECT * FROM Cuisine_Type")
    cuisines = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("products.html", products=products, cuisines=cuisines)


@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login")

    cart_items = get_cart(session["user_id"])
    return render_template("cart.html", cart=cart_items)


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
        SELECT TOP 5 p.prod_name, SUM(oi.quantity) AS total_quantity
        FROM Order_Item oi
        JOIN Product p ON oi.product_id = p.product_id
        GROUP BY p.prod_name
        ORDER BY total_quantity DESC
    """)
    recs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("recommend.html", recs=recs)


@app.route("/review/<int:product_id>")
def review(product_id):
    if "user_id" not in session:
        return redirect("/login")
    reviews = get_reviews(product_id)
    return render_template("review.html", product_id=product_id, reviews=reviews)


@app.route("/add_product", methods=["POST"])
def add_products():
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    prod_name = request.form["prod_name"]
    prod_description = request.form["prod_description"]
    price = request.form["price"]
    stock_quantity = request.form["stock_quantity"]
    cuisine_type_id = request.form["cuisine_type_id"]
    dietary_ids = request.form.getlist("dietary_tags")
    storytelling = request.form.get("storytelling")

    product_id = add_product_to_db(
        session["vendor_id"],
        cuisine_type_id,
        prod_name,
        prod_description,
        price,
        stock_quantity,
        storytelling
    )

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
    
    flash("Product added successfully!")

    return redirect("/vendor")


@app.route("/write_review", methods=["POST"])
def write_review():
    if "user_id" not in session:
        return redirect("/login")

    rating = request.form["rating"]
    comments = request.form["comments"]
    product_id = request.form["product_id"]
    user_id = session["user_id"]

    add_review_to_db(rating, comments, user_id, product_id)
    return redirect(f"/review/{product_id}")


@app.route("/add_cart", methods=["POST"])
def add_cart():
    if "user_id" not in session:
        return redirect("/login")

    try:
        user_id = session["user_id"]
        product_id = request.form.get("product_id")
        quantity = request.form.get("quantity")

        if not quantity or int(quantity) <= 0:
            return "Please enter a quantity greater than 0", 400

        quantity = int(quantity)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT cart_id FROM Cart WHERE user_id = ?", (user_id,))
        cart = cursor.fetchone()

        if not cart:
            cursor.execute("INSERT INTO Cart (user_id) VALUES (?)", (user_id,))
            conn.commit()
            cursor.execute("SELECT SCOPE_IDENTITY()")
            cart_id = int(cursor.fetchone()[0])
        else:
            cart_id = cart[0]

        cursor.execute("""
            INSERT INTO Cart_Item (cart_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (cart_id, product_id, quantity))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/cart")

    except Exception as e:
        print("ADD TO CART ERROR:", e)
        return "Failed to add item to cart", 500


@app.route("/delete_cart_item/<int:cart_item_id>", methods=["POST"])
def delete_cart_item(cart_item_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Cart_Item
        WHERE cart_item_id = ?
          AND cart_id = (SELECT cart_id FROM Cart WHERE user_id = ?)
    """, (cart_item_id, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/cart")


@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect("/login")

    try:
        user_id = session["user_id"]
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT cart_id FROM Cart WHERE user_id = ?", (user_id,))
        cart = cursor.fetchone()

        if not cart:
            cursor.close()
            conn.close()
            return redirect("/cart")

        cart_id = cart[0]

        cursor.execute("""
            SELECT p.product_id, ci.quantity, p.price
            FROM Cart_Item ci
            JOIN Product p ON ci.product_id = p.product_id
            WHERE ci.cart_id = ?
        """, (cart_id,))
        items = cursor.fetchall()

        if not items:
            cursor.close()
            conn.close()
            return redirect("/cart")

        total = sum(item[1] * item[2] for item in items)

        cursor.execute("""
            INSERT INTO Order_Info (order_date, total_amount, user_id)
            OUTPUT INSERTED.order_id
            VALUES (GETDATE(), ?, ?)
        """, (total, user_id))

        order_id = cursor.fetchone()[0]

        for item in items:
            product_id = item[0]
            quantity = item[1]
            price = item[2]

            cursor.execute("""
                INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase)
                VALUES (?, ?, ?, ?)
            """, (order_id, product_id, quantity, price))

        cursor.execute("DELETE FROM Cart_Item WHERE cart_id = ?", (cart_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(f"/payment/{order_id}")

    except Exception as e:
        print("ERROR:", repr(e))
        return "Order failed - check terminal"

@app.route("/order_confirm/<int:order_id>")
def order_confirm(order_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT total_amount, order_date
        FROM Order_Info
        WHERE order_id = ?
    """, (order_id,))
    order = cursor.fetchone()

    cursor.execute("""
        SELECT p.prod_name, oi.quantity, oi.price_at_purchase
        FROM Order_Item oi
        JOIN Product p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """, (order_id,))
    order_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("order_confirm.html", order=order, order_items=order_items)


@app.route("/register_user", methods=["GET", "POST"])
def register_user():
    if request.method == "GET":
        return render_template("register.html")

    user_name = request.form["user_name"]
    email = request.form["email"]
    password = request.form["password"]
    address = request.form["address"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Users (user_name, email, acc_password, address)
        VALUES (?, ?, ?, ?)
    """, (user_name, email, password, address))
    conn.commit()

    cursor.execute("SELECT SCOPE_IDENTITY()")
    user_id = int(cursor.fetchone()[0])

    cursor.execute("INSERT INTO Cart (user_id) VALUES (?)", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login_user():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, user_name
        FROM Users
        WHERE email = ? AND acc_password = ?
    """, (email, password))

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session["user_id"] = user[0]
        session["user_name"] = user[1]
        return redirect("/customer")
    else:
        return "Invalid email or password"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register_vendor", methods=["GET", "POST"])
def register_vendor():
    if request.method == "GET":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Cuisine_Type")
        cuisines = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("vendor_register.html", cuisines=cuisines)

    business_name = request.form["business_name"]
    cuisine_type_id = request.form["cuisine_type_id"]
    location = request.form["location"]
    phone = request.form["phone"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Vendor
        (business_name, cuisine_type_id, location, contact_info_phone, contact_info_email, vendor_password)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (business_name, cuisine_type_id, location, phone, email, password))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/vendor_login")


@app.route("/vendor_login", methods=["GET", "POST"])
def login_vendor():
    if request.method == "GET":
        return render_template("vendor_login.html")

    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT vendor_id, business_name
        FROM Vendor
        WHERE contact_info_email = ? AND vendor_password = ?
    """, (email, password))

    vendor = cursor.fetchone()
    cursor.close()
    conn.close()

    if vendor:
        session["vendor_id"] = vendor[0]
        session["business_name"] = vendor[1]
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

    cursor.execute("DELETE FROM Product_Dietary WHERE product_id = ?", (product_id,))
    conn.commit()

    cursor.execute("""
        DELETE FROM Product
        WHERE product_id = ? AND vendor_id = ?
    """, (product_id, vendor_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/vendor")


@app.route("/delete_review/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Review
        WHERE review_id = ? AND user_id = ?
    """, (review_id, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/customer")


@app.route("/add_cuisine", methods=["POST"])
def add_cuisine():
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    cuisine_name = request.form["cuisine_name"]
    region = request.form["region"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Cuisine_Type (cuisine_name, region) VALUES (?, ?)", (cuisine_name, region))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/vendor")


@app.route("/add_dietary", methods=["POST"])
def add_dietary():
    if "vendor_id" not in session:
        return redirect("/vendor_login")

    tag_name = request.form["tag_name"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Dietary (tag_name) VALUES (?)", (tag_name,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/vendor")


@app.route("/payment/<int:order_id>")
def payment(order_id):
    if "user_id" not in session:
        return redirect("/login")
    return render_template("payment.html", order_id=order_id)


@app.route("/process_payment", methods=["POST"])
def process_payment():
    order_id = request.form["order_id"]
    return redirect(f"/order_confirm/{order_id}")


print(app.url_map)

if __name__ == "__main__":
    app.run(debug=True)