from flask import Flask, render_template, request, redirect, url_for, Response
from flask_socketio import SocketIO, emit

import cv2
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

users = {}

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html', users=users.values())

@app.route('/process_login', methods=['POST'])
def process_login():
    if request.method == 'POST':
        username = request.form['username']
        devicename = request.form['devicename']  # Retrieve device name from the form
        user_id = str(uuid.uuid4())  # Generate a unique ID for the user
        users[user_id] = {'username': username, 'devicename': devicename}  # Store username and device name
        socketio.emit('update_users', {'users': list(users.values())})  # Broadcast the updated user list
        return redirect(url_for('index'))
    else:
        return "Method Not Allowed", 405


@socketio.on('disconnect')
def handle_disconnect():
    disconnected_sid = request.sid
    user_id = get_user_id_by_sid(disconnected_sid)
    if user_id in users:
        del users[user_id]  # Remove the disconnected user from the user list
        socketio.emit('update_users', {'users': list(users.values())})  # Broadcast the updated user list

def get_user_id_by_sid(sid):
    for user_id, user_sid in users.items():
        if user_sid == sid:
            return user_id
    return None

def generate_frames():
    cap = cv2.VideoCapture("rtsp://192.168.1.161:554/stream1")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/test', methods=['POST'])
def test_button():
    print("Button Clicked")
    return redirect(url_for('index'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
