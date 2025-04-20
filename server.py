from flask import Flask, render_template, jsonify
from kafka import KafkaConsumer
import threading, json
from collections import defaultdict

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
            if action in ["punch", "kick"]:  #more labels in future?
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

if __name__ == '__main__':
    app.run(debug=True)

