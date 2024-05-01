from flask import Flask, render_template, request, redirect, url_for, jsonify
from selenium import webdriver
from bs4 import BeautifulSoup
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['pricemonitoring']
users_collection = db['users']
products_collection = db['products']

@app.route('/')
def index():
    return render_template('index.html')

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
    products = products_collection.find()
    return render_template('monitoring.html',products=products)

@app.route('/ebay')
def get_ebay_price():
    url="https://www.ebay.com/itm/256458485567"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    html = driver.page_source
    driver.quit()  
    soup = BeautifulSoup(html, 'html.parser')

    price_element = soup.find("div", {"class": "x-price-primary"})
    if price_element:
        return jsonify({'ebay_price': price_element.text})
    else:
        return "NaN"
    
@app.route('/amazon')
def get_amazon_price():
    url = "https://www.amazon.com/Epson-DURABrite-Ultra-Capacity-Cartridge/dp/B08DX5F6XV"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    html = driver.page_source
    driver.quit() 
    soup = BeautifulSoup(html, 'html.parser')

    price_element = soup.find("span", {"id": "style_name_0_price"})
    if price_element:
        price_text = price_element.find("span", {"class": "a-size-mini olpWrapper"}).text.strip()
        amazon_price = price_text.split("from ")[1].split(" ")[0]
        return jsonify({'amazon_price': amazon_price})
    else:
        return "NaN"

@app.route('/cityblue')
def get_citybluetechnologies_price():
    product_url ="https://citybluetechnologies.com/product/t812-exra-high-capacity-black-ink-cartridge-sensormatic/"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    driver = webdriver.Chrome(options=options)

    driver.get(product_url)
    html = driver.page_source
    driver.quit()  
    soup = BeautifulSoup(html, 'html.parser')

    price_element = soup.find("span", {"class": "woocommerce-Price-amount amount"})
    if price_element:
        return jsonify({'cityblue_price':price_element.text.strip()})
    else:
        return "NaN"

@app.route('/update_price', methods=['POST'])
# for  updateing we use PUT method 
def update_price():
    product_id = request.json['product_id']
    new_price = request.json['new_price']
    db.products.update_one({'id': product_id}, {'$set': {'updated_cityblue': new_price}})
    return {"data":"Updated"}
if __name__ == '__main__':
    app.run(debug=True)

# search function
@app.route('/search', methods=['POST'])
def search_products():
    search_query = request.json.get('query', '')

    # Query MongoDB to search for products based on the search query
    results = products_collection.find({"$text": {"$search": search_query}})

    # Convert MongoDB cursor to list of dictionaries
    products = list(results)

    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode
    # Route to fetch real-time prices
@app.route('/prices')
def get_prices():
    # Code to fetch real-time prices from the data source
    prices = {'BTC': 55000, 'ETH': 2000}  # Example data
    return jsonify(prices)

if __name__ == '__main__':
    app.run(debug=True)