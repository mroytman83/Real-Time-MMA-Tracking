from flask import Flask, render_template, jsonify, Response
from kafka import KafkaConsumer
import threading, json
from collections import defaultdict
import sqlite3

app = Flask(__name__)

# TAKEN punches/ kicks
strikes_taken = {
    "1": defaultdict(int),
    "2": defaultdict(int)
}

# track grappling control time
control_time_counts = {
    "1": 0,
    "2": 0
}

def consume_kafka():
    consumer = KafkaConsumer(
        'ml-results',
        bootstrap_servers='localhost:9092',
        group_id='flask-dashboard',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest'
    )

    for message in consumer:
        msg = message.value
        predictions = msg.get("predictions", {})

        
        for fid in ["1", "2"]:
            opponent = "2" if fid == "1" else "1"

            # if kick/punch done count it as a strike TAKEN for the opponent
            action = predictions.get(fid, {}).get("action")
            if action in {"punch", "kick", "close_range_strike"}:  #more labels in future?
                #blocking not scored so its discounted
                #may use no action in the future as non-aggression, deducting points for the predicted fighter
                strikes_taken[opponent][action] += 1

            # grappling
            grappling = predictions.get(fid, {}).get("grappling")
            if grappling == "control time":
                control_time_counts[fid] += 1

        print("Strikes Taken:", dict(strikes_taken))
        print("Control Time:", control_time_counts)

#start background thread 
threading.Thread(target=consume_kafka, daemon=True).start()

@app.route('/')
def index():
    return render_template('dashboard.html', title="MMA Analysis")

@app.route('/data')
def data():
    return jsonify({
        "strikes_taken": {
            "1": dict(strikes_taken["1"]),
            "2": dict(strikes_taken["2"])
        },
        "control_time": control_time_counts
    })

@app.route('/download_data')
def download_data():
        #time series data
        conn = sqlite3.connect("data_utils/mma_predictions.db")
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, prediction_json FROM prediction_log ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()

        export = [
            {"timestamp": ts, "predictions": json.loads(pred_json)}
            for ts, pred_json in rows
        ]

        return Response(
            json.dumps(export, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=predictions.json"}
        )


if __name__ == '__main__':
    app.run(debug=True)

