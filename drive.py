from flask import Flask
import socketio
import eventlet
import numpy as np
import cv2
from tensorflow.keras.models import load_model
import base64
from io import BytesIO
from PIL import Image


sio = socketio.Server()   # khởi tạo web server bằng socketio
app = Flask(__name__)     # khởi tạo web application bằng flask
speed_limit = 10


def img_preprocess(img):
    img = img[60:135, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img/255
    return img


@sio.on('telemetry')
def telemetry(sid, data):  # data là image Simulator gửi về
    speed = float(data['speed'])
    # image được mã hóa theo kiểu dữ liệu base64 vì vậy phải decode. BytesIO tạo buffer module để có thể xem ảnh. Image.open đọc ảnh để xử lí ảnh
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    # vì ảnh đưa vào model phải là 4D-array trong khi ảnh chụp là 3D-array
    image = np.array([image])
    steering_angle = float(model.predict(image))
    throttle = 1.0 - speed/speed_limit  # giới hạn tốc độ tối đa là 10
    print('Steering angle: {}\tThrottle: {}\tSpeed: {}'.format(
        steering_angle, throttle, speed))
    send_control(steering_angle, throttle)


# kết nối với phần mềm Simulator
@sio.on('connect')  # message #disconnect
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)


# send_control gửi parameter steering angle và throttle cho phần mềm Simulator để điều khiển xe
def send_control(steering_angle, throttle):
    sio.emit('steer', data={                          # 'steer' là tên event, data là dữ liệu muốn emit(phát)
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })


if __name__ == '__main__':
    model = load_model('model.h5')
    # phần mềm trung gian kết nối server với client
    app = socketio.Middleware(sio, app)
    # tạo interface giúp client gửi request lên server
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
