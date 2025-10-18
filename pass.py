import mysql.connector
from werkzeug.security import generate_password_hash

# --- DB Connection ---
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",  # change if needed
    database="nikhil1"
)
cursor = conn.cursor()

# --- Owner Info ---
name = "nikhil"
email = "paterinikhil0888@gmail.com"
raw_password = "nikhil@1642"

# --- Hash the password ---
hashed_pw = generate_password_hash(raw_password)

# --- Insert or Update Owner ---
try:
    cursor.execute("""
        INSERT INTO owners (name, email, password)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            password = VALUES(password)
    """, (name, email, hashed_pw))
    
    conn.commit()
    print("✅ Owner inserted or updated successfully.")
except mysql.connector.Error as err:
    print("❌ Error:", err)

# --- Cleanup ---
cursor.close()
conn.close()
