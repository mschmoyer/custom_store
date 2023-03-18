import json
import os
import random
import requests
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash    
from datetime import datetime
import base64
import pycountry

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace these with your ShipStation API key and secret
API_KEY = "3b3e873ff35f4841bd098109b4500b2c"
API_SECRET = "f73caa021efa4435b609d969ad0b5b7f"
BASE_URL = "https://ss-devss221.sslocal.com:8060"
#BASE_URL = "https://ssapi.shipstation.com/"

products = [
    {
        "id": 1,
        "name": "High-Performance Mechanical Keyboard",
        "description": "A premium mechanical keyboard with customizable RGB backlighting, PBT keycaps, and programmable keys. Perfect for long coding sessions and a comfortable typing experience.",
        "price": 199.99,
        "sku": "HPMK-100"
    },
    {
        "id": 2,
        "name": "Ergonomic Adjustable Standing Desk",
        "description": "A high-quality, height-adjustable standing desk with an electric lift system and memory presets. Easily switch between sitting and standing positions for optimal comfort and productivity.",
        "price": 599.99,
        "sku": "EASD-200"
    },
    {
        "id": 3,
        "name": "Ultimate Engineer Bundle",
        "description": "A special bundle that includes a High-Performance Mechanical Keyboard, Ergonomic Adjustable Standing Desk, and Web App Development Masterclass. Elevate your work environment and skills!",
        "price": 999.99,
        "sku": "UEB-300"
    }
]

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

def fetch_shipstation_products():
    headers = {
        "Content-Type": "application/json"
    }

    auth_string = f"{API_KEY}:{API_SECRET}"
    auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {auth_string_encoded}"

    response = requests.get(f"{BASE_URL}/products", headers=headers)
    
    if response.ok:
        shipstation_data = response.json()
        shipstation_products = shipstation_data.get("products", [])
        products = []
        for product in shipstation_products:
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


@app.route("/")
def index():
    products = fetch_shipstation_products()
    return render_template("index.html", products=products)


@app.route("/buy/<int:product_id>", methods=["POST"])
def buy(product_id):
    shipping_info = request.get_json()
    order_id = str(uuid.uuid4())
    global products
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


if __name__ == "__main__":
    app.run(debug=True)
