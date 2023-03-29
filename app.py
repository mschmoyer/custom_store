import json
import os
import random
import requests
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
import base64
from flask_caching import Cache
import openai
from flask_sqlalchemy import SQLAlchemy
import pycountry

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

SS_API_KEY = os.environ["SHIPSTATION_API_KEY"]
SS_API_SECRET = os.environ["SHIPSTATION_API_SECRET"]

BASE_URL = "https://ss-devss257.sslocal.com:8060" # Bundles Z-DDE
#BASE_URL = "https://ssapi.shipstation.com/" # For a non-DDE account

# OpenAI API Key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Our persistent database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<Message {self.sender}: {self.content}>"

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'product_id': self.product_id,
            'quantity': self.quantity
        }

# Add this line before the on_message event handler
message_counter = 0

# Initialize the session with a default value for 'session_id'
@app.before_request
def make_session_permanent():
    session.permanent = True
    session.setdefault('session_id', str(uuid.uuid4()))

def add_to_cart(product_id):
    if not product_id:
        return {'error': 'Product ID is required'}, 400

    # Check if the product is already in the cart
    cart_item = Cart.query.filter_by(session_id=session['session_id'], product_id=product_id).first()

    if cart_item:
        # Update the quantity if the product is already in the cart
        cart_item.quantity += 1
    else:
        # Create a new cart item if the product is not in the cart
        cart_item = Cart(
            session_id=session['session_id'],
            product_id=product_id,
            quantity=1
        )
        db.session.add(cart_item)

    db.session.commit()

    return cart_item.to_dict(), 201

def create_shipstation_order(order_number, order_items, shipping_info):
    country = pycountry.countries.get(name=shipping_info["country"])
    country_code = country.alpha_2 if country else shipping_info["country"]
    order = {
        "orderNumber": order_number,
        "orderDate": datetime.now().isoformat(),
        "orderStatus": "awaiting_shipment",
        "billTo": {
            "name": shipping_info["name"],
            "street1": shipping_info["street1"],
            "city": shipping_info["city"],
            "state": shipping_info["state"],
            "postalCode": shipping_info["postalCode"],
            "country": country_code,
            "phone": "555-555-5555",
            "email": "john.doe@example.com"
        },
        "shipTo": {
            "name": shipping_info["name"],
            "street1": shipping_info["street1"],
            "city": shipping_info["city"],
            "state": shipping_info["state"],
            "postalCode": shipping_info["postalCode"],
            "country": country_code,
            "phone": "555-555-5555",
            "email": "john.doe@example.com"
        },
        "items": order_items
    }

    return order

@cache.memoize(300)
def fetch_shipstation_products():
    headers = {
        "Content-Type": "application/json"
    }

    auth_string = f"{SS_API_KEY}:{SS_API_SECRET}"
    auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {auth_string_encoded}"

    response = requests.get(f"{BASE_URL}/products", headers=headers)
    
    if response.ok:
        shipstation_data = response.json()
        shipstation_products = shipstation_data.get("products", [])
        products = []
        for product in shipstation_products:
            if product.get("weightOz", None) is not None:
                transformed_product = {
                    "id": int(product.get("productId", 0)),
                    "name": product.get("name", ""),
                    "description": product.get("customsDescription", ""),
                    "price": product.get("price", 0),
                    "sku": product.get("sku", "")
                }
                products.append(transformed_product)
        return products
    else:
        return []

def send_order_to_shipstation(order):
    headers = {
        "Content-Type": "application/json"
    }

    # Encode the API key and API secret using Base64
    auth_string = f"{API_KEY}:{API_SECRET}"
    auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    # Set the Authorization header with the encoded credentials
    headers["Authorization"] = f"Basic {auth_string_encoded}"

    response = requests.post(f"{BASE_URL}/orders/createorder", headers=headers, data=json.dumps(order))

    # Print the response status code and body
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")

    return response

# ROUTES
@app.route("/")
def index():
    return redirect(url_for('store'))

@app.route("/blog")
def blog():
    return render_template("blog.html")

@app.route("/store")
def store():
    products = fetch_shipstation_products()
    return render_template("store.html", products=products)

@app.route('/cart', methods=['GET'])
def view_cart():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    cart_items = Cart.query.filter_by(session_id=session['session_id']).all()
    products_dict = {product['id']: product['name'] for product in fetch_shipstation_products()}
    for item in cart_items:
        item.name = products_dict.get(item.product_id)
    return render_template('cart.html', cart_items=cart_items)



@app.route('/add_item_to_cart', methods=['POST'])
def add_item_to_cart_route():
    product_id = request.form.get('product_id')
    result, status_code = add_to_cart(product_id)
    return jsonify(result), status_code



@app.route('/place_order', methods=['POST'])
def place_order():
    product_ids = request.get_json().get('product_ids')
    shipping_info = request.get_json().get('shipping_info')
    order_id = str(uuid.uuid4())
    products = fetch_shipstation_products()

    order_items = []
    for product_id in product_ids:
        product = next((p for p in products if p["id"] == int(product_id)), None)

        if product is None:
            return jsonify({"error": f"Product with ID {product_id} not found."})

        order_item = {
            "lineItemKey": str(uuid.uuid4()),
            "name": product["name"],
            "sku": product["sku"],
            "quantity": 1,
            "unitPrice": product["price"],
            "warehouseLocation": "Shelf A1"
        }
        order_items.append(order_item)

    order = create_shipstation_order(order_id, order_items, shipping_info)
    response = send_order_to_shipstation(order)

    if response.ok:
        # Delete all items from the user's cart
        Cart.query.filter_by(session_id=session['session_id']).delete()
        db.session.commit()
        return jsonify({"message": "Order placed successfully!"})
    else:
        return jsonify({"error": "Failed to place the order. Please try again."})


# This is the now outdated function once used to buy a single product. 
@app.route("/buy/<int:product_id>", methods=["POST"])
def buy(product_id):
    shipping_info = request.get_json()
    order_id = str(uuid.uuid4())
    products = fetch_shipstation_products()
    product = next((p for p in products if p["id"] == product_id), None)
    
    if product is None:
        return jsonify({"error": "Product not found."})

    order_items = [{
        "lineItemKey": str(uuid.uuid4()),
        "name": product["name"],
        "sku": product["sku"],
        "quantity": 1,
        "unitPrice": product["price"],
        "warehouseLocation": "Shelf A1"
    }]
    
    order = create_shipstation_order(order_id, order_items, shipping_info)
    response = send_order_to_shipstation(order)

    if response.ok:
        return jsonify({"message": "Order placed successfully!"})
    else:
        return jsonify({"error": "Failed to place the order. Please try again."})

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json["message"]

    # Add a guiding prompt for the ChatGPT bot
    prompt = (
        "You are a customer service bot for an online store that sells engineering products. "
        "Customers may ask you questions about the ShipStation app as well. You may only respond with a short friendly message and a link to a ShipStation KB article. Provide the actual URL to the article in your response.\n\n"
        "Now, the customer asks:\n\n"
        f"{message}\n\n"
        "Chatbot:"
    )

    # Connect to ChatGPT and get the response
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.5,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    response_text = response.choices[0].text.strip()

     # Save the user's message to the database
    chatbot_message = Message(sender="User", content=message)
    db.session.add(chatbot_message)
    db.session.commit()

    return jsonify({"response": response_text})

@app.route("/messages", methods=["GET"])
def get_messages():
    messages = Message.query.all()
    messages_data = [
        {"sender": message.sender, "content": message.content} for message in messages
    ]
    return jsonify(messages_data)

if __name__ == "__main__":
    app.run(debug=True)
