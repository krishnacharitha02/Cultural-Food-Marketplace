from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        passwd="TeensDatabase-02",
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



if __name__ == "__main__":
    app.run(debug=True)