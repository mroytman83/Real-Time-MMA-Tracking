from kafka import KafkaConsumer, KafkaProducer
import base64
import cv2
import numpy as np
import json
from ultralytics import YOLO
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from deep_sort_realtime.deepsort_tracker import DeepSort
from collections import Counter
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
    auto_offset_reset='latest')

track_id_to_fighter = {}
track_id_ages = {}
next_fighter_id = 1

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

        results = yolo_model.predict(frame, conf=0.6, verbose=False)
        detections = results[0].boxes

        tracks = []
        for box in detections:
            cls_id = int(box.cls)
            label = yolo_model.names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            tracks.append(([x1, y1, x2 - x1, y2 - y1], 0.9, label))

        tracked_objects = tracker.update_tracks(tracks, frame=frame)
        frame_data = {}

        visible_ids = {t.track_id for t in tracked_objects}
        for track in tracked_objects:
            track_id_ages[track.track_id] = track_id_ages.get(track.track_id, 0) + 1

        missing_fighters = set(track_id_to_fighter.keys()) - visible_ids
        if missing_fighters:
            print("⚡ Remapping fighters due to missing IDs!")
            sorted_tracks = sorted(track_id_ages.items(), key=lambda x: -x[1])
            top_two_tracks = [str(tid) for tid, _ in sorted_tracks if tid in visible_ids][:2]
            track_id_to_fighter = {}
            next_fighter_id = 1
            for tid in top_two_tracks:
                track_id_to_fighter[int(tid)] = str(next_fighter_id)
                next_fighter_id += 1

        for track in tracked_objects:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            action_label = track.get_det_class()

            if track_id not in track_id_to_fighter and next_fighter_id <= 2:
                track_id_to_fighter[track_id] = str(next_fighter_id)
                next_fighter_id += 1

            if track_id in track_id_to_fighter:
                fighter_id = track_id_to_fighter[track_id]
                if action_label not in {"no action", "stand"}:
                    frame_data.setdefault(fighter_id, {})['action'] = action_label

        grappling_preds = infer_grappling_from_frame(frame)
        for g in grappling_preds:
            g_label = g['class']
            if g_label[-1] in ('1', '2'):
                try:
                    id_num = g_label[-1]
                    grappling_name = g_label[:-1]
                    if grappling_name in {"back", "mount", "takedown", "side_control"}:
                        frame_data.setdefault(id_num, {})['grappling'] = "control time"
                except:
                    continue

        for pid, labels in frame_data.items():
            action = labels.get('action')
            grappling = labels.get('grappling')
            if action: label_counts[action] += 1
            if grappling: label_counts[grappling] += 1

        print("Frame labels:", frame_data)

        output = {
            "time_stamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            'predictions': frame_data
        }

        save_prediction(output)
        producer.send('ml-results', output)

    except Exception as e:
        print("Frame processing error:", e)





