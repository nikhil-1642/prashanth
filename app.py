from flask import Flask, request, render\_template
from twilio.rest import Client
from flask\_pymongo import PyMongo
import os

app = Flask(**name**)

# ✅ Use full MongoDB URI from environment variable

app.config\["MONGO\_URI"] = os.getenv("MONGO\_URI")
mongo = PyMongo(app)

# ✅ Twilio setup using env vars

account\_sid = os.getenv("TWILIO\_SID")
auth\_token = os.getenv("TWILIO\_AUTH")
FROM\_PHONE = os.getenv("TWILIO\_FROM")
TO\_PHONE = os.getenv("TWILIO\_TO")
client = Client(account\_sid, auth\_token)

# ✅ Pickle price list

PICKLE\_INFO = {
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
return render\_template('english.html')

@app.route('/submit', methods=\['POST'])
def submit():
name = request.form.get('name')
phone = request.form.get('phone')
landmark = request.form.get('landmark')
address = request.form.get('address')
pincode = request.form.get('pincode')
pickles\_input = request.form.get('pickles')
total\_cost = 0
pickle\_lines = \[]

```
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

# ✅ Compose a proper SMS message
sms_message = f"New order from {name}, ₹{total_cost}:\n" + "\n".join(pickle_lines)

try:
    # ✅ Send SMS via Twilio
    message = client.messages.create(
        body=sms_message,
        from_=FROM_PHONE,
        to=TO_PHONE
    )
    print(f"✅ SMS sent with SID: {message.sid}")

    # ✅ Save order to MongoDB
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
    print("❌ Failed to send SMS or save order:", e)
    return f"<h2>Order Failed 😢</h2><p>Error: {e}</p>"
```

if **name** == '**main**':
app.run(debug=False)-------> take the code
