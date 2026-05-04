from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re
import json
import time

app = Flask(__name__)
CORS(app)

# Your Anthropic API key
ANTHROPIC_API_KEY = "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"

@app.route('/api/verdict', methods=['POST'])
def get_verdict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        side_a = data.get('sideA', '')
        side_b = data.get('sideB', '')
        
        # Basic validation
        if not side_a or not side_b:
            return jsonify({'error': 'Both sides are required'}), 400
        
        if len(side_a) < 10 or len(side_b) < 10:
            return jsonify({'error': 'Please provide more detail (minimum 10 characters)'}), 400
        
        if len(side_a) > 800 or len(side_b) > 800:
            return jsonify({'error': 'Text too long (maximum 800 characters)'}), 400
        
        # Create prompt
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
        text = ''.join([content.get('text', '') for content in result.get('content', []) 
                       if content.get('type') == 'text'])
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            return jsonify({
                'error': 'Invalid API response format'
            }), 500
        
        try:
            verdict_data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return jsonify({
                'error': 'Could not parse API response'
            }), 500
        
        # Validate response
        required_fields = ['winner', 'scoreA', 'scoreB', 'ruling', 'advice']
        for field in required_fields:
            if field not in verdict_data:
                return jsonify({
                    'error': f'Incomplete response: missing {field}'
                }), 500
        
        # Validate scores
        if not isinstance(verdict_data['scoreA'], int) or not isinstance(verdict_data['scoreB'], int):
            return jsonify({'error': 'Invalid score format'}), 500
        
        if verdict_data['scoreA'] + verdict_data['scoreB'] != 100:
            return jsonify({'error': 'Invalid score totals'}), 500
        
        return jsonify(verdict_data)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Request timeout. Please try again.'
        }), 504
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    print("🚀 Starting Am I Wrong? app...")
    print("📍 Running on http://127.0.0.1:5000")
    print("📱 Open http://127.0.0.1:5000 in your browser")
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000
    )
