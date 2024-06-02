import numpy as np
from PIL import Image
from feature_extractor import FeatureExtractor
from datetime import datetime, timedelta
from flask import Flask, request, render_template, jsonify,g
from pymongo import MongoClient
from functools import wraps
import bcrypt
import jwt


import heapq

app = Flask(__name__)

# Initialize feature extractor
fe = FeatureExtractor()

# Configure MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['inventory']
    products_collection = db['products']
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")


# Secret key for JWT
app.config['SECRET_KEY'] = 'your_secret_key'

# User credentials (replace with your actual user database)
users = {
    'user1': bcrypt.hashpw('password1'.encode('utf-8'), bcrypt.gensalt()),
    'user2': bcrypt.hashpw('password2'.encode('utf-8'), bcrypt.gensalt())
}

# Authentication decorator
def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user = data['user']
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Authorization decorator
def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user not in users:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'error': 'Missing username or password'}), 401
    if auth.username not in users:
        return jsonify({'error': 'Invalid username'}), 401
    if not bcrypt.checkpw(auth.password.encode('utf-8'), users[auth.username]):
        return jsonify({'error': 'Invalid password'}), 401
    token = jwt.encode({'user': auth.username, 'exp': datetime.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token': token})


def get_top_n_similar_images(query_feature, n=5):
    """Retrieve the top N most similar images from the database."""
    cursor = products_collection.find({}, {"image_features": 1, "image_path": 1, "name": 1, "description": 1, "date": 1})
    top_n = []

    for document in cursor:
        features = np.array(document['image_features'])
        dist = np.linalg.norm(features - query_feature)
        
        if len(top_n) < n:
            heapq.heappush(top_n, (-dist, dist, document))
        else:
            heapq.heappushpop(top_n, (-dist, dist, document))
    
    top_n.sort(reverse=True)
    return [(document['image_path'], document['name'], document['description'], document['date'], dist) for _, dist, document in top_n]

@app.route('/home', methods=['GET'])
def index():
    return render_template('welcome.html')

@app.route('/home', methods=['GET', 'POST'])
@authenticate
@authorize
def index():
    if request.method == 'POST':
        file = request.files['query_img']

        # Save the query image
        img = Image.open(file.stream)  # PIL image
        uploaded_img_path = "static/uploaded/" + datetime.now().isoformat().replace(":", ".") + "_" + file.filename
        img.save(uploaded_img_path)

        # Run search
        query = fe.extract(img)
        scores = get_top_n_similar_images(query)

        return render_template('index.html', query_path=uploaded_img_path, scores=scores)
    else:
        return render_template('index.html')

@app.route('/create', methods=['POST'])
@authenticate
@authorize
def create():
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product_date = request.form.get('product_date')
        product_desc = request.form.get('product_desc')
        file = request.files['product_image']

        # Print received data (for debugging purposes)
        print(f"Product Name: {product_name}, Product Date: {product_date}, File: {file.filename}")

        # Save the uploaded product image
        uploaded_img_path = "static/uploaded/" + datetime.now().isoformat().replace(":", ".") + "_" + file.filename
        img = Image.open(file.stream)  # PIL image
        feature = fe.extract(img)
        img.save(uploaded_img_path)

        # Convert feature to a list for storage in MongoDB
        feature_list = feature.tolist()

        # Save product data in MongoDB
        product = {
            'name': product_name,
            'description': product_desc,
            'date': product_date,
            'image_features': feature_list,
            'image_path': uploaded_img_path
        }
        products_collection.insert_one(product)

        return jsonify({"message": "Product created"}), 201

@app.route('/searchByImg', methods=['POST','GET'])
@authenticate
@authorize
def searchByImg():
    if request.method == 'POST':
        file = request.files['query_img']
        img = Image.open(file.stream)

        # Run search
        query = fe.extract(img)
        scores = get_top_n_similar_images(query)

        #return jsonify({"message": "found", "scores": scores})
        return render_template('index2.html', scores=scores)
    else:
        return render_template('index2.html')

@app.route('/searchImg', methods=['POST'])
@authenticate
@authorize
def searchImg():
    if request.method == 'POST':
        file = request.files['query_img']
        img = Image.open(file.stream)

        # Run search
        query = fe.extract(img)
        scores = get_top_n_similar_images(query)

        return jsonify({"message": "found", "scores": scores})
       

if __name__ == "__main__":
    port = 8080
    host = '0.0.0.0'
    app.run(host=host, port=port)
