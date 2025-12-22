from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
import uuid
import math

app = Flask(__name__)
app.secret_key = 'smartcard-secret-key-change-in-production'

# In-memory storage (use database in production)
users_data = {}

# Real merchant locations near 303 Vintage Ln, Buffalo Grove, IL (42.160, -87.967)
MERCHANT_LOCATIONS = [
    # Grocery Stores
    {'name': 'Jewel-Osco', 'category': 'grocery', 'lat': 42.1705, 'lng': -87.9793},
    {'name': 'Target', 'category': 'department', 'lat': 42.1545, 'lng': -87.9685},
    {'name': 'Walmart Supercenter', 'category': 'department', 'lat': 42.1490, 'lng': -88.0156},
    {'name': 'Costco Wholesale', 'category': 'grocery', 'lat': 42.1282, 'lng': -87.9245},
    {'name': 'Trader Joes', 'category': 'grocery', 'lat': 42.1418, 'lng': -87.8965},
    {'name': 'Whole Foods Market', 'category': 'grocery', 'lat': 42.1162, 'lng': -87.8912},
    {'name': 'Mariano\'s Fresh Market', 'category': 'grocery', 'lat': 42.1892, 'lng': -87.9456},
    
    # Gas Stations
    {'name': 'Shell', 'category': 'gas', 'lat': 42.1683, 'lng': -87.9712},
    {'name': 'BP Gas Station', 'category': 'gas', 'lat': 42.1550, 'lng': -87.9825},
    {'name': 'Speedway', 'category': 'gas', 'lat': 42.1625, 'lng': -87.9598},
    {'name': 'Marathon', 'category': 'gas', 'lat': 42.1478, 'lng': -87.9715},
    {'name': 'Mobil', 'category': 'gas', 'lat': 42.1715, 'lng': -87.9865},
    
    # Dining - Buffalo Grove Town Center / The Clove Area
    {'name': 'Chick-fil-A', 'category': 'dining', 'lat': 42.1685, 'lng': -87.9745},
    {'name': 'Giordano\'s Pizza', 'category': 'dining', 'lat': 42.1688, 'lng': -87.9752},
    {'name': 'Guzman Y Gomez', 'category': 'dining', 'lat': 42.1690, 'lng': -87.9748},
    {'name': 'Sushi Grove', 'category': 'dining', 'lat': 42.1692, 'lng': -87.9743},
    {'name': 'Cooper\'s Hawk Winery', 'category': 'dining', 'lat': 42.1458, 'lng': -87.9682},
    {'name': 'Mago Grill & Cantina', 'category': 'dining', 'lat': 42.1712, 'lng': -87.9778},
    {'name': 'Egg Harbor Cafe', 'category': 'dining', 'lat': 42.1562, 'lng': -87.9695},
    {'name': 'Buffalo Wild Wings', 'category': 'dining', 'lat': 42.1535, 'lng': -87.9702},
    {'name': 'Panera Bread', 'category': 'dining', 'lat': 42.1545, 'lng': -87.9688},
    {'name': 'Five Guys', 'category': 'dining', 'lat': 42.1552, 'lng': -87.9675},
    {'name': 'Chipotle Mexican Grill', 'category': 'dining', 'lat': 42.1558, 'lng': -87.9692},
    {'name': 'Starbucks', 'category': 'dining', 'lat': 42.1548, 'lng': -87.9678},
    {'name': 'Dunkin\'', 'category': 'dining', 'lat': 42.1695, 'lng': -87.9825},
    {'name': 'Portillo\'s Hot Dogs', 'category': 'dining', 'lat': 42.1425, 'lng': -87.9758},
    {'name': 'Outback Steakhouse', 'category': 'dining', 'lat': 42.1472, 'lng': -87.9698},
    
    # Pharmacy
    {'name': 'CVS Pharmacy', 'category': 'pharmacy', 'lat': 42.1698, 'lng': -87.9792},
    {'name': 'Walgreens', 'category': 'pharmacy', 'lat': 42.1522, 'lng': -87.9685},
    {'name': 'Walgreens (McHenry)', 'category': 'pharmacy', 'lat': 42.1688, 'lng': -87.9758},
    
    # Department Stores & Shopping
    {'name': 'Kohl\'s', 'category': 'department', 'lat': 42.1532, 'lng': -87.9712},
    {'name': 'Marshalls', 'category': 'department', 'lat': 42.1542, 'lng': -87.9705},
    {'name': 'HomeGoods', 'category': 'home', 'lat': 42.1538, 'lng': -87.9698},
    {'name': 'TJ Maxx', 'category': 'department', 'lat': 42.1448, 'lng': -87.9728},
    {'name': 'Ulta Beauty', 'category': 'department', 'lat': 42.1555, 'lng': -87.9685},
    {'name': 'PetSmart', 'category': 'department', 'lat': 42.1525, 'lng': -87.9692},
    
    # Home Improvement
    {'name': 'The Home Depot', 'category': 'home', 'lat': 42.1418, 'lng': -87.9842},
    {'name': 'Lowe\'s', 'category': 'home', 'lat': 42.1392, 'lng': -88.0125},
    {'name': 'Menards', 'category': 'home', 'lat': 42.1265, 'lng': -87.9558},
    {'name': 'Ace Hardware', 'category': 'home', 'lat': 42.1658, 'lng': -87.9802},
    
    # Entertainment
    {'name': 'Bowlero Buffalo Grove', 'category': 'entertainment', 'lat': 42.1702, 'lng': -87.9768},
    {'name': 'K1 Speed Indoor Karting', 'category': 'entertainment', 'lat': 42.1445, 'lng': -87.9695},
    {'name': 'AMC Theatres', 'category': 'entertainment', 'lat': 42.1475, 'lng': -87.9672},
    {'name': 'LA Fitness', 'category': 'entertainment', 'lat': 42.1562, 'lng': -87.9708},
    
    # Nearby Shopping Centers
    {'name': 'Best Buy', 'category': 'department', 'lat': 42.1435, 'lng': -87.9685},
    {'name': 'Dick\'s Sporting Goods', 'category': 'department', 'lat': 42.1442, 'lng': -87.9692},
    {'name': 'Bed Bath & Beyond', 'category': 'home', 'lat': 42.1452, 'lng': -87.9678},
    {'name': 'Barnes & Noble', 'category': 'department', 'lat': 42.1468, 'lng': -87.9688},
    {'name': 'Total Wine & More', 'category': 'grocery', 'lat': 42.1425, 'lng': -87.9715},
    
    # Coffee & Quick Service
    {'name': 'Starbucks (Jewel)', 'category': 'dining', 'lat': 42.1708, 'lng': -87.9795},
    {'name': 'Peet\'s Coffee', 'category': 'dining', 'lat': 42.1565, 'lng': -87.9682},
    {'name': 'McDonald\'s', 'category': 'dining', 'lat': 42.1635, 'lng': -87.9758},
    {'name': 'Subway', 'category': 'dining', 'lat': 42.1672, 'lng': -87.9785},
    {'name': 'Jimmy John\'s', 'category': 'dining', 'lat': 42.1545, 'lng': -87.9695},
]

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates in miles using Haversine formula"""
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def get_user_cards(user_id):
    if user_id not in users_data:
        users_data[user_id] = {'cards': [], 'location_enabled': False}
    return users_data[user_id]['cards']

def find_best_card_for_location(user_id, lat, lng):
    """Find the best card based on nearby merchants"""
    cards = get_user_cards(user_id)
    if not cards:
        return None
    
    # Find nearby merchants (within 2 miles)
    nearby_merchants = []
    for merchant in MERCHANT_LOCATIONS:
        distance = calculate_distance(lat, lng, merchant['lat'], merchant['lng'])
        if distance <= 2.0:
            nearby_merchants.append({
                **merchant,
                'distance': distance
            })
    
    if not nearby_merchants:
        return None
    
    # Sort by distance
    nearby_merchants.sort(key=lambda x: x['distance'])
    
    # Find best card for the nearest merchant
    best_card = None
    best_value = 0
    best_merchant = nearby_merchants[0]
    
    for card in cards:
        value = 0
        # Check category bonuses
        for bonus in card.get('category_bonuses', []):
            if bonus['category'].lower() == best_merchant['category'].lower():
                value = float(bonus['rate'])
                break
        
        # If no category bonus, use base rate
        if value == 0:
            value = float(card.get('base_rate', 0))
        
        if value > best_value:
            best_value = value
            best_card = card
    
    return {
        'card': best_card,
        'merchant': best_merchant,
        'rate': best_value,
        'all_nearby': nearby_merchants,
        'location': {'lat': lat, 'lng': lng}
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

@app.route('/api/cards', methods=['GET'])
def get_cards():
    user_id = get_user_id()
    cards = get_user_cards(user_id)
    location_enabled = users_data.get(user_id, {}).get('location_enabled', False)
    return jsonify({'cards': cards, 'location_enabled': location_enabled})

@app.route('/api/cards', methods=['POST'])
def add_card():
    user_id = get_user_id()
    card_data = request.json
    
    card_data['id'] = str(uuid.uuid4())
    card_data['added_date'] = datetime.now().isoformat()
    
    if user_id not in users_data:
        users_data[user_id] = {'cards': [], 'location_enabled': False}
    
    users_data[user_id]['cards'].append(card_data)
    
    return jsonify({'success': True, 'card': card_data})

@app.route('/api/cards/<card_id>', methods=['DELETE'])
def delete_card(card_id):
    user_id = get_user_id()
    cards = get_user_cards(user_id)
    
    users_data[user_id]['cards'] = [c for c in cards if c['id'] != card_id]
    
    return jsonify({'success': True})

@app.route('/api/cards/<card_id>', methods=['PUT'])
def update_card(card_id):
    user_id = get_user_id()
    cards = get_user_cards(user_id)
    card_data = request.json
    
    for i, card in enumerate(cards):
        if card['id'] == card_id:
            card_data['id'] = card_id
            card_data['added_date'] = card.get('added_date', datetime.now().isoformat())
            users_data[user_id]['cards'][i] = card_data
            return jsonify({'success': True, 'card': card_data})
    
    return jsonify({'success': False, 'error': 'Card not found'}), 404

@app.route('/api/location/enable', methods=['POST'])
def enable_location():
    user_id = get_user_id()
    if user_id not in users_data:
        users_data[user_id] = {'cards': [], 'location_enabled': False}
    
    users_data[user_id]['location_enabled'] = True
    return jsonify({'success': True})

@app.route('/api/location/check', methods=['POST'])
def check_location():
    user_id = get_user_id()
    data = request.json
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    if not lat or not lng:
        return jsonify({'success': False, 'error': 'Invalid location'}), 400
    
    result = find_best_card_for_location(user_id, lat, lng)
    
    return jsonify({
        'success': True,
        'recommendation': result
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)