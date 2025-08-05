from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import time

app = Flask(__name__)

# PostgreSQL config
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://aircraft_data_user:6PZIW63RoeCj5cthsEPTZaCeSZm2ZQEQ@dpg-d1t092emcj7s73b0mhlg-a.oregon-postgres.render.com/aircraft_data"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# DB Model
class AircraftData(db.Model):
    __tablename__ = 'aircraft_data'

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
    # sensors = db.Column(db.String(200))  # commented out - not in DB
    geo_altitude = db.Column(db.Float)
    # squawk = db.Column(db.String(10))  # commented out - not in DB
    spi = db.Column(db.Boolean)
    position_source = db.Column(db.Integer)
    # category = db.Column(db.Integer)  # commented out - not in DB
   # timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ keep this enabled

# Cache for Render fallback
last_fallback_fetch = 0
fallback_cache = {}

@app.route('/')
def home():
    return "Aircraft Tracker API — OpenSky → Render API → Database fallback"

@app.route('/aircraftss', methods=['GET'])
def get_aircrafts():
    global last_fallback_fetch, fallback_cache

    # 1. ✅ Try OpenSky API
    try:
        response = requests.get("https://opensky-network.org/api/states/all", timeout=5)
        response.raise_for_status()
        data = response.json()

        aircrafts = [{
            'icao24': state[0],
            'callsign': state[1],
            'origin_country': state[2],
            'longitude': state[5],
            'latitude': state[6],
            'baro_altitude': state[7],
            'geo_altitude': state[13],
            'velocity': state[9],
            'on_ground': state[8]
        } for state in data.get("states", [])[:10]]

        return jsonify({'source': 'opensky', 'aircrafts': aircrafts})

    except Exception as e:
        print("⚠️ OpenSky API failed:", str(e))

        # 2. 🔁 Try Render fallback API (with caching)
        if time.time() - last_fallback_fetch <= 60 and fallback_cache:
            print("✅ Using cached fallback data")
            return jsonify({'source': 'render-backup (cached)', 'aircrafts': fallback_cache.get('aircrafts', [])})

        try:
            fallback_response = requests.get("https://db-fv04.onrender.com/db-aircrafts", timeout=5)
            fallback_response.raise_for_status()
            fallback_cache = fallback_response.json()
            last_fallback_fetch = time.time()

            return jsonify({'source': 'render-backup', 'aircrafts': fallback_cache.get('aircrafts', [])})

        except Exception as fallback_error:
            print("❌ Render fallback failed:", str(fallback_error))
            print("📦 Attempting final fallback: database query...")

            # 3. 📦 Try to fetch from your PostgreSQL database
            try:
                db_aircrafts = AircraftData.query.order_by(AircraftData.timestamp.desc()).limit(10).all()
                db_data = [{
                    'icao24': ac.icao24,
                    'callsign': ac.callsign,
                    'origin_country': ac.origin_country,
                    'longitude': ac.longitude,
                    'latitude': ac.latitude,
                    'baro_altitude': ac.baro_altitude,
                    'geo_altitude': ac.geo_altitude,
                    'velocity': ac.velocity,
                    'on_ground': ac.on_ground
                } for ac in db_aircrafts]

                return jsonify({'source': 'database-backup', 'aircrafts': db_data})

            except Exception as db_error:
                print("❌ Database fallback failed:", str(db_error))
                return jsonify({
                    'error': 'All data sources failed (OpenSky, Render, DB).',
                    'details': str(db_error)
                }), 500

if __name__ == '__main__':
    app.run(debug=True)

