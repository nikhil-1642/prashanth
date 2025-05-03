import os
from flask import Flask, request, render_template
from twilio.rest import Client
from flask_pymongo import PyMongo
from urllib.parse import quote_plus

app = Flask(__name__)

# MongoDB Configuration (use environment variables)
username = os.environ.get("MONGO_USERNAME")
password = os.environ.get("MONGO_PASSWORD")
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)

app.config["MONGO_URI"] = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster0.6wjy4p3.mongodb.net/nikhil?retryWrites=true&w=majority"
mongo = PyMongo(app)

# Twilio Configuration (use environment variables)
account_sid = os.environ.get("TWILIO_SID")
auth_token = os.environ.get("TWILIO_AUTH")
FROM_PHONE = os.environ.get("TWILIO_FROM")
TO_PHONE = os.environ.get("TWILIO_TO")

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
                code = item_name.strip().upper().split()[0]  # Assume code is the first word
                qty = int(qty.strip().split()[0])
                full_name, price = PICKLE_INFO.get(code, ('', 100))
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
        # Sending SMS using Twilio (uncomment this when you're ready to send SMS)
        # message = client.messages.create(
        #     body=sms_message,
        #     from_=FROM_PHONE,
        #     to=TO_PHONE
        # )

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
    app.run(debug=True)
