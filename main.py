from flask import Flask, jsonify
from mongoengine import connect
from flask_cors import CORS
from routes import user_bp, building_bp
from routes.imageRoute import image_bp
from factory import app, celery

connect(
    db="pathFinder",
    host="mongodb+srv://db1:VIotwHFXr3WA1JiT@cluster0.ohmao.mongodb.net/",
    tls=True,
    tlsAllowInvalidCertificates=True,
    uuidRepresentation="standard",
)

# Apply CORS to each blueprint explicitly
# CORS(user_bp, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": "*"}})
# CORS(
#     building_bp,
#     resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": "*"}},
# )
# CORS(
#     image_bp, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": "*"}}
# )

app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(building_bp, url_prefix="/api")
app.register_blueprint(image_bp, url_prefix="/api")


@app.route("/", methods=["GET"])
def home():
    return "Welcome to PathFinder API"


@app.route("/api/hello", methods=["GET"])
def hello_world():
    return jsonify({"message": "Hello, World!"})


if __name__ == "__main__":
    app.run(debug=True, port=8080)
