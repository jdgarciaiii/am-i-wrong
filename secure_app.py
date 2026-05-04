from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re
import json
from werkzeug.middleware.proxy_fix import ProxyFix
import hashlib
import secrets

app = Flask(__name__)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# Trust proxy headers for SSL
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'], 
     methods=['POST'], allow_headers=['Content-Type'])

# Get API key from environment variable (more secure)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 
    "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")

# Rate limiting (simple in-memory store)
rate_limit_store = {}

def validate_input(text, max_length=800):
    """Validate and sanitize user input"""
    if not isinstance(text, str):
        raise ValueError("Invalid input type")
    
    # Remove potentially harmful content
    text = re.sub(r'[<>"\']', '', text)
    
    # Length validation
    if len(text) > max_length:
        raise ValueError(f"Text too long (max {max_length} characters)")
    
    if len(text.strip()) < 10:
        raise ValueError("Text too short (minimum 10 characters)")
    
    return text.strip()

def rate_limit_check(client_ip):
    """Simple rate limiting"""
    current_time = int(time.time())
    if client_ip in rate_limit_store:
        requests = rate_limit_store[client_ip]
        # Remove old requests (older than 1 minute)
        requests = [req_time for req_time in requests if current_time - req_time < 60]
        if len(requests) >= 10:  # 10 requests per minute
            return False
        requests.append(current_time)
    else:
        rate_limit_store[client_ip] = [current_time]
    
    return True

@app.route('/api/verdict', methods=['POST'])
def get_verdict():
    try:
        # Get client IP for rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Rate limiting
        if not rate_limit_check(client_ip):
            return jsonify({
                'error': 'Too many requests. Please try again later.'
            }), 429
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        side_a = data.get('sideA', '')
        side_b = data.get('sideB', '')
        
        # Validate inputs
        try:
            side_a = validate_input(side_a)
            side_b = validate_input(side_b)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Check API key
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith('sk-ant-api03'):
            return jsonify({
                'error': 'API key not properly configured'
            }), 500
        
        # Create secure prompt
        prompt = f"""You are an impartial judge. Two people are in a conflict.

Person A: {side_a}

Person B: {side_b}

Respond ONLY with valid JSON, no extra text:
{{"winner":"A","scoreA":76,"scoreB":24,"ruling":"Two sentences explaining your decision.","advice":"One sentence of actionable advice."}}

Rules: winner = "A", "B", or "tie". scoreA + scoreB = 100."""

        headers = {
            'Content-Type': 'application/json',
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'User-Agent': 'AmIWrong-App/1.0'
        }
        
        payload = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        # Make secure API request with timeout
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=payload,
            timeout=30,
            verify=True  # SSL verification
        )
        
        if response.status_code != 200:
            app.logger.error(f"API Error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'API service temporarily unavailable'
            }), 503
        
        result = response.json()
        text = ''.join([content.get('text', '') for content in result.get('content', []) 
                       if content.get('type') == 'text'])
        
        # Extract JSON safely
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
        
        # Validate response structure
        required_fields = ['winner', 'scoreA', 'scoreB', 'ruling', 'advice']
        for field in required_fields:
            if field not in verdict_data:
                return jsonify({
                    'error': f'Incomplete API response: missing {field}'
                }), 500
        
        # Validate scores
        if not (isinstance(verdict_data['scoreA'], int) and isinstance(verdict_data['scoreB'], int)):
            return jsonify({'error': 'Invalid score format'}), 500
        
        if verdict_data['scoreA'] + verdict_data['scoreB'] != 100:
            return jsonify({'error': 'Invalid score totals'}), 500
        
        return jsonify(verdict_data)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Request timeout. Please try again.'
        }), 504
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request error: {str(e)}")
        return jsonify({
            'error': 'Network error. Please try again.'
        }), 503
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'version': '1.0.0'
    })

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    import time
    
    # Generate a secure session key
    app.secret_key = secrets.token_hex(32)
    
    # Run in production mode
    app.run(
        debug=False,  # Disable debug in production
        host='127.0.0.1',
        port=5000,
        ssl_context='adhoc'  # Enable HTTPS for testing
    )
