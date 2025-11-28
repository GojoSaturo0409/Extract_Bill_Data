from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

from src.bill_extractor import BillExtractor
from src.validators import validate_request, validate_response
from config import GOOGLE_API_KEY, PORT

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found")
    extractor = BillExtractor(api_key=GOOGLE_API_KEY)
    logger.info("✅ Extractor initialized")
except Exception as e:
    logger.error(f"Failed to initialize: {e}")
    extractor = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Bill Data Extraction API (FREE - Google Gemini)',
        'version': '1.0.0',
        'api_provider': 'Google Generative AI (Gemini)'
    }), 200

@app.route('/extract-bill-data', methods=['POST'])
def extract_bill_data():
    try:
        is_valid, error = validate_request(request)
        if not is_valid:
            return jsonify({
                'is_success': False,
                'error': error,
                'data': None
            }), 400

        document_url = request.get_json()['document']
        logger.info(f"Processing: {document_url[:50]}...")

        if extractor is None:
            return jsonify({
                'is_success': False,
                'error': 'Extractor not initialized',
                'data': None
            }), 500

        result = extractor.extract(document_url)

        is_valid, validation_error = validate_response(result.dict())
        if not is_valid:
            return jsonify({
                'is_success': False,
                'error': validation_error,
                'data': None
            }), 500

        logger.info(f"✅ Success: {result.data.total_item_count} items")
        return jsonify(result.dict()), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({
            'is_success': False,
            'error': f'Internal error: {str(e)}',
            'data': None
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'is_success': False, 'error': 'Endpoint not found', 'data': None}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'is_success': False, 'error': 'Internal server error', 'data': None}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
