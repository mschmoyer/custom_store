from models import Cart, Order
import pycountry
import requests
#from app import app
from datetime import datetime
import base64
import dicttoxml
import json

def add_to_cart(session, db, product_id):
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

def fetch_shipstation_products(session):
    # Send them to config page if necessary config info missing
    if 'ss_api_key' not in session or 'ss_api_secret' not in session or 'base_url' not in session:
        print('Cannot fetch products. Missing session keys.')
        return []
    
    ss_api_key = session['ss_api_key']
    ss_api_secret = session['ss_api_secret']
    base_url = session['base_url']

    headers = {
        "Content-Type": "application/json"
    }


    ####
    auth_string = f"{ss_api_key}:{ss_api_secret}"
    auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {auth_string_encoded}"
    ###


    print(f"Getting ShipStation products from base_url={base_url} with key={ss_api_key} and secret={ss_api_secret}")

    response = requests.get(f"{base_url}/products", headers=headers)
    
    if response.ok:
        shipstation_data = response.json()
        shipstation_products = shipstation_data.get("products", [])
        # print(shipstation_products)
        products = []
        for product in shipstation_products:
            if product.get("active", None) is True:
                transformed_product = {
                    "id": int(product.get("productId", 0)),
                    "name": product.get("name", ""),
                    "description": product.get("customsDescription", ""),
                    #"price": product.get("price", 0),
                    "price": 100,
                    "sku": product.get("sku", ""),
                    "thumbnailURL": product.get("thumbnailURL", ""),
                }
                # print(transformed_product['thumbnailURL'])
                products.append(transformed_product)
        return products
    else:
        # Send them to config page if HTTP error. Might make this more specific to a HTTP 401
        # print(response)
        return []

def send_order_to_shipstation(session, order):
    ss_api_key = session['ss_api_key']
    ss_api_secret = session['ss_api_secret']
    base_url = session['base_url']
    
    # Send them to config page if necessary config info missing
    if 'ss_api_key' not in session or 'ss_api_secret' not in session or 'base_url' not in session:
        return []
    
    headers = {
        "Content-Type": "application/json"
    }

    # Encode the API key and API secret using Base64
    auth_string = f"{ss_api_key}:{ss_api_secret}"
    auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    # Set the Authorization header with the encoded credentials
    headers["Authorization"] = f"Basic {auth_string_encoded}"

    response = requests.post(f"{base_url}/orders/createorder", headers=headers, data=json.dumps(order))

    # Print the response status code and body
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")

    return response

def orders_to_shipstation_xml(session, orders):
    orders_list = []

    products = fetch_shipstation_products(session)
    for order in orders:
        #print(f"generating order ...")
        product_ids = order.product_ids.split(',')
        items = []

        for product_id in product_ids:
            product = next((p for p in products if str(p["id"]) == product_id), None)
            if product:
                item_data = {
                    "SKU": product["sku"],
                    "Name": product["name"],
                    "Quantity": 1,
                    "UnitPrice": product["price"]
                }
                item = {'Item': item_data}
                items.append(item)

        # remove the full_name, last_name, and first_name from the shipping info
        # and instead add name which contains full_name
        shipping_info_for_xml = json.loads(order.shipping_info)
        shipping_info_for_xml['Name'] = shipping_info_for_xml['full_name']
        del shipping_info_for_xml['full_name']
        del shipping_info_for_xml['last_name']
        del shipping_info_for_xml['first_name']

        if 'type' in shipping_info_for_xml:
            del shipping_info_for_xml['type']

        # camel case everything in shipping_info_for_xml
        shipping_info_for_xml = {k.capitalize(): v for k, v in shipping_info_for_xml.items()}

        #new variable billTo_for_xml only has name, email, phone, company. If no value in shipping_info_for_xml, do empty string
        billTo_for_xml = {
            "Name": shipping_info_for_xml.get('Name', ''),
            "Email": shipping_info_for_xml.get('Email', ''),
            "Phone": shipping_info_for_xml.get('Phone', ''),
            "Company": shipping_info_for_xml.get('Company', '')
        }

        # remove email from shipping_info_for_xml
        del shipping_info_for_xml['Email']

        # convert Ln1 to Address1, Ln2 to Address2
        if 'Ln1' in shipping_info_for_xml:
            shipping_info_for_xml['Address1'] = shipping_info_for_xml.get('Ln1', '')
            shipping_info_for_xml['Address2'] = shipping_info_for_xml.get('Ln2', '')
            del shipping_info_for_xml['Ln1']
            del shipping_info_for_xml['Ln2']

        # remove province from shipping_info_for_xml
        if 'Province' in shipping_info_for_xml:
            del shipping_info_for_xml['Province']

        # if found, convert Zip to PostalCode
        if 'Zip' in shipping_info_for_xml:
            shipping_info_for_xml['PostalCode'] = shipping_info_for_xml['Zip']
            del shipping_info_for_xml['Zip']

        # if Country_code is found, replace it with Country
        if 'Country_code' in shipping_info_for_xml:
            shipping_info_for_xml['Country'] = shipping_info_for_xml['Country_code']
            del shipping_info_for_xml['Country_code']

        # Country should be converted to a 2-digit country code
        country = pycountry.countries.get(name=shipping_info_for_xml["Country"])
        country_code = country.alpha_2 if country else shipping_info_for_xml["Country"]
        # trim to 2 characters
        shipping_info_for_xml["Country"] = country_code[:2]

        #if country code is not 2 characters, default to US
        if len(shipping_info_for_xml["Country"]) != 2:
            shipping_info_for_xml["Country"] = 'US'

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
                "BillTo": billTo_for_xml,
                "ShipTo": shipping_info_for_xml,
            },
            "Items": items
        }
        order = {'Order': order_data}

        orders_list.append(order)


    xml_data = dicttoxml.dicttoxml(orders_list, custom_root='Orders', attr_type=False)
    xml_data = xml_data.decode().replace('<item>', '').replace('</item>', '')
    return xml_data.encode()