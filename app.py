import json
import os
import random
import requests
import uuid
from flask import Response, Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
import base64
from flask_caching import Cache
import openai
from flask_sqlalchemy import SQLAlchemy
import pycountry
import dicttoxml
from xml.etree.ElementTree import Element, SubElement, tostring

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

SS_API_KEY = os.environ["SHIPSTATION_API_KEY"]
SS_API_SECRET = os.environ["SHIPSTATION_API_SECRET"]

#BASE_URL = "https://ss-devss257.sslocal.com:8060" # Bundles Z-DDE
BASE_URL = "https://ssapi.shipstation.com/" # For a non-DDE account

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

class Order(db.Model):
    id = db.Column(db.String, primary_key=True)
    product_ids = db.Column(db.String)
    shipping_info = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, id, product_ids, shipping_info):
        self.id = id
        self.product_ids = product_ids
        self.shipping_info = shipping_info


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
    country = pycountry.countries.get(name=shipping_info["Country"])
    country_code = country.alpha_2 if country else shipping_info["Country"]

    # TODO: HACK!
    country_code='US'
    order = {
        "OrderNumber": order_number,
        "OrderDate": datetime.now().isoformat(),
        "OrderStatus": "awaiting_shipment",
        "BillTo": {
            "Name": shipping_info["Name"],
            "Address1": shipping_info["Address1"],
            "City": shipping_info["City"],
            "State": shipping_info["State"],
            "PostalCode": shipping_info["PostalCode"],
            "Country": country_code,
            "Phone": "555-555-5555",
            "Email": "john.doe@example.com"
        },
        "ShipTo": {
            "Name": shipping_info["Name"],
            "Address1": shipping_info["Address1"],
            "City": shipping_info["City"],
            "State": shipping_info["State"],
            "PostalCode": shipping_info["PostalCode"],
            "Country": country_code,
            "Phone": "555-555-5555",
            "Email": "john.doe@example.com"
        },
        "Items": order_items
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
    auth_string = f"{SS_API_KEY}:{SS_API_SECRET}"
    auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    # Set the Authorization header with the encoded credentials
    headers["Authorization"] = f"Basic {auth_string_encoded}"

    response = requests.post(f"{BASE_URL}/orders/createorder", headers=headers, data=json.dumps(order))

    # Print the response status code and body
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")

    return response

def orders_to_shipstation_xml(orders):
    orders_list = []

    for order in orders:
        product_ids = order.product_ids.split(',')
        items = []

        for product_id in product_ids:
            product = next((p for p in fetch_shipstation_products() if str(p["id"]) == product_id), None)
            if product:
                item_data = {
                    "SKU": product["sku"],
                    "Name": product["name"],
                    "Quantity": 1,
                    "UnitPrice": product["price"]
                }
                item = {'Item': item_data}
                items.append(item)

        order_data = {
            "OrderID": order.id,
            "OrderNumber": order.id,
            "OrderDate": order.created_at.strftime("%m/%d/%Y %H:%M %p"),
            "OrderStatus": "paid",
            "LastModified": order.created_at.strftime("%m/%d/%Y %H:%M %p"),
            "CurrencyCode": "USD",
            "TaxAmount": "0.00",
            "ShippingAmount": "100.00",
            "OrderTotal": "100.00",
            "Gift": "false",
            "GiftMessage": "false",
            "CustomField1": "",
            "CustomField2": "",
            "CustomField3": "",
            "Customer": {
                "CustomerCode": "mike.schmoyer@auctane.com",
                "BillTo": json.loads(order.shipping_info),
                "ShipTo": json.loads(order.shipping_info),
            },
            "Items": items
        }
        order = {'Order': order_data}

        orders_list.append(order)

    xml_data = dicttoxml.dicttoxml(orders_list, custom_root='Orders', attr_type=False)
    xml_data = xml_data.decode().replace('<item>', '').replace('</item>', '')
    return xml_data.encode()





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

@app.route('/place_order_db', methods=['POST'])
def place_order_db():
    data = request.get_json()
    product_ids = data.get('product_ids')
    shipping_info = data.get('shipping_info')
    order_id = str(uuid.uuid4())

    order = Order(id=order_id, product_ids=','.join(product_ids), shipping_info=json.dumps(shipping_info))
    db.session.add(order)
    db.session.commit()

    response = {
        "status": "success",
        "order_id": order_id
    }

    return jsonify(response)

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
            "Name": product["name"],
            "SKU": product["sku"],
            "Quantity": 1,
            "UnitPrice": product["price"],
            "WarehouseLocation": "Shelf A1"
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
        "Name": product["name"],
        "SKU": product["sku"],
        "Quantity": 1,
        "UnitPrice": product["price"],
        "WarehouseLocation": "Shelf A1"
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


@app.route('/shipstation_orders', methods=['GET'])
def shipstation_orders():
    action = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = int(request.args.get('page', 1))

    if action == 'export':
        start_date = datetime.strptime(start_date, "%m/%d/%Y %H:%M") if start_date else None
        end_date = datetime.strptime(end_date, "%m/%d/%Y %H:%M") if end_date else None

        # Filter orders based on start_date and end_date
        orders_query = Order.query
        if start_date:
            orders_query = orders_query.filter(Order.created_at >= start_date)
        if end_date:
            orders_query = orders_query.filter(Order.created_at <= end_date)

        orders = orders_query.all()

        # Add pagination
        per_page = 50  # Adjust this value to set the number of orders per page
        orders_paginated = orders[(page - 1) * per_page: page * per_page]

        xml_data = orders_to_shipstation_xml(orders_paginated)

        return Response(xml_data, content_type='application/xml')
    else:
        return jsonify({"error": "Invalid action."}), 400



if __name__ == "__main__":
    app.run(debug=True)
