# app/image_upload.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import openai
import base64

# Blueprint setup
image_upload_bp = Blueprint('image_upload', __name__)

# Configurations
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'uploads/'

# OpenAI API key setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to process the image (this could be adjusted to your needs)
def image_to_grocery_list(image_path):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Interpret this grocery list image and return each item on the grocery list, separated by commas."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_data}},
                    ],
                }
            ],
        )
    return [item.strip() for item in response.choices[0].message.content.lower().split(',')]


# Image upload route
@image_upload_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Process the image (e.g., with OpenAI)
        try:
            result = image_to_grocery_list(file_path)
            return jsonify({"message": "File uploaded and processed successfully!", "data": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400
