from kafka import KafkaConsumer, KafkaProducer
import base64
import cv2
import numpy as np
import json
from ultralytics import YOLO
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from deep_sort_realtime.deepsort_tracker import DeepSort
from collections import defaultdict, Counter
import uuid
import os
import tempfile
from dotenv import load_dotenv
import time 
from data_utils.connection import save_prediction

load_dotenv()


yolo_model = YOLO("model_weights/action_weights.pt")


grapple_model = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=os.getenv("ROBOFLOW"))

custom_configuration = InferenceConfiguration(confidence_threshold=0.1)


tracker = DeepSort(max_age=30)


label_counts = Counter()


producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    'screen-frames',
    bootstrap_servers='localhost:9092',
    group_id=f"ml-consumer-{uuid.uuid4()}",
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest'
)

# Deepsort track
track_id_to_fighter = {}
next_fighter_id = 1  # Will be 1 or 2

def infer_grappling_from_frame(frame):
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            cv2.imwrite(tmp.name, frame)
            with grapple_model.use_configuration(custom_configuration):
                result = grapple_model.infer(tmp.name, model_id="bjj3/1")
        return result['predictions']
    except Exception as e:
        print("Grappling inference error:", e)
        return []


for message in consumer:
    try:
        img_b64 = message.value['image']
        img_bytes = base64.b64decode(img_b64)
        np_img = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # run YOLO
        results = yolo_model.predict(frame, conf=0.6, verbose=False)
        detections = results[0].boxes

        tracks = []
        for box in detections:
            cls_id = int(box.cls)
            label = yolo_model.names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            tracks.append(([x1, y1, x2 - x1, y2 - y1], 0.9, label))  # format: (xywh, conf, label)

        tracked_objects = tracker.update_tracks(tracks, frame=frame)




        frame_data = {}  # Structure: {id: {'grappling': ..., 'action': ...}}

        #DEBUGGING=====================================>


        # BEFORE the loop
        print("📦 Number of tracked objects:", len(tracked_objects))
        print("🔢 Current fighter mapping:", track_id_to_fighter)
        print("🧹 Frame data so far:", frame_data)

        # Get all incoming track IDs from the tracker
        current_track_ids = {t.track_id for t in tracked_objects}

        # See if any active track_ids are not mapped to fighters
        unmapped_ids = current_track_ids - set(track_id_to_fighter.keys())

        if unmapped_ids:
            print(f"🚨 Unmapped Track IDs Detected: {unmapped_ids}")
            print(f"🔎 Current mapping: {track_id_to_fighter}")

        #DEBUGGING=====================================>

        # YOLO tracking, and once matchededdedede, assign fighter IDs
        for track in tracked_objects:


            print(f"👉 Track ID {track.track_id} - Confirmed: {track.is_confirmed()} - Detected class: {track.get_det_class()}")

            if not track.is_confirmed():
                continue
            track_id = track.track_id
            action_label = track.get_det_class()  # from YOLO
            
            # Assign track ID to fighter 1 or 2
            if track_id not in track_id_to_fighter and next_fighter_id <= 2:
                track_id_to_fighter[track_id] = str(next_fighter_id)
                next_fighter_id += 1

            #considering mapped ids
            if track_id in track_id_to_fighter:
                fighter_id = track_id_to_fighter[track_id]

                if action_label not in {"no action", "stand"}:
                    frame_data.setdefault(fighter_id, {})['action'] = action_label

        # match grappling position
        grappling_preds = infer_grappling_from_frame(frame)
        for g in grappling_preds:
            g_label = g['class']
            if g_label[-1] in ('1', '2'):
                try:
                    id_num = g_label[-1]  # 1 or 2
                    grappling_name = g_label[:-1]  # Remove the 1 or 2
                    if grappling_name=="back" or grappling_name=="mount" or grappling_name=="takedown" or grappling_name=="side_control":
                        frame_data.setdefault(id_num, {})['grappling'] = "control time"
                except:
                    continue

        # Update counts and print per person
        for pid, labels in frame_data.items():
            action = labels.get('action')
            grappling = labels.get('grappling')
            if action: label_counts[action] += 1
            if grappling: label_counts[grappling] += 1

        print("Frame labels:", frame_data)

        output={"time_stamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                'predictions': frame_data
                }
        
        #send data to database
        save_prediction(output)
        
        producer.send('ml-results', output)

    except Exception as e:
        print("Frame processing error:", e)




