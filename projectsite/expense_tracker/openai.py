from openai import OpenAI
import base64
import json
import os

class OpenAIReceiptScanner:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def scan_receipt(self, image_file):
        """Use GPT-4 Vision to analyze receipt"""
        try:
            # Encode image to base64
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this receipt and extract:
                                - Total amount
                                - Date 
                                - Merchant name
                                - Tax amount
                                - Main category (food, shopping, etc.)
                                Return as JSON with these fields."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse JSON response
            result_text = response.choices[0].message.content
            # GPT might wrap JSON in ```json ```, so clean it
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
                'confidence': 'high',  # GPT is very reliable
                'raw_data': receipt_data
            }
            
        except Exception as e:
            return {'error': f'OpenAI scanning failed: {str(e)}'}