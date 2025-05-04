from flask import Flask, request, render_template
from twilio.rest import Client
from flask_pymongo import PyMongo
from urllib.parse import quote_plus  # ✅ Correct import
import os

app = Flask(__name__)

# MongoDB Configuration
mongo_username = os.getenv("MONGO_USERNAME")
mongo_password = os.getenv("MONGO_PASSWORD")
encoded_username = quote_plus(mongo_username or "")
encoded_password = quote_plus(mongo_password or "")

app.config["MONGO_URI"] = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster0.6wjy4p3.mongodb.net/nikhil?retryWrites=true&w=majority"
mongo = PyMongo(app)

# Twilio Configuration
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")
FROM_PHONE = os.getenv("TWILIO_FROM")
TO_PHONE = os.getenv("TWILIO_TO")

client = Client(account_sid, auth_token)

PICKLE_INFO = {
    'KF': ('King Fish', 120),
    'KFP': ('King Fish Pulusu', 110),
    'TN': ('Tuna', 130),
    'PSN': ('Prawns Small Non-Spicy', 140),
    'JDM': ('Jalebi Dry Mango', 125),
    'HS': ('Hilsa', 100),
    'PR': ('Prawns Regular', 150),
    'MR': ('Mackerel', 135),
    'SFP': ('Sankara Fish Pulusu', 115),
    'KMP': ('Katla Mustard Pulusu', 160)
}

@app.route('/')
def home():
    return render_template('english.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    phone = request.form.get('phone')
    landmark = request.form.get('landmark')
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    pickles_input = request.form.get('pickles')
    total_cost = 0
    pickle_lines = []

    if pickles_input:
        for line in pickles_input.strip().split('\n'):
            try:
                line = line.replace('•', '').strip()
                if not line:
                    continue
                item_name, qty = line.split(':')
                code = item_name.strip().upper().split()[0]
                qty = int(qty.strip().split()[0])
                full_name, price = PICKLE_INFO.get(code, ('Unknown', 100))
                cost = price * qty
                total_cost += cost
                pickle_lines.append(f"{full_name} ({code}) x {qty} = ₹{cost}")
            except Exception as e:
                print(f"⚠️ Failed to parse line: '{line}' | Error: {e}")

    sms_message = "\n".join([
        f"🥒 Pickle Order from {name}",
        f"📞 {phone}",
        f"🏠 Landmark: {landmark}",
        f"📍 Address: {address}",
        f"📮 Pincode: {pincode}",
        "",
        "🧴 Items Ordered:"
    ] + pickle_lines + [
        "",
        f"💰 Total: ₹{total_cost}"
    ])

    try:
        # Uncomment if SMS sending is needed
        # client.messages.create(body=sms_message, from_=FROM_PHONE, to=TO_PHONE)

        order_data = {
            "name": name,
            "phone": phone,
            "landmark": landmark,
            "address": address,
            "pincode": pincode,
            "pickles": pickle_lines,
            "total_cost": total_cost
        }
        order_id = mongo.db.fish.insert_one(order_data).inserted_id
        print(f"✅ Order saved with ID: {order_id}")

        return render_template('thank_you.html', name=name, pickle_lines=pickle_lines, total_cost=total_cost)
    except Exception as e:
        print("❌ Failed:", e)
        return f"<h2>Order Failed 😢</h2><p>Error: {e}</p>"

if __name__ == '__main__':
    app.run(debug=False)
