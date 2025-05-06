from flask import Flask, request, render_template
from twilio.rest import Client
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# ✅ Use full MongoDB URI from environment variable
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# ✅ Twilio setup using env vars
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")
FROM_PHONE = os.getenv("TWILIO_FROM")  # e.g., +14155238886 (Twilio sandbox)
TO_PHONE = os.getenv("TWILIO_TO")
whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
whatsapp_to = os.getenv('WHATSAPP_TO')  # e.g., +91XXXXXXXXXX (your WhatsApp number)
client = Client(account_sid, auth_token)

# ✅ Pickle price list
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

    # ✅ Parse pickle input
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

    # ✅ Compose a shortened message (limit to 3 items)
    max_items = 3
    pickle_summary = "\n".join(pickle_lines[:max_items])
    if len(pickle_lines) > max_items:
        pickle_summary += "\n+ More items..."

    sms_message = f"Order from {name}: ₹{total_cost} | {pickle_summary}"

    try:
        # ✅ Send SMS
        sms = client.messages.create(
            body=sms_message,
            from_=FROM_PHONE,
            to=TO_PHONE
        )
        print(f"✅ SMS sent with SID: {sms.sid}")

        # ✅ Send WhatsApp message
        message = client.messages.create(
            body=sms_message,
            from_=whatsapp_from,
            to=whatsapp_to
        )
        print('✅ Message sent! SID:', message.sid)

        # ✅ Save to MongoDB
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
        print("❌ Failed to send message or save order:", e)
        return f"<h2>Order Failed 😢</h2><p>Error: {e}</p>"

if __name__ == '__main__':
    app.run(debug=False)
