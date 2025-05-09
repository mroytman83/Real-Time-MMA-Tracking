import numpy as np
import cv2
from mss import mss
from kafka import KafkaProducer
import base64
import json
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    api_version=(2, 8),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("producer started")
sct = mss()
region = sct.monitors[1]  

frame_count = 0
start_time = time.time()
#currently ~6 frames per second, not bad at all


while True:
    sct_img = sct.grab(region)
    frame = np.array(sct_img)[:, :, :3]
    

    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')


    producer.send('screen-frames', {'image': jpg_as_text})

    #implemented to keep 6 fps 
    time.sleep(0.15)

    print("Sent frame to Kafka")
    frame_count += 1
    elapsed = time.time() - start_time
    if elapsed >= 1.0:
        print(f"FPS: {frame_count}")
        frame_count = 0
        start_time = time.time()


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

producer.close()
