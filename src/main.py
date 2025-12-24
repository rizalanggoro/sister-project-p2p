from aes_crypto import aes_encrypt, aes_decrypt
from flask import Flask, request, render_template
from flask_socketio import SocketIO
import socket
import json
import time
import argparse
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

PEER_HOST = None
PEER_PORT = None
PEERS = [
    {"host": "127.0.0.1", "port": 5001},
    {"host": "127.0.0.1", "port": 5002},
    {"host": "127.0.0.1", "port": 5003},
]

received_messages = []

@app.route('/', methods=['GET'])
def index():
    other_peers = [p for p in PEERS if not (p["host"] == PEER_HOST and p["port"] == PEER_PORT)]
    return render_template(
        "index.html",
        sent=False,
        peer_host=PEER_HOST,
        peer_port=PEER_PORT,
        peers=other_peers
    )

@app.route('/send_message', methods=['POST'])
def send_message_api():
    data = request.get_json()
    target_host = data.get('host')
    target_port = int(data.get('port'))
    sender_name = data.get('name')
    text = data.get('text')
    send_message(target_host, target_port, sender_name, text)
    return {'status': 'ok'}

@app.route('/messages')
def get_messages():
    print(f"[INFO] Sending {len(received_messages)} messages to web client")
    return json.dumps(received_messages), 200, {'Content-Type': 'application/json'}

def send_message(target_host, target_port, sender, text):
    try:
        ts = time.time()
        msg_obj = {
            "from": sender,
            "text": text,
            "timestamp": ts,
            "outgoing": True
        }

        received_messages.append(msg_obj)
        
        msg_to_send = dict(msg_obj)
        msg_to_send.pop("outgoing", None)
        
        message = json.dumps(msg_to_send).encode()
        encrypted = aes_encrypt(message)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_host, target_port))
            s.sendall(encrypted)
    except Exception as e:
        print(f"[ERROR] {e}")

def receive_messages():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PEER_HOST, PEER_PORT))
    server.listen(5)
    print(f"[INFO] WebPeer listening for messages on {PEER_HOST}:{PEER_PORT}")
    while True:
        client_socket, addr = server.accept()
        try:
            encrypted = client_socket.recv(4096)
            if encrypted:
                try:
                    data = aes_decrypt(encrypted)
                    message = json.loads(data.decode())
                except Exception as e:
                    print(f"[ERROR] Decrypt/Decode failed: {e}")
                    client_socket.close()
                    continue
                
                if "timestamp" not in message:
                    message["timestamp"] = time.time()
                received_messages.append(message)
                
                print(f"[RECEIVED from {addr}] {message['from']}: {message['text']}")
                print(f"[INFO] Total messages received: {len(received_messages)}")
                
                socketio.emit('new_message', message)
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            client_socket.close()

def main():
    global PEER_HOST, PEER_PORT, NAME, PEERS
    parser = argparse.ArgumentParser(description="Peer-to-peer messaging app")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind the peer server')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind the peer TCP server')
    parser.add_argument('--webport', type=int, default=8000, help='Port for the web (Flask) server')
    args = parser.parse_args()

    PEER_HOST = args.host
    PEER_PORT = args.port
    WEB_PORT = args.webport

    t = threading.Thread(target=receive_messages, daemon=True)
    t.start()
    socketio.run(app, port=WEB_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
