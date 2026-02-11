from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import uuid
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# LOAD ENV VARIABLES
load_dotenv()

app = Flask(__name__)
CORS(app)

# ==============================
# MongoDB
# ==============================
client = MongoClient(os.getenv("MONGO_URI"))
db = client["charvi_maggam_hub"]
bookings_col = db["bookings"]
gallery_col = db["gallery"]

# ==============================
# Cloudinary (CORRECT)
# ==============================
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# ==============================
# Admin Auth (Simple Token)
# ==============================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_TOKEN = None

def check_admin(req):
    return req.headers.get("Authorization") == ADMIN_TOKEN

# ==============================
# ADMIN LOGIN
# ==============================
@app.route("/admin/login", methods=["POST"])
def admin_login():
    global ADMIN_TOKEN
    data = request.json

    if data.get("password") == ADMIN_PASSWORD:
        ADMIN_TOKEN = str(uuid.uuid4())
        return jsonify({"success": True, "token": ADMIN_TOKEN})

    return jsonify({"success": False}), 401

# ==============================
# CREATE BOOKING (USER)
# ==============================
@app.route("/booking", methods=["POST"])
def create_booking():
    data = request.json

    booking = {
        "booking_id": "CMH-" + uuid.uuid4().hex[:6].upper(),
        "name": data["name"],
        "phone": data["phone"],
        "service": data["service"],
        "amount": data["amount"],
        "status": "Pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    bookings_col.insert_one(booking)

    return jsonify({
        "success": True,
        "booking_id": booking["booking_id"]
    })

# ==============================
# ADMIN – GET BOOKINGS
# ==============================
@app.route("/admin/bookings", methods=["GET"])
def get_bookings():
    if not check_admin(request):
        return jsonify({"message": "Unauthorized"}), 403

    return jsonify(list(bookings_col.find({}, {"_id": 0})))

# ==============================
# ADMIN – UPDATE STATUS
# ==============================
@app.route("/admin/update-status", methods=["PUT"])
def update_status():
    if not check_admin(request):
        return jsonify({"message": "Unauthorized"}), 403

    data = request.json
    bookings_col.update_one(
        {"booking_id": data["booking_id"]},
        {"$set": {"status": data["status"]}}
    )
    return jsonify({"success": True})

# ==============================
# ADMIN – UPLOAD IMAGE
# ==============================
@app.route("/admin/upload-image", methods=["POST"])
def upload_image():
    print("📩 Upload request received")

    print("Auth header:", request.headers.get("Authorization"))
    print("Admin token:", ADMIN_TOKEN)

    if not check_admin(request):
        print("❌ Unauthorized")
        return jsonify({"message": "Unauthorized"}), 403

    if "image" not in request.files:
        print("❌ No image in request.files")
        return jsonify({"message": "No image"}), 400

    image = request.files["image"]
    print("✅ Image filename:", image.filename)

    upload = cloudinary.uploader.upload(image, folder="charvi_gallery")
    print("✅ Uploaded to Cloudinary")

    gallery_col.insert_one({
        "url": upload["secure_url"],
        "public_id": upload["public_id"]
    })

    print("✅ Saved to MongoDB")

    return jsonify({"success": True})


# ==============================
# GET GALLERY (PUBLIC)
# ==============================
@app.route("/gallery", methods=["GET"])
def get_gallery():
    return jsonify(list(gallery_col.find({}, {"_id": 0})))

# ==============================
# ADMIN – DELETE IMAGE
# ==============================
@app.route("/admin/delete-image", methods=["DELETE"])
def delete_image():
    if not check_admin(request):
        return jsonify({"message": "Unauthorized"}), 403

    data = request.json
    cloudinary.uploader.destroy(data["public_id"])
    gallery_col.delete_one({"url": data["url"]})

    return jsonify({"success": True})

# ==============================
# HOME TEST
# ==============================
@app.route("/")
def home():
    return "Backend running successfully 🚀"

# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

