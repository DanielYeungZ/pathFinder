# app.py
from flask import Flask, jsonify
from mongoengine import connect
from routes import user_bp, building_bp

app = Flask(__name__)

connect(
    db='pathFinder',
    host='mongodb+srv://db1:VIotwHFXr3WA1JiT@cluster0.ohmao.mongodb.net/',
    tls=True,
    tlsAllowInvalidCertificates=True
)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(building_bp, url_prefix='/api')

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Flask API!"


# Define a simple API endpoint
@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello, World!"})


if __name__ == '__main__':
    app.run(debug=True, port=8080)
