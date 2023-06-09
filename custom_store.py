import requests
import json
import random
import uuid
from datetime import datetime
import base64

# Replace these with your ShipStation API key and secret
API_KEY = "536af632ffa74eb5a13c1ba17a3b7da5"
API_SECRET = "4293aae0e7a44217a45c784eeb235704"

# ShipStation API base URL
BASE_URL = "https://ssapi.shipstation.com"

def create_shipstation_order(order_number, items):
    order_date = datetime.now().isoformat()

    order = {
        "orderNumber": order_number,
        "orderDate": order_date,
        "orderStatus": "awaiting_shipment",
        "amountPaid": round(sum(item["unitPrice"] * item["quantity"] for item in items), 2),
        "shippingAmount": 0,
        "taxAmount": 0,
        "internalNotes": "Generated by custom store integration",
        "billTo": {
            "name": "John Doe",
            "company": None,
            "street1": "123 Main St",
            "street2": None,
            "city": "Austin",
            "state": "TX",
            "postalCode": "78759",
            "country": "US",
            "phone": "512-555-1234",
            "email": "john.doe@example.com"
        },
        "shipTo": {
            "name": "John Doe",
            "company": None,
            "street1": "123 Main St",
            "street2": None,
            "city": "Austin",
            "state": "TX",
            "postalCode": "78759",
            "country": "US",
            "phone": "512-555-1234",
            "email": "john.doe@example.com"
        },
        "items": items
    }

    return order

def create_dummy_order_item(quantity):
    product_name = f"Product {uuid.uuid4()}"
    unit_price = round(random.uniform(1, 100), 2)

    order_item = {
        "lineItemKey": str(uuid.uuid4()),
        "sku": f"SKU-{uuid.uuid4()}",
        "name": product_name,
        "imageUrl": None,
        "weight": {
            "value": round(random.uniform(1, 10), 2),
            "units": "ounces"
        },
        "quantity": quantity,
        "unitPrice": unit_price,
        "taxAmount": 0,
        "shippingAmount": 0,
        "warehouseLocation": "A1",
        "options": []
    }

    return order_item

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
    return response

def main(number_of_orders, order_items_count):
    for i in range(number_of_orders):
        order_number = generate_order_number()
        order_items = generate_order_items(order_items_count)
        order = create_shipstation_order(order_number, order_items)
        response = send_order_to_shipstation(order)

        if response.status_code == 200:
            print(f"Order {order_number} successfully created")
        else:
            print(f"Error creating order {order_number}: {response.status_code} - {response.text}")

def generate_order_number():
    return f"CustomOrder-{uuid.uuid4()}"

def generate_order_items(order_items_count):
    return [create_dummy_order_item(random.randint(1, 5)) for _ in range(order_items_count)]


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Generate dummy orders and send them to ShipStation")
    parser.add_argument("-n", "--orders", type=int, required=True, help="Number of orders to create")
    parser.add_argument("-i", "--items", type=int, required=True, help="Number of items in each order")

    args = parser.parse_args()

    main(args.orders, args.items)



#To run the script, save it as `shipstation_custom_integration.py` and execute it from the command line with the desired number of orders and items per order:

#```bash
#python shipstation_custom_integration.py --orders 10 --items 3
#