import requests
import base64
import json
import logging
from typing import List, Dict, Tuple, Any
import google.generativeai as genai
from fuzzywuzzy import fuzz
import io

from src.models import (
    ExtractionResponse, ExtractionData, PageLineItems,
    BillItem, TokenUsage
)

logger = logging.getLogger(__name__)

class BillExtractor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.fuzzy_threshold = 0.85
        logger.info("BillExtractor initialized with Gemini 2.0 Flash (Handwriting Optimized)")
    
    def extract(self, document_url: str) -> ExtractionResponse:
        try:
            logger.info(f"Starting extraction for: {document_url[:50]}...")
            
            # Fetch document
            image_data = self._fetch_document(document_url)
            
            # Pre-process for handwriting (enhance OCR quality)
            image_data = self._preprocess_for_handwriting(image_data)
            
            # Convert PDF to all pages
            image_pages = self._get_all_pages(image_data, document_url)
            logger.info(f"Processing {len(image_pages)} pages")
            
            # Extract from each page
            all_pages_items = []
            total_tokens = 0
            
            for page_num, page_image in enumerate(image_pages, 1):
                logger.info(f"Extracting page {page_num}/{len(image_pages)}")
                # Further enhance each page for handwriting
                enhanced_page = self._enhance_image_for_handwriting(page_image)
                page_items, usage = self._extract_page(enhanced_page, page_num)
                all_pages_items.extend(page_items)
                total_tokens += usage.get('total', 0)
            
            # Deduplicate across all pages
            deduplicated_items = self._deduplicate_items(all_pages_items)
            
            # Calculate totals
            total_items = sum(len(page.bill_items) for page in deduplicated_items)
            
            logger.info(f"Extraction complete: {total_items} items across {len(deduplicated_items)} pages")
            
            response = ExtractionResponse(
                is_success=True,
                token_usage=TokenUsage(
                    total_tokens=total_tokens,
                    input_tokens=int(total_tokens * 0.5),
                    output_tokens=int(total_tokens * 0.5)
                ),
                data=ExtractionData(
                    pagewise_line_items=deduplicated_items,
                    total_item_count=total_items
                )
            )
            return response
        
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}", exc_info=True)
            raise
    
    def _fetch_document(self, url: str) -> bytes:
        """Fetch document from URL or data URL"""
        try:
            if url.startswith('data:'):
                logger.info("Processing data URL")
                try:
                    header, data = url.split(',', 1)
                    image_bytes = base64.b64decode(data)
                    logger.info(f"Data URL decoded: {len(image_bytes)} bytes")
                    return image_bytes
                except Exception as e:
                    logger.error(f"Failed to decode data URL: {str(e)}")
                    raise ValueError(f"Invalid data URL format: {str(e)}")
            
            logger.info(f"Fetching from: {url[:50]}...")
            
            if url.startswith('TRAINING_SAMPLES/') or url.startswith('./'):
                logger.info(f"Loading local file: {url}")
                with open(url, 'rb') as f:
                    response_content = f.read()
                logger.info(f"Local file loaded: {len(response_content)} bytes")
            else:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                response_content = response.content
            
            file_size = len(response_content)
            logger.info(f"Document fetched: {file_size} bytes")
            
            return response_content
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch: {str(e)}")
            raise ValueError(f"Failed to fetch document: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _fetch_document: {str(e)}")
            raise ValueError(f"Document processing error: {str(e)}")
    
    def _preprocess_for_handwriting(self, image_bytes: bytes) -> bytes:
        """Pre-process document to optimize for handwriting recognition"""
        try:
            import cv2
            import numpy as np
            
            # Check if PDF
            if image_bytes.startswith(b'%PDF'):
                logger.info("PDF detected - will apply handwriting optimization at page level")
                return image_bytes
            
            # Image pre-processing for handwriting
            logger.info("Applying handwriting pre-processing...")
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                logger.warning("Could not decode image, skipping pre-processing")
                return image_bytes
            
            # 1. Contrast enhancement (CLAHE - Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img = clahe.apply(img)
            logger.info("Applied CLAHE contrast enhancement")
            
            # 2. Denoise
            img = cv2.fastNlMeansDenoising(img, h=10)
            logger.info("Applied denoising")
            
            # 3. Thresholding for handwritten text clarity
            _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            logger.info("Applied binary thresholding")
            
            # Convert back to bytes
            _, buffer = cv2.imencode('.png', img)
            processed_bytes = buffer.tobytes()
            
            logger.info(f"Pre-processing complete: {len(processed_bytes)} bytes")
            return processed_bytes
            
        except ImportError:
            logger.warning("OpenCV not available - skipping pre-processing")
            return image_bytes
        except Exception as e:
            logger.warning(f"Pre-processing failed: {str(e)} - continuing without enhancement")
            return image_bytes
    
    def _enhance_image_for_handwriting(self, page_image: bytes) -> bytes:
        """Enhance individual page for better handwriting recognition"""
        try:
            from PIL import Image, ImageEnhance
            import cv2
            import numpy as np
            
            logger.info("Enhancing page for handwriting recognition...")
            
            # Open image
            img_pil = Image.open(io.BytesIO(page_image))
            
            # Convert to RGB if needed
            if img_pil.mode != 'RGB':
                img_pil = img_pil.convert('RGB')
            
            # 1. Increase sharpness (helps with handwritten text)
            enhancer = ImageEnhance.Sharpness(img_pil)
            img_pil = enhancer.enhance(2.0)
            logger.info("Applied sharpness enhancement")
            
            # 2. Increase contrast (makes handwriting more visible)
            enhancer = ImageEnhance.Contrast(img_pil)
            img_pil = enhancer.enhance(1.8)
            logger.info("Applied contrast enhancement")
            
            # 3. Increase brightness if image is dark
            enhancer = ImageEnhance.Brightness(img_pil)
            img_pil = enhancer.enhance(1.1)
            logger.info("Applied brightness adjustment")
            
            # 4. Apply deskew using OpenCV
            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2GRAY)
            coords = np.column_stack(np.where(img_cv > 0))
            angle = cv2.minAreaRect(cv2.convexHull(coords))[2]
            
            if angle < -45:
                angle = 90 + angle
            
            if abs(angle) > 1:  # Only rotate if angle is significant
                img_pil = img_pil.rotate(angle, expand=True, fillcolor='white')
                logger.info(f"Deskewed image by {angle} degrees")
            
            # Convert back to bytes
            img_byte_arr = io.BytesIO()
            img_pil.save(img_byte_arr, format='PNG', optimize=True)
            img_byte_arr.seek(0)
            
            enhanced_bytes = img_byte_arr.getvalue()
            logger.info(f"Page enhancement complete: {len(enhanced_bytes)} bytes")
            return enhanced_bytes
            
        except Exception as e:
            logger.warning(f"Page enhancement failed: {str(e)} - using original")
            return page_image
    
    def _get_all_pages(self, document_bytes: bytes, url: str) -> List[bytes]:
        """Convert document to individual page images"""
        
        if document_bytes.startswith(b'%PDF') or url.lower().endswith('.pdf'):
            logger.info("PDF detected, converting all pages to images")
            return self._convert_pdf_all_pages(document_bytes)
        
        logger.info("Single image detected")
        return [document_bytes]
    
    def _convert_pdf_all_pages(self, pdf_bytes: bytes) -> List[bytes]:
        """Convert ALL PDF pages to images with handwriting optimization"""
        try:
            from pdf2image import convert_from_bytes
            from PIL import Image
            
            logger.info(f"Converting PDF ({len(pdf_bytes)} bytes) to images with handwriting optimization...")
            
            # Higher DPI for better handwriting quality
            images = convert_from_bytes(pdf_bytes, dpi=300)  # Increased from 150
            
            if not images:
                raise ValueError("No pages found in PDF")
            
            logger.info(f"PDF has {len(images)} pages (300 DPI for handwriting)")
            
            page_images = []
            for page_num, img in enumerate(images, 1):
                logger.info(f"Processing page {page_num}/{len(images)}")
                
                # Resize if too large
                max_dimension = 4096
                if img.width > max_dimension or img.height > max_dimension:
                    ratio = max_dimension / max(img.width, img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    logger.info(f"Resizing page {page_num} from {img.size} to {new_size}")
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save to PNG bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG', optimize=True)
                img_byte_arr.seek(0)
                
                image_bytes = img_byte_arr.getvalue()
                
                if not image_bytes.startswith(b'\x89PNG'):
                    raise ValueError(f"Invalid PNG generated for page {page_num}")
                
                logger.info(f"Page {page_num} converted: {len(image_bytes)} bytes")
                page_images.append(image_bytes)
            
            logger.info(f"All {len(page_images)} pages converted successfully")
            return page_images
            
        except ImportError as e:
            logger.error(f"pdf2image not installed: {str(e)}")
            raise ValueError("PDF support not available. Install: pip install pdf2image")
        except Exception as e:
            logger.error(f"Failed to convert PDF: {str(e)}", exc_info=True)
            raise ValueError(f"PDF conversion error: {str(e)}")
    
    def _extract_page(self, image_data: bytes, page_num: int) -> Tuple[List[PageLineItems], Dict[str, int]]:
        """Extract from single page image using Gemini Vision (optimized for handwriting)"""
        
        logger.info(f"Extracting page {page_num}, image size: {len(image_data)} bytes")
        
        # Compress if too large
        if len(image_data) > 5 * 1024 * 1024:
            logger.info(f"Page {page_num}: Image > 5MB, compressing...")
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', optimize=True, quality=85)
            image_data = img_byte_arr.getvalue()
            logger.info(f"Page {page_num}: Compressed to {len(image_data)} bytes")
        
        image_base64 = base64.standard_b64encode(image_data).decode('utf-8')
        logger.info(f"Page {page_num}: Encoded to base64: {len(image_base64)} chars")
        
        # Enhanced prompt for mixed printed/handwritten documents
        prompt = """You are an expert at extracting line items from medical bills, invoices, and receipts - including those with handwritten elements, mixed formats, and poor image quality.

TASK: Extract EVERY single line item from this bill/invoice page. This is page of a multi-page document.

CRITICAL RULES:
1. Look for ANY structured data: rows with Item Name | Qty | Rate | Amount (columns may be misaligned or handwritten)
2. Extract ALL line items including handwritten entries - do NOT skip any
3. EXCLUDE totals like "Total", "Sub Total", "Grand Total", "Net Amount", "Total Amount Payable"
4. EXCLUDE headers, category names, and section titles
5. Be flexible with column alignment - handwritten bills may have irregular spacing
6. If text is unclear, make best educated guess based on context
7. For amounts, look for: price, rate, cost, amount, Rs., rupees, ₹
8. Each line item should have: item_name, item_quantity, item_rate, item_amount

WHAT TO EXTRACT (Examples - including handwritten formats):
- Printed: "2D echocardiography" qty=1, rate=1180, amount=1180
- Handwritten: "Lazivate-MF" qty=1, rate=150, amount=150
- Mixed: "Consultation" qty=2 (handwritten), rate=350 (printed), amount=700
- Partial: If only name visible, use qty=1 and rate=amount (best guess)

HANDLE VARIOUS FORMATS:
- Table format (columns aligned)
- List format (items listed)
- Handwritten notes
- Faded or blurry text
- Different currencies/symbols (Rs., ₹, $)

RETURN FORMAT - ONLY VALID JSON, nothing else:
{
    "page_type": "Bill Detail",
    "bill_items": [
        {
            "item_name": "Name from handwriting or print",
            "item_quantity": 1.0,
            "item_rate": 150.0,
            "item_amount": 150.0
        }
    ]
}

Extract ALL items from this page including handwritten ones. Return ONLY the JSON."""
        
        try:
            logger.info(f"Page {page_num}: Sending to Gemini Vision API (handwriting optimized)...")
            
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/png",
                    "data": image_base64
                }
            ])
            
            response_text = response.text
            logger.info(f"Page {page_num}: Gemini response received ({len(response_text)} chars)")
            logger.debug(f"Page {page_num} response preview: {response_text[:300]}")
            
            extracted_data = self._parse_json(response_text)
            
            if not extracted_data.get('bill_items'):
                logger.warning(f"Page {page_num}: No items extracted")
                return [PageLineItems(page_no=str(page_num), page_type="Bill Detail", bill_items=[])], \
                       {'input': 0, 'output': 0, 'total': 0}
            
            bill_items = [
                BillItem(**item) for item in extracted_data.get('bill_items', [])
            ]
            
            page_items = PageLineItems(
                page_no=str(page_num),
                page_type=extracted_data.get('page_type', 'Bill Detail'),
                bill_items=bill_items
            )
            
            # Estimate tokens
            usage = {
                'input': len(prompt.split()) * 2,
                'output': len(response_text.split()) * 2,
                'total': (len(prompt.split()) + len(response_text.split())) * 2
            }
            
            logger.info(f"Page {page_num}: Extracted {len(bill_items)} items")
            return [page_items], usage
        
        except Exception as e:
            logger.error(f"Page {page_num}: Gemini API error: {str(e)}", exc_info=True)
            return [PageLineItems(page_no=str(page_num), page_type="Bill Detail", bill_items=[])], \
                   {'input': 0, 'output': 0, 'total': 0}
    
    def _parse_json(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            try:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response_text[start:end]
                    logger.info(f"Extracted JSON from response (chars {start}-{end})")
                    return json.loads(json_str)
            except Exception as e:
                logger.error(f"Failed to extract JSON: {str(e)}")
            
            logger.warning("JSON parse failed, returning empty")
            return {'page_type': 'Bill Detail', 'bill_items': []}
    
    def _deduplicate_items(self, pages: List[PageLineItems]) -> List[PageLineItems]:
        """Remove duplicates using fuzzy matching"""
        seen_items = {}
        result_pages = []
        
        for page in pages:
            new_items = []
            
            for item in page.bill_items:
                is_duplicate = False
                
                for seen_key, seen_item in seen_items.items():
                    if self._is_duplicate(item, seen_item):
                        logger.debug(f"Duplicate detected: {item.item_name}")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    new_items.append(item)
                    seen_items[f"{item.item_name}_{item.item_amount}"] = item
            
            result_pages.append(PageLineItems(
                page_no=page.page_no,
                page_type=page.page_type,
                bill_items=new_items
            ))
        
        return result_pages
    
    def _is_duplicate(self, item1: BillItem, item2: BillItem) -> bool:
        """Check if items are duplicates using fuzzy matching"""
        
        name_similarity = fuzz.ratio(
            item1.item_name.lower(),
            item2.item_name.lower()
        ) / 100
        
        if item1.item_amount == 0 or item2.item_amount == 0:
            amount_diff = 0 if item1.item_amount == item2.item_amount else 1
        else:
            amount_diff = abs(item1.item_amount - item2.item_amount) / \
                         max(item1.item_amount, item2.item_amount)
        
        return (name_similarity > self.fuzzy_threshold and amount_diff < 0.05)
