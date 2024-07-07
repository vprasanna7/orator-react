import os
import json
import logging
import pyaudio
import websocket
import threading
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode=None)

# AssemblyAI setup
API_KEY = "6da73691953e46efa30f69ecf9e39009"
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000

# PyAudio setup
audio = pyaudio.PyAudio()
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)

stop_audio = threading.Event()

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('start_transcription')
def handle_start_transcription():
    global stop_audio
    stop_audio.clear()
    threading.Thread(target=transcribe_worker).start()
    logger.info('Transcription started')
    return {'status': 'started'}

@socketio.on('stop_transcription')
def handle_stop_transcription():
    global stop_audio
    stop_audio.set()
    logger.info('Transcription stopped')
    return {'status': 'stopped'}

def transcribe_worker():
    headers = {
        'authorization': API_KEY,
    }
    url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}"

    def on_message(ws, message):
        try:
            data = json.loads(message)
            logger.info(f"Received message from AssemblyAI: {data}")
            if 'text' in data:
                logger.info(f"Transcription received: {data['text']}")
                event_data = {'text': data['text'], 'type': data.get('message_type')}
                logger.info(f"Emitting live_transcription event: {event_data}")
                socketio.emit('live_transcription', event_data, namespace='/')
                logger.info(f"Emission complete. Event data: {event_data}")
        except Exception as e:
            logger.error(f"Error in on_message: {str(e)}")

    def on_error(ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")

    def on_open(ws):
        logger.info("WebSocket connection opened to AssemblyAI")
        def send_audio():
            while not stop_audio.is_set():
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                except Exception as e:
                    logger.error(f"Error sending audio data: {str(e)}")
                    break
            logger.info("Stopped sending audio data")
        threading.Thread(target=send_audio).start()

    ws = websocket.WebSocketApp(
        url,
        header=headers,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()

@socketio.on('test_socket')
def test_socket():
    logger.info("Emitting test transcription event")
    socketio.emit('live_transcription', {'text': 'Test message', 'type': 'TestTranscript'}, namespace='/')
    logger.info("Emitted test live_transcription event")
    return {'status': 'test_sent'}

@app.route('/test_emit')
def test_emit():
    test_data = {'text': 'This is a test emission', 'type': 'TestTranscript'}
    socketio.emit('live_transcription', test_data, namespace='/')
    logger.info(f"Test emit sent: {test_data}")
    return jsonify({'message': 'Test emission sent'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)