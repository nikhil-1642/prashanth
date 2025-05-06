from flask import Flask, request, render_template
from twilio.rest import Client
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# MongoDB setup
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Twilio config
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")
whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")
whatsapp_to = os.getenv("WHATSAPP_TO")
client = Client(account_sid, auth_token)

# Pickle price data
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

    # Send WhatsApp message
    order_message = (
        f"New Order Received!\n"
        f"Name: {name}\n"
        f"Phone: {phone}\n"
        f"Landmark: {landmark}\n"
        f"Address: {address}\n"
        f"Pincode: {pincode}\n"
        f"Total: ₹{total_cost}\n"
        f"Items:\n" + "\n".join(pickle_lines)
    )

    try:
        message = client.messages.create(
            body=order_message,
            from_=whatsapp_from,
            to=f"whatsapp:{whatsapp_to}"  # Use the phone number input by the user
        )
        print('✅ WhatsApp message sent! SID:', message.sid)

        # Save to MongoDB
        mongo.db.fish.insert_one({
            "name": name,
            "phone": phone,
            "landmark": landmark,
            "address": address,
            "pincode": pincode,
            "pickles": pickle_lines,
            "total_cost": total_cost
        })

        return render_template('thank_you.html', name=name, pickle_lines=pickle_lines, total_cost=total_cost)

    except Exception as e:
        print("❌ Order failed:", e)
        return f"<h2>Order Failed 😢</h2><p>Error: {e}</p>"

if __name__ == '__main__':
    app.run(debug=False)
