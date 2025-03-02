from flask import Blueprint, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes.script import openai_bp
from routes.stores import stores_bp
from routes.imageupload import image_upload_bp



from routes.stores import stores_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['GOOGLE_MAPS_KEY'] = os.getenv('GOOGLE_MAPS_KEY')
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
    
    app.register_blueprint(stores_bp)
    app.register_blueprint(openai_bp)
    app.register_blueprint(image_upload_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
