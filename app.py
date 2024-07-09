import json
import os
import requests
import uuid
import base64
import pycountry
import dicttoxml
import yaml
import time
import random

from flask import Response, Flask, render_template, request, jsonify, redirect, url_for, session
from flask_session import Session
from datetime import datetime
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_cors import cross_origin

from xml.etree.ElementTree import Element, SubElement, tostring

app = Flask(__name__)
app.secret_key = os.urandom(24)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Set your secret key. This is required to keep the client-side sessions secure.
# Use a random value or generate one using os.urandom(16)
app.config['SECRET_KEY'] = 'WhyDidTheDeveloperGoBroke?BecauseHeUsedUpAllHisCache!'

# You can use filesystem session, or others like redis or memcached
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


# Our persistent database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///custom_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from database import db

db.init_app(app)

# Now import the models
#from models import Cart, Order

with app.app_context():
    db.create_all()


# Initialize the session with a default value for 'session_id'
@app.before_request
def make_session_permanent():
    session.permanent = True
    session.setdefault('session_id', str(uuid.uuid4()))

# **************************************************
# Helper Functions related to using ShipStation API
from shipstation import *

@cache.memoize(20)
def fetch_products():
    return fetch_shipstation_products(session)
# **************************************************

# ROUTES
@app.route("/")
def index():
    return redirect(url_for('store'))

@app.route("/blog")
def blog():
    return render_template("blog.html")

# This route is our main store page that lists products for sell. 
@app.route("/store")
def store():
    #if 'ss_api_key' not in session:
    #    return redirect('/start')
    
    products = fetch_products()
    return render_template("store.html", products=products)


# This route returns what is in my cart.
@app.route("/cart_items")
def cart_items():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    cart_items = Cart.query.filter_by(session_id=session['session_id']).all()
    products_dict = {product['id']: product['name'] for product in fetch_products()}
    for item in cart_items:
        item.name = products_dict.get(item.product_id)
    return jsonify(cart_items)


# This route is the cart page that shows orders and a place to send the order. 
@app.route('/cart', methods=['GET'])
def view_cart():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

    if 'ss_api_key' not in session:
        return redirect('/start')

    cart_items = Cart.query.filter_by(session_id=session['session_id']).all()
    products_dict = {product['id']: product['name'] for product in fetch_products()}
    for item in cart_items:
        item.name = products_dict.get(item.product_id)
    return render_template('cart.html', cart_items=cart_items)

@app.route('/add_item_to_cart', methods=['POST'])
def add_item_to_cart_route():
    product_id = request.form.get('product_id')
    result, status_code = add_to_cart(session, db, product_id)
    return jsonify(result), status_code

@app.route('/place_order_db', methods=['POST'])
def place_order_db():
    data = request.get_json()
    product_ids = data.get('product_ids')
    shipping_info = data.get('shipping_info')

    print(f"Shipping to: {shipping_info}")
    print(f"Products: {product_ids}")

    return save_order_to_db(product_ids, shipping_info)

def save_order_to_db(product_ids, shipping_info):
    count = 0
    duplicate_order_count= 1
    while count < duplicate_order_count:
        count = count + 1
        order_id = str(uuid.uuid4())
        try:
            order = Order(id=order_id, product_ids=','.join(product_ids), shipping_info=json.dumps(shipping_info), shipped=True)
            db.session.add(order)
            db.session.commit()
        except Exception as e:
            print(f"Error saving the order: {e}")
            return {}
        
        response = {
            "status": "success",
            "order_id": order_id
        }    
    # Delete all items from the user's cart
    Cart.query.filter_by(session_id=session['session_id']).delete()
    db.session.commit()

    print("Order processed successfully. Removing items from cart DB...")

    return jsonify(response)

# This would place an order via OpenAPI (not a custom store)
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

    print(f"Placing order. Count={count}")
    order = create_shipstation_order(order_id, order_items, shipping_info)
    response = send_order_to_shipstation(session, order)

    if response.ok:
        # Delete all items from the user's cart
        Cart.query.filter_by(session_id=session['session_id']).delete()
        db.session.commit()

        print("Order processed successfully. Removing items from cart DB...")
        return jsonify({"message": "Order placed successfully!"})
    else:
        return jsonify({"error": "Failed to place the order. Please try again."})

# this is a function that writes a new message
@app.route("/messages", methods=["POST"])
def add_message():
    data = request.get_json()
    message = Message(sender=data["sender"], content=data["content"])
    db.session.add(message)
    db.session.commit()
    return jsonify({"message": "Message created successfully!"})

@app.route("/messages", methods=["GET"])
def get_messages():
    messages = Message.query.all()
    messages_data = [
        {"sender": message.sender, "content": message.content} for message in messages
    ]
    return jsonify(messages_data)

# MARKETPLACE NOTIFICATION
#POST /shipstation_orders?SS-UserName=abc&SS-Password=123&action=shipnotify&order_number=698895f8-e857-44de-8739-9f316b91e36c&carrier=3297&service=&tracking_number=abc123 HTTP/1.1
# Route to receive marketplace notifications from ShipStation API
@app.route('/shipstation_orders', methods=['POST'])
def shipstation_notifications():
    print("---")
    print("*** ORDER UPDATE RECEIVED ***")
    print("---")
    print("Causing a delay to simulate a long-running process...")
    time.sleep(3)
    print("Done.")
    #print(request.data)
    return Response(status=200)

# REQUEST FOR NEW ORDERS
#https://ccc996c96d3b.ngrok.app/shipstation_orders
#?action=export&start_date=01%2f23%2f2012+17%3a28&end_date=01%2f23%2f2012+17%3a33&page=1
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

        print("Session before ENV check:")
        print(session)

        if 'ss_api_key' not in session:
            print('No local config. Using ENV default...')
            session['ss_api_key'] = os.environ['SHIPSTATION_API_KEY']
            session['ss_api_secret'] = os.environ['SHIPSTATION_API_SECRET']
            session['base_url'] = "https://ssapi.shipstation.com/"

        print("Session before XML:")
        print(session)

        xml_data = orders_to_shipstation_xml(session, orders_paginated)

        print(xml_data)
        # Delete all items from the user's cart
        Order.query.delete()
        db.session.commit()

        return Response(xml_data, content_type='application/xml')
    else:
        return jsonify({"error": "Invalid action."}), 400


@app.route('/start')
def start():
    with app.app_context():
        db.create_all()
    return render_template('start.html')

@app.route('/config_save', methods=['POST'])
def config_save():
    # Store the submitted values in the session
    session['ss_api_key'] = request.form['ss_api_key']
    session['ss_api_secret'] = request.form['ss_api_secret']
    session['base_url'] = request.form['base_url']

    # Redirect to the /store page
    print('Configuration saved. Session:')
    print(session)
    return redirect('/store')


def ingest_yaml_address_file(file_name):
    try:
        # __file__ is the path to the current script file
        script_location = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_location, file_name)

        with open(file_path, 'r') as file:
            addresses = yaml.safe_load(file)
            return addresses
    except Exception as e:
        print(f"Error reading the YAML file: {e}")
        return {}



@app.route('/addresses')
def addresses():
    addresses = ingest_yaml_address_file("static/addresses.yml")
    return render_template('addresses.html', addresses=addresses)


# This is designed to be called randomly to simulate a store situation. 
# Function that picks a random address from the YAML file
@app.route('/submit_chaotic_order', methods=['POST'])
def submit_chaotic_order():

    # pick a random persona from the file
    addresses = ingest_yaml_address_file("static/addresses.yml")

    # Assuming 'addresses' is your dictionary
    random_address = random.choice(list(addresses.values()))
    shipping_info=random_address[1]
    print(f"Shipping to: {shipping_info}")

    # put 1-5 random products in the cart
    products = fetch_products()
    if len(products) > 0:
        
        #choose 1-5 random products from the products array and return the product_ids

        # Randomly determine the number of products to choose
        num_products_to_choose = random.randint(1, min(5, len(products)))

        # Randomly select unique products
        selected_products = random.sample(products, num_products_to_choose)

        # Extract the product_ids from the selected products
        product_ids = [str(product['id']) for product in selected_products]
        print(f"Submitting order with {len(product_ids)} products.")
        print(f"Products: {product_ids}")      

        #now place the order. it will be saved in the DB. 
        save_order_to_db(product_ids, shipping_info)
    
    #return success
    return jsonify({"message": "Order placed successfully!"})


# New route to handle the new ShipStation chatbot
@cross_origin() # allow all origins all methods.
@app.route('/shipstation-chat', methods=['GET'])
def shipstation_chat_route():
    # Get the question query parameter
    question = request.args.get('question')
    session_id = session['session_id']

    # Generate a new session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    #put the question into the data object
    output_json = {"question": question, "session_id": session_id}

    # Call out to https://supportgpt.sslocal.com/shipstation-chat to get the answer
    response = requests.post('https://supportgpt.sslocal.com/shipstation-chat', json=output_json)
    print(f"Response status code: {response.status_code}")
    return response

if __name__ == "__main__":
    app.run(debug=True)