from flask import Flask, request
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)

# SQLite database setup
def init_db():
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS SensorData (
                    soil_moisture REAL,
                    light_intensity REAL,
                    soil_ph REAL,
                    soil_temp REAL,
                    ambient_temp REAL,
                    ambient_humidity REAL,
                    timestamp_utc TEXT,
                    timestamp_local TEXT,
                    time_zone TEXT
                )''')
    conn.commit()
    conn.close()

@app.route('/sensor', methods=['POST'])
def sensor_data():
    data = request.get_json()

    soil_moisture = data['soil_moisture']
    light_intensity = data['light_intensity']
    soil_ph = data['soil_ph']
    soil_temp = data['soil_temp']
    ambient_temp = data['ambient_temp']
    ambient_humidity = data['ambient_humidity']
    
    # Capture the current UTC time
    now_utc = datetime.now(pytz.utc)

    # Convert to local time zone (change 'Asia/Kolkata' if needed)
    time_zone = pytz.timezone('Asia/Kolkata')
    local_time = now_utc.astimezone(time_zone)

    # Store the UTC and local timestamps, and the time zone
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute('''INSERT INTO SensorData 
                 (soil_moisture, light_intensity, soil_ph, soil_temp, ambient_temp, ambient_humidity, 
                  timestamp_utc, timestamp_local, time_zone)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (soil_moisture, light_intensity, soil_ph, soil_temp, ambient_temp, ambient_humidity, 
               now_utc.strftime("%Y-%m-%d %H:%M:%S"), local_time.strftime("%Y-%m-%d %H:%M:%S"), time_zone.zone))
    conn.commit()
    conn.close()
    
    return "Data stored successfully", 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001)  # Ensure different port from the other app
