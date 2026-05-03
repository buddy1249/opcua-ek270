import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymodbus.client import ModbusSerialClient
import settings

app = FastAPI(title="EK270 Final Gateway")

# 1. Разрешение(CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = {key: 0.0 for key in settings.REGISTER_MAP}
storage["status"] = "starting"
active_connections = set()

async def modbus_poller():
    while True:
        client = ModbusSerialClient(**settings.SERIAL_CONFIG)
        try:
            if client.connect():
                for tag, params in settings.REGISTER_MAP.items():
                    res = client.read_holding_registers(address=params["address"], count=params["count"], slave=settings.SLAVE_ID)
                    if not res.isError():
                        from pymodbus.payload import BinaryPayloadDecoder
                        from pymodbus.constants import Endian
                        # Используем декодер 
                        decoder = BinaryPayloadDecoder.fromRegisters(res.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
                        storage[tag] = round(decoder.decode_32bit_float(), 4)
                        storage["status"] = "online"
                client.close()
                
                # Рассылаем данные всем подключенным по WS
                if active_connections:
                    message = {"type": "update", "data": storage}
                    for ws in list(active_connections):
                        try:
                            await ws.send_json(message)
                        except:
                            active_connections.remove(ws)
            else:
                storage["status"] = "offline"
        except Exception as e:
            storage["status"] = f"error: {str(e)}"
        
        await asyncio.sleep(settings.POLL_INTERVAL)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(modbus_poller())

@app.get("/api/data")
async def get_data():
    return storage


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
