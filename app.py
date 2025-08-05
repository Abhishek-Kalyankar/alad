from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@hostname:port/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Aircraft model with correct fields
class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icao24 = db.Column(db.String(10))
    callsign = db.Column(db.String(10))
    origin_country = db.Column(db.String(50))
    time_position = db.Column(db.BigInteger)
    last_contact = db.Column(db.BigInteger)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    baro_altitude = db.Column(db.Float)
    on_ground = db.Column(db.Boolean)
    velocity = db.Column(db.Float)
    true_track = db.Column(db.Float)
    vertical_rate = db.Column(db.Float)
    geo_altitude = db.Column(db.Float)
    squawk = db.Column(db.String(10))
    spi = db.Column(db.Boolean)
    position_source = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create all tables
with app.app_context():
    db.create_all()

# Endpoint to insert aircraft data
@app.route('/aircrafts', methods=['POST'])
def add_aircraft():
    try:
        data = request.get_json()
        aircraft = Aircraft(
            icao24=data.get('icao24'),
            callsign=data.get('callsign'),
            origin_country=data.get('origin_country'),
            time_position=data.get('time_position'),
            last_contact=data.get('last_contact'),
            longitude=data.get('longitude'),
            latitude=data.get('latitude'),
            baro_altitude=data.get('baro_altitude'),
            on_ground=data.get('on_ground'),
            velocity=data.get('velocity'),
            true_track=data.get('true_track'),
            vertical_rate=data.get('vertical_rate'),
            geo_altitude=data.get('geo_altitude'),
            squawk=data.get('squawk'),
            spi=data.get('spi'),
            position_source=data.get('position_source'),
        )
        db.session.add(aircraft)
        db.session.commit()
        return jsonify({"message": "Aircraft data saved", "id": aircraft.id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check route
@app.route('/')
def index():
    return jsonify({"message": "Aircraft tracking API is running"})


if __name__ == '__main__':
    app.run(debug=True)
