from machine import ADC, Pin
import onewire
import ds18x20
import dht
import utime
import network
import urequests

# Wi-Fi Credentials
SSID = 'data_cyber'
PASSWORD = '11223344'

# Flask Server URL
FLASK_SERVER_URL = 'http://192.168.29.95:5001/sensor'

# Initialize sensors
soil_moisture_pin = ADC(Pin(26))
light_sensor_pin = ADC(Pin(28))
ph_sensor_pin = ADC(Pin(27))
temperature_pin = Pin(22)
dht_sensor = dht.DHT11(Pin(1))  # Adjust the pin as per your connection

# Initialize the DS18B20 temperature sensor
ds_sensor = ds18x20.DS18X20(onewire.OneWire(temperature_pin))
roms = ds_sensor.scan()

# pH sensor calibration data (example values, adjust as needed)
min_adc = 15000   # ADC value corresponding to pH 4
max_adc = 50000   # ADC value corresponding to pH 10
min_ph_value = 4.0
max_ph_value = 10.0

# Functions
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        print('Connecting to Wi-Fi...')
        utime.sleep(1)
    
    print('Connected to Wi-Fi:', wlan.ifconfig())

def read_temperature():
    ds_sensor.convert_temp()
    utime.sleep_ms(750)
    if roms:
        temp = ds_sensor.read_temp(roms[0])
        return temp
    return None

def convert_adc_to_ph(adc_value):
    ph_value = min_ph_value + (adc_value - min_adc) * (max_ph_value - min_ph_value) / (max_adc - min_adc)
    return ph_value

def read_dht11():
    retries = 3
    for _ in range(retries):
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            return temperature, humidity
        except OSError:
            print("Failed to read from DHT11 sensor, retrying...")
            utime.sleep(1)
    raise RuntimeError("Failed to read from DHT11 sensor after multiple attempts.")

# Connect to Wi-Fi
connect_to_wifi(SSID, PASSWORD)

# Main loop
while True:
    try:
        # Read sensor values
        soil_moisture_value = soil_moisture_pin.read_u16()
        light_value = light_sensor_pin.read_u16()
        ph_adc_value = ph_sensor_pin.read_u16()
        ambient_temperature, ambient_humidity = read_dht11()
        soil_temperature = read_temperature()
        
        # Convert ADC values to meaningful values
        soil_moisture_percentage = (soil_moisture_value / 65535.0) * 100
        light_percentage = (light_value / 65535.0) * 100
        ph_value = convert_adc_to_ph(ph_adc_value)
        
        # Print sensor values
        print(f"Soil Moisture: {soil_moisture_percentage:.2f}%")
        print(f"Light Intensity: {light_percentage:.2f}%")
        print(f"Soil pH Value: {ph_value:.2f}")
        print(f"Soil Temperature: {soil_temperature:.2f}°C")
        print(f"Ambient Temperature: {ambient_temperature:.2f}°C")
        print(f"Ambient Humidity: {ambient_humidity:.2f}%")
        
        # Prepare data for transmission
        data = {
            "soil_moisture": soil_moisture_percentage,
            "light_intensity": light_percentage,
            "soil_ph": ph_value,
            "soil_temp": soil_temperature,
            "ambient_temp": ambient_temperature,
            "ambient_humidity": ambient_humidity
        }
        
        # Send data to Flask server
        response = urequests.post(FLASK_SERVER_URL, json=data)
        print("Server Response:", response.text)
        
    except RuntimeError as e:
        print(e)
    
    # Wait before the next reading
    utime.sleep(2)
