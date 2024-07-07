import pyaudio
import websockets
import asyncio
import base64
import json

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
API_KEY = '6da73691953e46efa30f69ecf9e39009'

p = pyaudio.PyAudio()
stream = p.open(
   format=FORMAT,
   channels=CHANNELS,
   rate=RATE,
   input=True,
   frames_per_buffer=FRAMES_PER_BUFFER
)

async def send_receive():
   print('Connecting websocket')
   async with websockets.connect(
       f'wss://api.assemblyai.com/v2/realtime/ws?sample_rate={RATE}',
       extra_headers=(('Authorization', API_KEY),),
       ping_interval=5,
       ping_timeout=20
   ) as websocket:
       await asyncio.sleep(0.1)
       print('Receiving messages')
       async def send():
           while True:
               try:
                   data = stream.read(FRAMES_PER_BUFFER)
                   data = base64.b64encode(data).decode("utf-8")
                   json_data = json.dumps({"audio_data":str(data)})
                   await websocket.send(json_data)
               except websockets.exceptions.ConnectionClosedError as e:
                   print(e)
                   assert e.code == 4008
                   break
               except Exception as e:
                   print(e)
                   break
               await asyncio.sleep(0.01)
          
           return True
      
       async def receive():
           while True:
               try:
                   result_str = await websocket.recv()
                   result = json.loads(result_str)
                   if 'text' in result:
                       print(result['text'])
               except websockets.exceptions.ConnectionClosedError as e:
                   print(e)
                   assert e.code == 4008
                   break
               except Exception as e:
                   print(e)
                   break
      
       send_result, receive_result = await asyncio.gather(send(), receive())

def main():
   loop = asyncio.get_event_loop()
   loop.run_until_complete(send_receive())
   loop.close()

if __name__ == "__main__":
   main()