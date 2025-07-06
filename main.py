import asyncio
import websockets
import json
import time

TOKEN = "Cc9v7BAcM7ImeX9"
montos = [1.00, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30]
posicion_actual = 0
perdio = False

async def run_bot():
    global perdio, posicion_actual
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"authorize": TOKEN}))
        await ws.recv()
        print("✅ Autenticado correctamente")

        while True:
            await ws.send(json.dumps({"ticks": "R_10"}))
            tick_data = await ws.recv()
            tick = json.loads(tick_data)
            ultimo_digito = int(str(tick["tick"]["quote"])[-1])

            digito_que_evito = 5
            monto = 5.0 if perdio else montos[posicion_actual]

            print(f"\n📉 Último dígito: {ultimo_digito}")
            print(f"🎯 Apuesto a que NO salga el dígito: {digito_que_evito}")
            print(f"💰 Monto: ${monto:.2f}")

            await ws.send(json.dumps({
                "buy": 1,
                "price": monto,
                "parameters": {
                    "amount": monto,
                    "basis": "stake",
                    "contract_type": "DIGITDIFF",
                    "currency": "USD",
                    "duration": 1,
                    "duration_unit": "t",
                    "symbol": "R_10",
                    "barrier": str(digito_que_evito)
                }
            }))

            buy_response = json.loads(await ws.recv())
            if "error" in buy_response:
                print("❌ Error:", buy_response["error"]["message"])
                await asyncio.sleep(2)
                continue

            contract_id = buy_response["buy"]["contract_id"]
            print("📤 Orden enviada. ID:", contract_id)

            await ws.send(json.dumps({
                "proposal_open_contract": 1,
                "contract_id": contract_id
            }))

            while True:
                result_data = await ws.recv()
                result = json.loads(result_data)

                if "proposal_open_contract" in result:
                    status = result["proposal_open_contract"]["status"]
                    if status == "won":
                        print("✅ ¡Ganaste!")
                        perdio = False
                        posicion_actual = 0
                        break
                    elif status == "lost":
                        print("❌ Perdiste")
                        perdio = True
                        if posicion_actual < len(montos) - 1:
                            posicion_actual += 1
                        else:
                            posicion_actual = 0
                        break

            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_bot())
