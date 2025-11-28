from flask import Request
import json

def validate_request(request: Request):
    try:
        if not request.is_json:
            return False, "Request must be JSON"

        data = request.get_json()

        if not data:
            return False, "Request body is empty"

        if 'document' not in data:
            return False, "Missing 'document' field"

        document = data['document']
        if not isinstance(document, str):
            return False, "Document must be a string"

        if not document:
            return False, "Document URL/data cannot be empty"

        return True, None
    except Exception as e:
        return False, f"Request validation error: {str(e)}"

def validate_response(response_dict):
    try:
        if not response_dict.get('is_success'):
            return True, None

        if 'data' not in response_dict:
            return False, "Missing 'data' field"

        data = response_dict['data']
        if not isinstance(data, dict):
            return False, "Data must be a dict"

        if 'pagewise_line_items' not in data:
            return False, "Missing 'pagewise_line_items'"

        if 'total_item_count' not in data:
            return False, "Missing 'total_item_count'"

        return True, None
    except Exception as e:
        return False, str(e)
