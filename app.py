from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re
import json
import time
import secrets

app = Flask(__name__)
CORS(app)

# Get API key from environment variable
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

@app.route('/api/verdict', methods=['POST'])
def get_verdict():
    try:
        data = request.json
        side_a = data.get('sideA', '')
        side_b = data.get('sideB', '')
        
                
        prompt = f"""You are an impartial judge. Two people are in a conflict.

Person A: {side_a}

Person B: {side_b}

Respond ONLY with valid JSON, no extra text:
{{"winner":"A","scoreA":76,"scoreB":24,"ruling":"Two sentences explaining your decision.","advice":"One sentence of actionable advice."}}

Rules: winner = "A", "B", or "tie". scoreA + scoreB = 100."""

        headers = {
            'Content-Type': 'application/json',
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': f'API request failed: {response.status_code}'
            }), 500
        
        result = response.json()
        text = ''.join([content.get('text', '') for content in result.get('content', []) if content.get('type') == 'text'])
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            return jsonify({
                'error': 'No valid JSON found in API response'
            }), 500
        
        verdict = json_match.group(0)
        verdict_data = json.loads(verdict)
        
        return jsonify(verdict_data)
        
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.secret_key = secrets.token_hex(32)
    app.run(debug=False, host='0.0.0.0', port=5000)
