import re
import ast
import math
import json
import numpy as np
from bson import json_util
from flask_cors import CORS
from flask import Flask, request
from authenticator.authenticate_user import authenticate_user
from databases.redis_connector import get_redis_database
from databases.mongodb_connector import get_database, create_object_id

app = Flask(__name__)
CORS(app)


@app.route('/login/<username>/<password>', methods=['GET'])
def user_login(username, password):
    database = get_database()
    user_collection = database.get_collection("user")
    query = {'username': {"$eq": username}}

    user = user_collection.find_one(query)

    if user:
        if authenticate_user(user, password):
            return json.loads(json_util.dumps({
                "message": "Login_Successful",
                "user_id": str(user["_id"]),
                "name": user["first_name"]
            }))
        else:
            return json.loads(json_util.dumps({"message": "Wrong_Password"}))
    else:
        return json.loads(json_util.dumps({"message": "NO_USER"}))


@app.route('/search_products', methods=['POST'])
def search_products():
    content_type = request.headers.get('Content-Type')

    if content_type == 'application/json':
        body = request.json

        database = get_database()
        collection = database.get_collection("products")

        query = dict()

        # Search Query
        if body['query']:
            name_regex = re.compile(f'.*{body["query"]}.*', re.IGNORECASE)
            query['name'] = {'$regex': name_regex}

        # Category Filter
        if body['category'] != 'ALL':
            query['category'] = {"$eq": body['category']}

        # Price Filter
        if body['start_price'] == -1 and body['end_price'] == -1:
            query['price'] = {'$gte': -math.inf, '$lte': math.inf}
        elif body['start_price'] == -1:
            query['price'] = {'$gte': -math.inf, '$lte': body['end_price']}
        elif body['end_price'] == -1:
            query['price'] = {'$gte': body['start_price'], '$lte': math.inf}
        else:
            query['price'] = {'$gte': body['start_price'], '$lte': body['end_price']}

        # Rating Filter
        query['rating'] = {'$gte': body['rating']}

        items = collection.find(query).limit(20)

        product_respond = list()
        for item in items:
            temp_dict = {
                "product_id": str(item['_id']),
                "name": item['name'],
                "description": item['description'],
                "price": item['price'],
                "rating": item['rating'],
            }

            product_respond.append(temp_dict)

        return json.loads(json_util.dumps(product_respond))


@app.route('/fetch_product/<product_id>', methods=['GET'])
def fetch_product(product_id):
    products_collection = get_database().get_collection('products')
    product = products_collection.find_one({"_id": create_object_id(product_id)})

    if product:
        product['product_id'] = str(product['_id'])
        del product['_id']
        return json.loads(json_util.dumps(product))

    return json.loads(json_util.dumps(dict()))


@app.route('/add_product_to_cart', methods=['POST'])
def add_product_to_cart():
    content_type = request.headers.get('Content-Type')

    if content_type == 'application/json':
        body = request.json
        user_id = body['user_id']
        product_id = body['product_id']

        database = get_database()
        cart_collection = database.get_collection("cart")
        query = {'user_id': {"$eq": user_id}, 'product_id': {"$eq": product_id}}
        cart_item = cart_collection.find_one(query)

        if cart_item:
            updated_cart_item = {
                "user_id": user_id,
                "product_id": product_id,
                "quantity": cart_item['quantity'] + 1
            }

            id_dict = {"_id": cart_item["_id"]}
            update_dict = {"$set": updated_cart_item}

            cart_collection.update_one(id_dict, update_dict)

            return json.loads(json_util.dumps({"message": "Cart updated Successfully"}))
        else:
            new_cart_item = {
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            }

            cart_collection.insert_one(new_cart_item)

            return json.loads(json_util.dumps({"message": "Item added to cart Successfully"}))

    return json.loads(json_util.dumps({"message": "Something went Wrong !"}))


@app.route('/get_cart/<user_id>', methods=['GET'])
def get_cart(user_id):
    database = get_database()
    cart_collection = database.get_collection("cart")

    query = {'user_id': {"$eq": user_id}}
    cart_items = cart_collection.find(query)

    products_list = list()
    for item in cart_items:
        products_collection = database.get_collection('products')
        product = products_collection.find_one({"_id": create_object_id(item['product_id'])})

        if product:
            temp_product = {
                'product_id': str(product['_id']),
                'name': product['name'],
                'price': product['price'],
                'quantity': item['quantity']
            }

            products_list.append(temp_product)

    user = database.get_collection("user").find_one({'_id': create_object_id(user_id)})
    user_address = database.get_collection("user_address").find_one({'user_id': {"$eq": user_id}})
    user_data_json = dict()

    if user and user_address:
        user_data_json["name"] = user['first_name'] + " " + user['last_name']
        user_data_json["address"] = user_address['address']
        user_data_json["city_id"] = user_address['city_id']
        user_data_json["postal"] = user_address['postal']
        user_data_json["mobile"] = user_address['mobile']
    else:
        user_data_json["name"] = "Error"
        user_data_json["address"] = "Error"
        user_data_json["city_id"] = "Error"
        user_data_json["postal"] = "Error"
        user_data_json["mobile"] = "Error"

    response_json = {"products_list": products_list, "user_data_json": user_data_json}

    return json.loads(json_util.dumps(response_json))


@app.route('/remove_item_from_cart', methods=['POST'])
def remove_item_from_cart():
    content_type = request.headers.get('Content-Type')

    if content_type == 'application/json':
        body = request.json
        user_id = body['user_id']
        product_id = body['product_id']

        database = get_database()
        cart_collection = database.get_collection("cart")
        query = {'user_id': {"$eq": user_id}, 'product_id': {"$eq": product_id}}
        cart_collection.delete_one(query)

        return json.loads(json_util.dumps({"message": "Item removed from cart successfully."}))


@app.route('/complete_order', methods=['POST'])
def complete_order():
    content_type = request.headers.get('Content-Type')

    if content_type:
        body = request.json

        user_id = body['user_id']
        total_amount = body['total_amount']

        database = get_database()

        # Adding Payment Details
        payment_details_collection = database.get_collection("payment_details")
        payment_details_dict = {
            "amount": total_amount,
            "status": "Payment Successful"
        }
        payment_details = payment_details_collection.insert_one(payment_details_dict)

        # Order Details
        order_details_collection = database.get_collection("order_details")
        order_details_dict = {
            "user_id": user_id,
            "total": total_amount,
            "payment_details_id": str(payment_details.inserted_id)
        }
        order_details = order_details_collection.insert_one(order_details_dict)

        # Order Items
        cart_collection = database.get_collection("cart")
        cart_items = cart_collection.find({"user_id": {"$eq": user_id}})

        order_items_collection = database.get_collection("order_items")
        for item in cart_items:
            temp_order_item = {
                "order_details_id": str(order_details.inserted_id),
                "product_id": item["product_id"],
                "quantity": item["quantity"]
            }

            order_items_collection.insert_one(temp_order_item)

            # Updating Product Inventory Count after the purchase
            products_collection = database.get_collection("products")
            product_item = products_collection.find_one({"_id": create_object_id(item["product_id"])})

            updated_product_id = {
                "name": product_item["name"],
                "description": product_item["description"],
                "category": product_item["category"],
                "price": product_item["price"],
                "rating": product_item["rating"],
                "inventory": product_item["inventory"] - item["quantity"],
                "sold_qtn": product_item["sold_qtn"] + item["quantity"]
            }

            id_dict = {"_id": product_item["_id"]}
            update_dict = {"$set": updated_product_id}

            products_collection.update_one(id_dict, update_dict)

        # Deleting Cart After Purchase
        cart_collection.delete_many({"user_id": {"$eq": user_id}})

    return json.loads(json_util.dumps({"message": "Order Booking Confirmed."}))


@app.route('/get_all_orders/<user_id>', methods=['GET'])
def get_all_orders(user_id):
    order_details = get_database().get_collection("order_details").find({'user_id': {"$eq": user_id}})

    order_details_list = list()
    for od in order_details:
        temp_od = {
            "order_id": str(od["_id"]),
            "amount": od["total"]
        }

        order_details_list.append(temp_od)

    return json.loads(json_util.dumps(order_details_list[::-1]))


@app.route('/get_order_details/<order_details_id>', methods=['GET'])
def get_order_details(order_details_id):
    database = get_database()

    order_details = database.get_collection("order_details").find_one({'_id': create_object_id(order_details_id)})

    payment_details_id = order_details['payment_details_id']
    payment_details_collection = database.get_collection("payment_details")
    payment_details = payment_details_collection.find_one({'_id': create_object_id(payment_details_id)})

    order_items = database.get_collection("order_items").find({'order_details_id': {"$eq": order_details_id}})

    products_list = list()
    for ot in order_items:
        product_id = ot['product_id']
        product = database.get_collection("products").find_one({'_id': create_object_id(product_id)})

        temp_ot = {
            "name": product['name'],
            "price": product['price'],
            "category": product['category'],
            "quantity": ot['quantity']
        }

        products_list.append(temp_ot)

    payment_details_dict = {
        "order_id": order_details_id,
        "amount": payment_details["amount"],
        "status": payment_details["status"]
    }

    return json.loads(json_util.dumps({"payment_details": payment_details_dict, "order_items": products_list}))


@app.route('/fetch_suggestions/<user_id>', methods=['GET'])
def fetch_suggestions(user_id):
    database = get_database()
    order_details_collection = database.get_collection("order_details")

    users_all_ordered_items = order_details_collection.aggregate([
        {
            '$addFields': {
                'order_details_id': {
                    '$toString': '$_id'
                }
            }
        }, {
            '$match': {
                'user_id': {
                    '$eq': user_id
                }
            }
        }, {
            '$lookup': {
                'from': 'order_items',
                'localField': 'order_details_id',
                'foreignField': 'order_details_id',
                'as': 'order_items_array'
            }
        }, {
            '$unwind': {
                'path': '$order_items_array',
                'preserveNullAndEmptyArrays': False
            }
        }
    ])

    category_frequency = list()
    price_json = list()
    prices = list()

    for order in users_all_ordered_items:
        try:
            products_collection = get_database().get_collection('products')
            product = products_collection.find_one({"_id": create_object_id(order['order_items_array']['product_id'])})

            if product:
                price_json.append({"price": product["price"], "category": product["category"]})
                category_frequency.extend([product['category']] * order['order_items_array']['quantity'])
            else:
                continue
        except Exception as e:
            print(e)

    most_occured_cat = max(set(category_frequency), key=category_frequency.count)

    for price in price_json:
        if price['category'] == most_occured_cat:
            prices.append(price['price'])

    mean = np.mean(prices)
    std = np.std(prices)

    start_price = int(mean - std)
    end_price = int(mean + std)

    start_price = start_price if start_price > 0 else 0

    return {"category": most_occured_cat, "start_price": start_price, "end_price": end_price}


@app.route('/live_tracking/<order_tracking_id>')
def live_location(order_tracking_id):
    rc = get_redis_database()

    p = rc.pubsub()
    p.subscribe(order_tracking_id)

    while True:
        try:
            message = p.get_message()
            if message:
                longlat = message['data']
                if longlat == 1:
                    pass
                elif longlat == "Delivered":
                    return json.dumps(["Delivered"])
                else:
                    my_list = ast.literal_eval(longlat)
                    return json.dumps(my_list)
        except Exception as e:
            print(e)
            return json.dumps(["Delivered"])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050)
