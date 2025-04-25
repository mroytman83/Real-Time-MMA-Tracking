import sqlite3
import json
import time

conn = sqlite3.connect("data_utils/mma_predictions.db", check_same_thread=False)
cursor = conn.cursor()



cursor.execute("""
CREATE TABLE IF NOT EXISTS prediction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    prediction_json TEXT NOT NULL
)
""")

def save_prediction(prediction_dict):
    timestamp = prediction_dict["time_stamp"]
    json_data = json.dumps(prediction_dict["predictions"])
    cursor.execute("INSERT INTO prediction_log (timestamp, prediction_json) VALUES (?, ?)", (timestamp, json_data))
    conn.commit()
