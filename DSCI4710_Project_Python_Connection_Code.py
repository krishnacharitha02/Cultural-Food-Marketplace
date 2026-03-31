import mysql.connector

def get_users(cursor):
    cursor.execute("SELECT * FROM Users")
    return cursor.fetchall()

def get_all_products(cursor):
    cursor.execute("SELECT * FROM Product")
    return cursor.fetchall()

def get_products_by_cuisine(cursor, cuisine_name):
    query = """
    SELECT p.prod_name, c.cuisine_name
    FROM Product p
    JOIN Cuisine_Type c
        ON p.cuisine_type_id = c.cuisine_type_id
    WHERE c.cuisine_name = %s
    """
    cursor.execute(query, (cuisine_name,))
    return cursor.fetchall()

def get_products_by_dietary(cursor, tag_name):
    query = """
    SELECT p.prod_name, d.tag_name
    FROM PRoduct p
    JOIN Product_Dietary pd
        ON p.product_id = pd.product_id
    JOIN Dietary d
        ON pd.tag_id = d.tag_id
    WHERE d.tag_name = %s
    """
    cursor.execute(query, (tag_name,))
    return cursor.fetchall()

def get_trending_products(cursor):
    query = """
    SELECT p.prod_name, SUM(oi.quantity) AS total_orders
    FROM Order_Item oi
    JOIN Product p
        ON oi.product_id = p.product_id
    GROUP BY p.product_id, p.prod_name
    ORDER BY total_orders DESC
    """
    cursor.execute(query)
    return cursor.fetchall()

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    passwd="USG26@ohcwy11",
    database="cultural_food_marketplace"
)

cursor = conn.cursor()

# BASIC TESTS
print("===USERS===")
for row in get_users(cursor):
    print(row)

print("\n===ALL PRODUCTS===")
for row in get_all_products(cursor):
    print(row)

#  ADVANCED TESTS
print("\n===PRODUCTS BY CUISINE (Indian)===")
for row in get_products_by_cuisine(cursor, "Indian"):
    print(row)

print("\n===PRODUCTS BY DIETARY (Vegetarian)===")
for row in get_products_by_dietary(cursor, "Vegetarian"):
    print(row)

print("\n===TRENDING PRODUCTS===")
for row in get_trending_products(cursor):
    print(row)

cursor.close()
conn.close()