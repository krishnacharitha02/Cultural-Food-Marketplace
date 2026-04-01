#CREATING DATABASE
CREATE DATABASE cultural_food_marketplace; 
USE cultural_food_marketplace; 

#CREATING TABLES 
#User 
CREATE TABLE Users (user_id INT auto_increment PRIMARY KEY, user_name varchar(100), email varchar(100), acc_password varchar(100), address varchar(250));

#Cuisine Type
create table Cuisine_Type (cuisine_type_id INT auto_increment PRIMARY KEY, cuisine_name varchar(100), region varchar(100));

#Dietary
create table Dietary (tag_id int auto_increment PRIMARY KEY, tag_name VARCHAR(100));

#Vendor
create table Vendor (vendor_id INT auto_increment PRIMARY KEY, business_name varchar(150), cuisine_type_id INT, location varchar(100), contact_info_phone varchar(20), contact_info_email varchar(100), foreign key (cuisine_type_id) references Cuisine_Type(cuisine_type_id));

#Product
create table Product (product_id int auto_increment primary key, vendor_id INT, cuisine_type_id INT, prod_name varchar(100), prod_description text, price decimal(6,2), availability boolean, stock_quantity int, storytelling text, foreign key (vendor_id) references Vendor(vendor_id), foreign key (cuisine_type_id) references Cuisine_Type(cuisine_type_id));

#Cart
create table Cart (cart_id int auto_increment primary key, user_id int, foreign key (user_id) references Users(user_id));

#Order_Info
create table Order_Info (order_id int auto_increment primary key, order_date DATE, total_amount decimal(8,2), user_id INT, foreign key (user_id) references Users(user_id));

#Review 
create table Review (review_id int auto_increment primary key, rating int, comments TEXT, user_id INT, product_id INT, foreign key (user_id) references Users(user_id), foreign key (product_id) references Product(product_id));

#ProductDietary 
create table Product_Dietary(product_id INT, tag_id INT, primary key (product_id, tag_id), foreign key (product_id) references Product(product_id), foreign key (tag_id) references Dietary(tag_id));

#CartItem
create table Cart_Item(cart_item_id INT auto_increment primary key, cart_id INT, product_id int, quantity int, foreign key (cart_id) references Cart(cart_id), foreign key (product_id) references Product(product_id));

#Order Item
create table Order_Item (order_item_id INT auto_increment primary key, order_id int, product_id int, quantity int, price_at_purchase decimal(6,2), foreign key (order_id) references Order_Info(order_id), foreign key (product_id) references Product(product_id));


#INSERTING SAMPLE DATA
 #Users 
 insert into Users (user_name, email, acc_password, address) values ('Avery', 'avery04@gmail.com', 'av0234', 'Texas'), ('Xander', 'xander@gmail.com', 'xanny75', 'New York'), ('Jin', 'jink@gmail.com', 'jinpanda', 'California');
 #Cuisine Type 
 insert into Cuisine_Type (cuisine_name, region) values ('Indian', 'South Asia'), ('Korean', 'East Asia'), ('Italian', 'Europe'), ('Mexican', 'Latin America');
 #Vendor 
 insert into Vendor(business_name, cuisine_type_id, location, contact_info_phone, contact_info_email) values ('Spice Corner', 1, 'Marietta', '4041245896', 'spicecorner@gmal.com'), ('Local Pasta Place', 2, 'San Jose', '987654623', 'localpastaplace@gmail.com');
 #Dietary
 insert into Dietary (tag_name) values ('Vegetarian'), ('Halal'), ('Gluten-Free');
 #Product
 insert into Product(vendor_id, cuisine_type_id, prod_name, prod_description, price, availability, stock_quantity, storytelling) values (1,1, 'Paneer Tikka Masala', 'Grilled paneer in rich tomato-based gravy', 12.99, TRUE, 10, 'Popular Indian vegetarian dish'), (2,2, 'Margherita Pizza', 'Classic Pizza', 9.99, TRUE, 20, 'Originated in Italy');
 #Cart
 insert into Cart (user_id) values (1), (2);
 #Cart Item
 insert into Cart_Item (cart_id, product_id, quantity) values (1,1,2), (1,2,1);
 #Order
 insert into Order_Info (order_date, total_amount, user_id) values ('2026-03-01', 25.98, 1);
 #Order Item 
 insert into Order_Item (order_id, product_id, quantity, price_at_purchase) values (1,1,2,12.99);
 #Review 
 insert into Review (rating, comments, user_id, product_id) values (5, 'Amazing taste!', 1,1), (4, 'Very good', 2,2);
 #Product Dietary
 insert into Product_Dietary (product_id, tag_id) values (1,1), (2,3);
 
 #SHOWING TABLES 
 select * from Users;
 select * from Vendor;
 select * from Cuisine_Type;
 select * from Dietary;
 select * from Product;
 select * from Cart;
 select * from Order_Info;
 select * from Review;
 select * from Product_Dietary;
 select * from Order_Item;
 select * from Cart_Item;
 
 #ADVANCED QUERIES 
 #Filtering by Dietary
 select p.prod_name, d.tag_name from Product p join Product_Dietary pd ON p.product_id = pd.product_id join Dietary d ON pd.tag_id = d.tag_id where d.tag_name = 'Vegetarian';
 #Filtering by cuisine
 select p.prod_name, c.cuisine_name from Product p join Cuisine_Type c on p.cuisine_type_id = c.cuisine_type_id where c.cuisine_name = 'Indian';
 #Trending popular products
 select p.prod_name, SUM(oi.quantity) as total_orders from Order_Item oi join Product p on oi.product_id = p.product_id group by p.product_id order by total_orders desc;
 #Products with vendor info
 select p.prod_name, v.business_name, p.price from Product p join Vendor v on p.vendor_id = v.vendor_id;
 #Total spending per user
 select u.user_name, SUM(o.total_amount) as total_spent from Order_Info o join Users u on o.user_id = u.user_id group by u.user_name;
 
 
 

