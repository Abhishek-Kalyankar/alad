from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests

app = Flask(__name__)

# PostgreSQL connection (update credentials as needed)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://aircraft_data_user:6PZIW63RoeCj5cthsEPTZaCeSZm2ZQEQ@dpg-d1t092emcj7s73b0mhlg-a.oregon-postgres.render.com/aircraft_data"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# AircraftData table model
class AircraftData(db.Model):
    __tablename__ = 'aircrafts'
    id = db.Column(db.Integer, primary_key=True)
    icao24 = db.Column(db.String(10))
    callsign = db.Column(db.String(10))
    origin_country = db.Column(db.String(100))
    time_position = db.Column(db.Integer)
    last_contact = db.Column(db.Integer)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    baro_altitude = db.Column(db.Float)
    on_ground = db.Column(db.Boolean)
    velocity = db.Column(db.Float)
    true_track = db.Column(db.Float)
    vertical_rate = db.Column(db.Float)
    sensors = db.Column(db.String(100))
    geo_altitude = db.Column(db.Float)
    squawk = db.Column(db.String(10))
    spi = db.Column(db.Boolean)
    position_source = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/aircrafts', methods=['GET'])
def get_aircraft_data():
    try:
        # Try to fetch from OpenSky API
        response = requests.get("https://opensky-network.org/api/states/all", timeout=5)
        response.raise_for_status()
        opensky_data = response.json()

        aircraft_list = []
        for state in opensky_data.get('states', []):
            aircraft_list.append({
                'icao24': state[0],
                'callsign': state[1],
                'origin_country': state[2],
                'time_position': state[3],
                'last_contact': state[4],
                'longitude': state[5],
                'latitude': state[6],
                'baro_altitude': state[7],
                'on_ground': state[8],
                'velocity': state[9],
                'true_track': state[10],
                'vertical_rate': state[11],
                'sensors': state[12],
                'geo_altitude': state[13],
                'squawk': state[14],
                'spi': state[15],
                'position_source': state[16],
                'timestamp': datetime.utcnow().isoformat()
            })

        return jsonify({'source': 'OpenSky', 'aircrafts': aircraft_list})

    except Exception as e1:
        try:
            # Fallback API
            fallback_response = requests.get("https://db-fv04.onrender.com/aircrafts", timeout=5)
            fallback_response.raise_for_status()
            return jsonify({'source': 'Render', 'aircrafts': fallback_response.json()})

        except Exception as e2:
            try:
                # Fallback to DB
                aircrafts = AircraftData.query.all()
                aircraft_list = []
                for a in aircrafts:
                    aircraft_list.append({
                        'icao24': a.icao24,
                        'callsign': a.callsign,
                        'origin_country': a.origin_country,
                        'time_position': a.time_position,
                        'last_contact': a.last_contact,
                        'longitude': a.longitude,
                        'latitude': a.latitude,
                        'baro_altitude': a.baro_altitude,
                        'on_ground': a.on_ground,
                        'velocity': a.velocity,
                        'true_track': a.true_track,
                        'vertical_rate': a.vertical_rate,
                        'sensors': a.sensors,
                        'geo_altitude': a.geo_altitude,
                        'squawk': a.squawk,
                        'spi': a.spi,
                        'position_source': a.position_source,
                        'timestamp': a.timestamp.isoformat()
                    })
                return jsonify({'source': 'Database', 'aircrafts': aircraft_list})

            except Exception as e3:
                return jsonify({
                    "error": "All data sources failed (OpenSky, Render, DB).",
                    "details": str(e3)
                }), 500

if __name__ == '__main__':
    app.run(debug=True)
