from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from urllib.request import urlopen
import ssl
from bs4 import BeautifulSoup
from pymongo import MongoClient
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)


client = MongoClient('mongodb://localhost:27017/')
db = client['pricemonitoring']
users_collection = db['users']
products_collection = db['products']

PER_PAGE = 25

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/products')
def get_products():
    products = products_collection.find()
    formatted_products = []
    for product in products:
        with open(product['image'], 'rb') as f:
            image_data = f.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

        product['image'] = base64_image
        formatted_products.append(product)

    return jsonify({'products': formatted_products})

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    users = users_collection.find()
    for user in users:
        if user['username']==username and user['password']==password : 
            return redirect(url_for('monitoring'))
    
    message = "Invalid Credentials! Try Again!"
    return render_template('index.html', message=message)

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/monitoring')
def monitoring():
    page = request.args.get('page', default=1, type=int)
    skip_count = (page - 1) * PER_PAGE
    
    total_products = products_collection.count_documents({})
    total_pages = ((total_products + PER_PAGE - 1) // PER_PAGE)
    end_page = min(6, total_pages + 1) 
    
    products = products_collection.find().skip(skip_count).limit(PER_PAGE)
    
    return render_template('monitoring.html', products=products, page=page, total_pages=total_pages, end_page=end_page)


@app.route('/ebay/<product_id>')
def get_ebay_price(product_id):    
    product = products_collection.find_one({"id": product_id}, {"_id": 0, "Ebay": 1})
    url = product.get("Ebay","")
    if url == "Not available":
        return jsonify({'ebay_price':"NA"})
    else:
        page = requests.get(url)
        soup = BeautifulSoup(page.content , "html.parser")

        price_element = soup.find("div", {"class": "x-price-primary"})
        if price_element:
            return jsonify({'ebay_price': price_element.get_text().split()[1]})
        else:
            return jsonify({'ebay_price':"NaN"})
    
@app.route('/amazon/<product_id>')
def get_amazon_price(product_id):
    product = products_collection.find_one({"id": product_id}, {"_id": 0, "Amazon": 1})
    url = product.get("Amazon", "")
    if url == "Not available":
        return jsonify({'amazon_price':"NA"})

    # url = "https://www.amazon.com/Epson-DURABrite-Ultra-Capacity-Cartridge/dp/B08DX5F6XV"
    context = ssl._create_unverified_context()
    res = urlopen(url,context=context)
    soup = BeautifulSoup(res, "html.parser")

    price_element = soup.find("span",{'class':'a-offscreen'})
    if price_element:
        price_text = price_element.find("span", {"class": "a-size-mini olpWrapper"}).text.strip()
        amazon_price = price_text.split("from ")[1].split(" ")[0]
        return jsonify({'amazon_price': price_element.text})
    else:
        return jsonify({'amazon_price' : "NaN"})

@app.route('/cityblue/<product_id>')
def get_citybluetechnologies_price(product_id):
    product = products_collection.find_one({"id": product_id}, {"_id": 0, "CityBlue": 1})
    product_url = product.get("CityBlue", "")
    if product_url == "Not available":
        return jsonify({'cityblue_price':"NA"})
    else:

        # product_url ="https://citybluetechnologies.com/product/t812-exra-high-capacity-black-ink-cartridge-sensormatic/"

        context = ssl._create_unverified_context()
        res = urlopen(product_url,context=context)
        soup = BeautifulSoup(res, "html.parser")
        price = soup.find("bdi")
        if price:
            return jsonify({'cityblue_price':price.get_text()})
        else:
            return jsonify({'cityblue_price':"NaN"})
    
@app.route('/officemax/<product_id>')
def get_office_max_price(product_id):
    product = products_collection.find_one({"id": product_id}, {"_id": 0, "OfficeMax": 1})
    url = product.get("OfficeMax","")  
    if url == "Not available":
        return jsonify({'officemax_price':"NA"})
    else :
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            price_element = soup.find('span', class_='od-graphql-price-big-price')

            if price_element:
                price_text = price_element.text.strip()
                return jsonify({'officemax_price': price_text})

        return jsonify({'officemax_price':"NaN"})

@app.route('/staples/<product_id>')
def extract_price(product_id):
    product = products_collection.find_one({"id": product_id}, {"_id": 0, "Staples": 1})
    url = product.get("Staples","")  

    if url == "Not available":
        return jsonify({'staples_price':"NA"})
    response = requests.get(url)
    if response.status_code == 200: 
        soup = BeautifulSoup(response.content, 'html.parser')

        price_element = soup.find("div", {"class": "price-info__final_price_sku"})

        if price_element:
            price_text = price_element.text.strip()
            return jsonify({'staples_price': price_text})

        return jsonify({'staples_price':"NA"})

@app.route('/update_price', methods=['POST'])
def update_price():
    product_id = request.json['product_id']
    new_price = request.json['new_price']
    db.products.update_one({'id': product_id}, {'$set': {'updated_cityblue': new_price}})
    return {"data":"Updated"}


@app.route('/search', methods=['POST'])
def search_products():
    search_query = request.json.get('query', '')
    results = products_collection.find({"$text": {"$search": search_query}})
    products = list(results)
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)  
