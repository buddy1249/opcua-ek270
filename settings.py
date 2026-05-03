# Настройки порта
SERIAL_CONFIG = {
    "port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "parity": "N",
    "stopbits": 1,
    "bytesize": 8,
    "timeout": 3
}

# Настройки протокола
SLAVE_ID = 1
POLL_INTERVAL = 5

# Карта регистров (адреса уже со смещением -1)
REGISTER_MAP = {
    "density": {"address": 324, "count": 2, "type": "float32"},
    "temperature": {"address": 316, "count": 2, "type": "float32"},
    "pressure": {"address": 310, "count": 2, "type": "float32"}
}
