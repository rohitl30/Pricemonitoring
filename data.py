import pandas as pd
from pymongo import MongoClient

df = pd.read_excel("products.xlsx")

client = MongoClient("mongodb://localhost:27017/")
db = client["pricemonitoring"]
collection = db["products"]

data = df.to_dict(orient='records')

collection.insert_many(data)

print("Data inserted successfully into MongoDB.")