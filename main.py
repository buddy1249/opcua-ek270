import asyncio
import struct
import can
import uvicorn
from fastapi import FastAPI
from asyncua import Server, ua

app = FastAPI(title="CAN Telemetry Gateway")

# Глобальное хранилище данных
storage = {"voltage": 0.0, "current": 0.0, "status": "searching_bus"}
opcua_nodes = {}

async def init_opcua():
    """Настройка и запуск OPC UA сервера"""
    try:
        server = Server()
        await server.init()
        # В режиме host используем 0.0.0.0
        server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        
        uri = "http://buro1440.can"
        idx = await server.register_namespace(uri)
        
        # Создаем объект и переменные в дереве OPC UA
        obj = await server.nodes.objects.add_object(idx, "Satellite_Data")
        opcua_nodes["v"] = await obj.add_variable(idx, "Voltage", 0.0)
        opcua_nodes["i"] = await obj.add_variable(idx, "Current", 0.0)
        
        # Разрешаем запись в ноды (для клиентов)
        for node in opcua_nodes.values():
            await node.set_writable()
            
        await server.start()
        print("🚀 OPC UA Server started on port 4840")
        return server
    except Exception as e:
        print(f"❌ OPC UA Error: {e}")

async def can_reader():
    """Читает данные из SocketCAN vcan0"""
    global storage # Указываем, что работаем с глобальным словарем
    print("📡 CAN Reader started on vcan0...")
    
    while True:
        try:
            with can.interface.Bus(channel='vcan0', interface='socketcan') as bus:
                storage["status"] = "connected"
                while True:
                    msg = bus.recv(timeout=1.0)
                    if msg:
                        # Разбор Напряжения
                        if msg.arbitration_id == 0x101:
                            # unpack возвращает кортеж (val,), берем первый элемент [0]
                            val = struct.unpack('>f', msg.data)[0]
                            storage["voltage"] = round(float(val), 2)
                            if "v" in opcua_nodes:
                                await opcua_nodes["v"].write_value(float(val))
                        
                        # Разбор Тока
                        elif msg.arbitration_id == 0x102:
                            val = struct.unpack('>f', msg.data)[0]
                            storage["current"] = round(float(val), 2)
                            if "i" in opcua_nodes:
                                await opcua_nodes["i"].write_value(float(val))
                                
                    await asyncio.sleep(0.01)
        except Exception as e:
            print(f"❌ CAN Error: {e}")
            storage["status"] = f"error: {e}"
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup():
    # 1. Сначала запускаем OPC UA
    await init_opcua()
    # 2. Затем запускаем поллер в фоне
    asyncio.create_task(can_reader())

@app.get("/telemetry")
async def get_telemetry():
    """Эндпоинт для получения текущего состояния телеметрии"""
    return storage

if __name__ == "__main__":
    # Запуск API на порту 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
