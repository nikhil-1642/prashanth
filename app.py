from flask import Flask, request, jsonify, send_from_directory, session, redirect
from functools import wraps
import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder='.', static_url_path='')
  # Replace with a secure random key
app.secret_key = os.getenv("SECRET_KEY", "fallback-key")
# ------------------- Helpers -------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api") or request.is_json:
                return jsonify({"success": False, "message": "Not logged in"}), 401
            return redirect("/index.html")
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            auth_plugin='mysql_native_password'
        )


    except Error as e:
        print("Error connecting to MySQL:", e)
        return None

def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

# ------------------- Static Routes -------------------
@app.route("/get_cart", methods=["GET"])
@login_required
def get_cart():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM cart")
        return jsonify({"success": True, "cart": cursor.fetchall()})
    except Exception as e:
        print("Error fetching cart:", e)
        return jsonify({"success": False, "message": "Failed to load cart"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/remove_cart_item", methods=["POST"])
@login_required
def remove_cart_item():
    data = request.get_json()
    item_id = data.get("id")

    if not item_id:
        return jsonify({"success": False, "message": "Invalid item ID"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cart WHERE id = %s", (item_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Error removing cart item:", e)
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/place_order_from_cart', methods=['POST'])
@login_required
def place_order_from_cart():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get all cart items for the user
        cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400

        # Process each cart item into individual orders
        for item in cart_items:
            cursor.execute("""
                INSERT INTO orders (user_id, pickles, quantity, cost, status)
                VALUES (%s, %s, %s, %s, 'Ordered')
            """, (
                user_id,
                item["pickle_name"],
                item["quantity"],
                item["cost"]
            ))

        # Clear the cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        conn.commit()

        return jsonify({'success': True, 'redirect': '/Thank.html'})

    except Exception as e:
        print("Error in /place_order_from_cart:", e)
        return jsonify({'success': False, 'message': 'Database error'}), 500

    finally:
        cursor.close()
        conn.close()



@app.route("/")
@app.route("/index.html")
def index():
    return send_from_directory(os.getcwd(), "index.html")

@app.route("/demo.html")
@login_required
def demo():
    return send_from_directory(os.getcwd(), "demo.html")

@app.route("/Thank.html")
@login_required
def thank_page():
    return send_from_directory(os.getcwd(), "Thank.html")

@app.route("/order_info.html")
def order_info():
    return send_from_directory(os.getcwd(), "order_info.html")

@app.route("/your_orders.html")
@login_required
def your_orders_page():
    return send_from_directory(os.getcwd(), "your_orders.html")

@app.route("/cart.html")
@login_required
def cart_page():
    return send_from_directory(os.getcwd(), "cart.html")

@app.route("/edit_profile.html")
def edit_profile():
    return send_from_directory(os.getcwd(), "edit_profile.html")

# ------------------- Auth APIs -------------------
@app.route('/edit_profile_user', methods=['GET', 'POST'])
@login_required
def edit_profile_user():
    if request.method == 'POST':
        # handle form data update here
        name = request.form['name']
        email = request.form['email']
        # Update database...
        return redirect('/some_page')

    return send_from_directory(os.getcwd(),'edit_profile_user.html')
@app.route('/demo')
@login_required
def demo_page():
    return send_from_directory(os.getcwd(), 'demo.html')

# ------------------- Cart APIs -------------------

@app.route("/add_to_cart_test", methods=["POST"])
@login_required
def add_to_cart_test():
    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO cart (user_id, pickles, quantity, cost) VALUES (%s, %s, %s, %s)",
            (user_id, "Test Pickle", 1, 100)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "DB error"}), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json()
    items = data.get("items", [])

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for item in items:
            pickle_name = item.get("pickle_name")
            quantity = item.get("quantity")
            cost = item.get("cost")

            if not pickle_name or not quantity or not cost:
                continue  # skip invalid

            cursor.execute(
                "INSERT INTO cart (user_id, pickle_name, quantity, cost) VALUES (%s, %s, %s, %s)",
                (user_id, pickle_name, quantity, cost)
            )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Error adding to cart:", e)
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route("/login", methods=["POST"])

def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and verify_password(user["password"], password):
        session.permanent = True
        session["user_id"] = user["id"]
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid credentials"})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Email already exists"})

    hashed_pw = hash_password(password)
    cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_pw))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})

# ------------------- Owner Login & Password Update -------------------
@app.route('/buy_now', methods=['POST'])
@login_required
def buy_now():
    data = request.get_json()
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    # Accept single item or list of items
    if isinstance(data, dict) and "items" not in data:
        items = [data]  # Single item passed from frontend
    else:
        items = data.get("items", [])

    if not items:
        return jsonify({'success': False, 'message': 'No items received'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500

    cursor = conn.cursor()
    try:
        for item in items:
            cursor.execute("""
                INSERT INTO orders (user_id, pickles, quantity, cost, status)
                VALUES (%s, %s, %s, %s, 'Ordered')
            """, (
                user_id,
                item["pickle_name"],
                item["quantity"],
                item["cost"]
            ))
        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        print("Error in /buy_now:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/owner-login", methods=["POST"])

def owner_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM owners WHERE email = %s", (email,))
    owner = cursor.fetchone()
    cursor.close()
    conn.close()

    if owner and verify_password(owner["password"], password):
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid credentials"})

@app.route("/owner-update-password", methods=["POST"])
def owner_update_password():
    data = request.get_json()
    email = data.get("email")
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM owners WHERE email = %s", (email,))
    owner = cursor.fetchone()

    if not owner:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Email not found"})

    if not verify_password(owner["password"], current_password):
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Current password is incorrect"})

    hashed_new_password = hash_password(new_password)
    cursor.execute("UPDATE owners SET password = %s WHERE email = %s", (hashed_new_password, email))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})



@app.route("/get-orders", methods=["GET"])
def get_all_orders():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "orders": orders})

@app.route("/get-orders1", methods=["GET"])
@login_required
def get_user_orders():
    user_id = session["user_id"]

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC", (user_id,))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "orders": orders})

@app.route("/cancel-order", methods=["POST"])

@login_required
def cancel_order():
    user_id = session["user_id"]
    data = request.get_json()
    order_id = data.get("id")

    if not order_id:
        return jsonify({"success": False, "message": "Order ID missing"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Order not found"}), 404
        if row[0] != user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Error cancelling order:", e)
        return jsonify({"success": False, "message": "Failed to cancel order"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/update-order-status", methods=["POST"])

def update_order_status():
    data = request.get_json()
    order_id = data.get("id")
    status = data.get("status")

    if order_id is None or status is None:
        return jsonify({"success": False, "message": "Invalid data"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print("Error updating order status:", e)
        return jsonify({"success": False, "message": "Failed to update status"}), 500
    finally:
        cursor.close()
        conn.close()
# ------------------- Profile APIs -------------------

@app.route("/get-profile", methods=["GET"])
@login_required
def get_profile():
    user_id = session["user_id"]
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "User not found"}), 404


@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    data = request.get_json()
    name = data.get("name", "").strip()
    current_password = data.get("currentPassword", "").strip()
    new_password = data.get("newPassword", "").strip()

    user_id = session["user_id"]

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "User not found"}), 404

    if new_password:
        # Changing password requires current password validation
        if not current_password:
            return jsonify({"success": False, "message": "Current password is required"}), 400
        if not verify_password(user["password"], current_password):
            return jsonify({"success": False, "message": "Current password is incorrect"}), 403
        hashed_new_pw = hash_password(new_password)
        cursor.execute("UPDATE users SET name = %s, password = %s WHERE id = %s", (name, hashed_new_pw, user_id))
    else:
        # Just update name
        cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})
# ------------------- Run App -------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)






