import google.generativeai as genai
import base64
import json
import os
import PIL.Image
import io

class GeminiReceiptScanner:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def scan_receipt(self, image_file):
        """Use Gemini Pro Vision to analyze receipt"""
        try:
            # Reset file pointer to beginning
            image_file.seek(0)
            
            # Convert to PIL Image for Gemini
            image = PIL.Image.open(image_file)
            
            prompt = """Analyze this receipt and extract:
            - Total amount
            - Date 
            - Merchant name
            - Tax amount
            - Main category (food, shopping, etc.)
            Return as JSON with these fields."""
            
            response = self.model.generate_content([
                prompt,
                image
            ])
            
            # Parse JSON response
            result_text = response.text
            # Gemini might wrap JSON in ```json ```, so clean it
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1]
                
            receipt_data = json.loads(result_text)
            
            return {
                'amount': receipt_data.get('total_amount'),
                'date': self._parse_date(receipt_data.get('date')),
                'merchant': receipt_data.get('merchant_name', 'Unknown'),
                'tax': receipt_data.get('tax_amount'),
                'category': receipt_data.get('category'),
                'confidence': 'high',
                'raw_data': receipt_data
            }
            
        except Exception as e:
            return {'error': f'Gemini scanning failed: {str(e)}'}

    def _parse_date(self, date_string):
        """Parse date string (keep your existing implementation)"""
        # Keep your existing date parsing logic here
        return date_string