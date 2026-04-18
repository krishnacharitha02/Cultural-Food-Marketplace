# Cultural Food Marketplace 
A full-stack database-driven web application that allows users to browse, purchase, and review culturally diverse food products, while enabling vendors to manage product listings, cuisine types, and dietary categories. 

---

## Project Overview
The **Cultural Food Marketplace** is a Flask-based web application connected to a cloud-hosted Azure SQL database. It connects customers and vendors on a single platform where users can explore culturally diverse cuisines, apply dietary filters, manage carts, and place orders. 
Vendors can add products, define cuisine and dietary categories, and manage inventory, making the platform a complete marketplace system. 

---

## Key Features
### Customer Features
- User registration and login system
- Browse products by cuisine type
- Filter products by dietary preferences (Vegan, Vegetarian, Halal, Gluten-Free, etc.)
- Add products to cart
- Place orders and view order confirmation
- Purchase history tracking

### Vendor Features
- Vendor registration and login
- Add new products with cuisine and dietary tags
- Delete product listings
- Manage cuisine types and dietary categories

### System Features
- Session-based authentication
- Dynamic SQL queries with JOINs and filters
- Cart and order management system
- Real-time product updates

---

## System Architecture 
The application follows a **three-tier architecture**:

1. **Frontend:** HTML templates rendered using Flask (Jinja2)
2. **Backend:** Flask routes handling application logic
3. **Database:** Azure SQL Database for persistent storage

User actions trigger Flask routes, which execute SQL queries and return dynamically rendered HTML pages.

---

## How to Run the Project
```bash
git clone https://github.com/krishnacharitha02/Cultural-Food-Marketplace.git
cd Cultural-Food-Marketplace

pip install flask pyodbc

python app.py
```
Then open:  http://127.0.0.1:5000/

