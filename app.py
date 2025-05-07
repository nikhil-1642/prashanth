from flask import Flask, request, render_template
from twilio.rest import Client
from flask_pymongo import PyMongo
import os

app = Flask(__name__)

# MongoDB setup
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Twilio setup
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH")
whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")  # +14155238886
whatsapp_to = os.getenv("WHATSAPP_TO")             # e.g., +919390286430
client = Client(account_sid, auth_token)

# Pickle info with short codes
PICKLE_INFO = {
    'RFP': ('Rohu Fish Pickle', 900),
    'PR': ('Prawns Pickles', 1200),
    'MFP': ('Murrel Fish Pickle', 1200),
    'CP': ('Chicken Pickle', 850),
    'CBP': ('Chicken Boneless Pickle', 900),
    'MP': ('Mutton Pickle', 1200),
    'KFP': ('Katla Fish Pickle', 900),
    'TFP': ('Tilapia Fish Pickle', 800)
}

# Reverse map: full name => code
FULLNAME_TO_CODE = {v[0].lower(): k for k, v in PICKLE_INFO.items()}

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

                item_name, qty_str = line.split(':')
                item_name = item_name.strip().lower()
                qty = int(qty_str.strip().split()[0])

                code = FULLNAME_TO_CODE.get(item_name)
                if not code:
                    raise ValueError(f"Unrecognized pickle: {item_name}")

                full_name, price = PICKLE_INFO[code]
                cost = price * qty
                total_cost += cost
                pickle_lines.append(f"{full_name} ({code}) x {qty} = ₹{cost}")

            except Exception as e:
                pickle_lines.append(f"⚠️ Failed to parse line: '{line}' | Error: {e}")

    order_message = (
        f"🧂 *New Order Received!*\n"
        f"👤 Name: {name}\n"
        f"📞 Phone: {phone}\n"
        f"📍 Landmark: {landmark}\n"
        f"🏠 Address: {address}\n"
        f"📮 Pincode: {pincode}\n"
        f"💰 Total: ₹{total_cost}\n\n"
        f"📝 Items:\n" + "\n".join(pickle_lines)
    )

    try:
        # Send WhatsApp message
        message = client.messages.create(
            body=order_message,
            from_=whatsapp_from,
            to=f'whatsapp:{whatsapp_to}'
        )
        print('✅ WhatsApp message sent! SID:', message.sid)

        # Save order to MongoDB
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
        print("❌ Order processing failed:", e)
        return f"<h2>Order Failed 😢</h2><p>Error: {e}</p>"

if __name__ == '__main__':
    app.run(debug=False)
