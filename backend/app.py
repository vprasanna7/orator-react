import os
import logging
import json
import threading
import requests
import pyaudio
import websocket
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from flask_cors import CORS

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Hard-coded API Key
API_KEY = "6da73691953e46efa30f69ecf9e39009"

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=FRAMES_PER_BUFFER)

stop_event = threading.Event()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/start', methods=['POST'])
def start_transcription():
    logging.debug("Received request to start transcription")
    stop_event.clear()
    threading.Thread(target=transcribe_worker).start()
    return jsonify(success=True)

@app.route('/stop', methods=['POST'])
def stop_transcription():
    logging.debug("Received request to stop transcription")
    stop_event.set()
    return jsonify(success=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        headers = {
            "authorization": API_KEY,
            "content-type": "application/json"
        }
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=open(filepath, "rb")
        )

        if upload_response.status_code == 200:
            audio_url = upload_response.json()["upload_url"]

            transcript_response = requests.post(
                "https://api.assemblyai.com/v2/transcript",
                headers=headers,
                json={"audio_url": audio_url}
            )

            if transcript_response.status_code == 200:
                transcript_id = transcript_response.json()['id']
                return jsonify({'transcript_id': transcript_id}), 200
            else:
                return jsonify({'error': 'Failed to start transcription job'}), 500
        else:
            return jsonify({'error': 'Failed to upload audio file'}), 500
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/transcript/<transcript_id>', methods=['GET'])
def get_transcript(transcript_id):
    headers = {
        "authorization": API_KEY,
    }
    response = requests.get(
        f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
        headers=headers
    )

    if response.status_code == 200:
        transcript_data = response.json()
        if transcript_data['status'] == 'completed':
            return jsonify({'transcript': transcript_data['text']}), 200
        else:
            return jsonify({'status': transcript_data['status']}), 202
    else:
        return jsonify({'error': 'Failed to get transcript'}), 500

def transcribe_worker():
    logging.info("Audio streaming thread started")
    ws = websocket.WebSocketApp(
        f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
        header={"Authorization": API_KEY},
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

def on_open(ws):
    logging.info("WebSocket connection opened successfully")
    def run(*args):
        logging.info("Audio streaming thread started")
        chunk_count = 0
        while not stop_event.is_set():
            try:
                data = stream.read(FRAMES_PER_BUFFER)
                ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                chunk_count += 1
                if chunk_count % 100 == 0:
                    logging.debug(f"Sent {chunk_count} audio chunks")
            except Exception as e:
                logging.error(f"Error reading or sending audio data: {str(e)}")
    threading.Thread(target=run).start()

def on_message(ws, message):
    logging.debug(f"Received message from AssemblyAI: {message}")
    try:
        response = json.loads(message)
        message_type = response.get('message_type')

        if message_type in ['PartialTranscript', 'FinalTranscript']:
            text = response['text']
            confidence = response.get('confidence')
            audio_start = response.get('audio_start')
            audio_end = response.get('audio_end')

            logging.info(f"{message_type}: {text} (Confidence: {confidence}, Time: {audio_start}-{audio_end}ms)")
            socketio.emit('transcription', {
                'type': message_type,
                'text': text,
                'confidence': confidence,
                'audio_start': audio_start,
                'audio_end': audio_end
            })
        elif message_type == 'SessionTerminated':
            logging.info("Session terminated by AssemblyAI")
            socketio.emit('session_terminated')
        else:
            logging.warning(f"Unhandled message type: {message_type}")

    except json.JSONDecodeError:
        logging.error(f"Failed to decode message: {message}")
    except KeyError as e:
        logging.error(f"Missing expected key in message: {str(e)}")
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")

def on_error(ws, error):
    logging.error(f"WebSocket error: {str(error)}")
    socketio.emit('error', {'message': 'An error occurred with the transcription service'})

def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket closed. Status code: {close_status_code}, Message: {close_msg}")
    socketio.emit('connection_closed', {'status_code': close_status_code, 'message': close_msg})

if __name__ == "__main__":
    logging.info("Starting Flask server")
    socketio.run(app, host='127.0.0.1', port=5000)
