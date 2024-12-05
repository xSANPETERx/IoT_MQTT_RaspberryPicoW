import network
from umqtt.robust import MQTTClient
import time
import sys
import machine
from bme280 import BME280  # Importa la librería personalizada

# Configuración WiFi y ThingSpeak
WIFI_SSID = 'S4NP1'
WIFI_PASSWORD = 'LAFAMILIAESPRIMERO'
THINGSPEAK_MQTT_CLIENT_ID = b"KzoCETsWIBsyGjovIBQ1BBM"
THINGSPEAK_MQTT_USERNAME = b"KzoCETsWIBsyGjovIBQ1BBM"
THINGSPEAK_MQTT_PASSWORD = b"3eiqAGKY9zjSwp3GUnJBwuFm"
THINGSPEAK_CHANNEL_ID = b'2767059'

# Configuración de pines I2C
I2C_SCL = 5  # Cambia según tu conexión
I2C_SDA = 4  # Cambia según tu conexión

# Inicializa WiFi
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# Espera conexión WiFi
MAX_ATTEMPTS = 20
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:
    attempt_count += 1
    time.sleep(1)

if attempt_count == MAX_ATTEMPTS:
    print('No se pudo conectar al WiFi.')
    sys.exit()

# Conexión MQTT a ThingSpeak
client = MQTTClient(server=b"mqtt3.thingspeak.com",
                    client_id=THINGSPEAK_MQTT_CLIENT_ID,
                    user=THINGSPEAK_MQTT_USERNAME,
                    password=THINGSPEAK_MQTT_PASSWORD,
                    ssl=False)

try:
    client.connect()
except Exception as e:
    print(f'Error al conectar con MQTT: {e}')
    sys.exit()

# Inicializa el sensor BME280
i2c = machine.I2C(0, scl=machine.Pin(I2C_SCL), sda=machine.Pin(I2C_SDA))
sensor = BME280(i2c=i2c)

# Publicar datos periódicamente
PUBLISH_PERIOD_IN_SEC = 10

while True:
    try:
        # Obtiene los valores del sensor
        temperature = sensor.read_temperature() / 100.0  # Convertir a °C
        pressure = sensor.read_pressure() / 256.0 / 100.0  # Convertir a hPa
        humidity = sensor.read_humidity() / 1024.0  # Convertir a %

        # Construye el payload MQTT
        credentials = bytes(f"channels/{THINGSPEAK_CHANNEL_ID.decode('utf-8')}/publish", 'utf-8')
        payload = bytes(f"field1={temperature:.2f}&field2={pressure:.2f}&field3={humidity:.2f}\n", 'utf-8')

        # Publica en ThingSpeak
        client.publish(credentials, payload)

        # Debug de los valores
        print(f"Temperatura: {temperature:.2f} °C, Presión: {pressure:.2f} hPa, Humedad: {humidity:.2f} %")

        # Espera el siguiente ciclo
        time.sleep(PUBLISH_PERIOD_IN_SEC)

    except KeyboardInterrupt:
        print('Interrupción del usuario. Saliendo...')
        client.disconnect()
        wifi.disconnect()
        break

    except Exception as e:
        print(f"Error: {e}")
        break