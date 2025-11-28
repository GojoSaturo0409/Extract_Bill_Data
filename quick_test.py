#!/usr/bin/env python3
import requests
import base64
import json
import sys
from pathlib import Path

API_URL = "http://localhost:5000/extract-bill-data"

def test_bill_extraction(image_path):
    if not Path(image_path).exists():
        print(f"❌ ERROR: File not found: {image_path}")
        return

    print(f"📄 Testing: {image_path}")
    print(f"{'='*60}")

    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        print(f"✅ Image loaded ({len(image_data)} bytes)")

        image_base64 = base64.b64encode(image_data).decode('utf-8')

        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        mime_type = mime_types.get(ext, 'image/png')

        data_url = f"data:{mime_type};base64,{image_base64}"

        print(f"📤 Sending to API...")
        response = requests.post(
            API_URL,
            json={'document': data_url},
            timeout=60
        )

        result = response.json()

        print(f"{'='*60}")

        if result.get('is_success'):
            print(f"✅ EXTRACTION SUCCESSFUL\n")

            data = result['data']
            print(f"📊 RESULTS:")
            print(f"   Total items: {data['total_item_count']}")
            print(f"   Tokens: {result['token_usage']['total_tokens']}")

            print(f"\n📋 LINE ITEMS:")
            for page in data['pagewise_line_items']:
                print(f"   Page {page['page_no']} ({page['page_type']}):")
                for item in page['bill_items']:
                    print(f"      • {item['item_name']}: ₹{item['item_amount']}")
        else:
            print(f"❌ FAILED: {result.get('error')}")

        print(f"\n{'='*60}")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if len(sys.argv) < 2:
    print("Usage: python quick_test.py <image_path>")
    print("Example: python quick_test.py TRAINING_SAMPLES/sample_1.png")
    sys.exit(1)

test_bill_extraction(sys.argv[1])
