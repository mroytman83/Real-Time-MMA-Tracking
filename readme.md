# 🥋 Real-Time MMA Action Tracking Dashboard


## Introduction
The initial idea behind this project was to analyze the performance and fighting styles across different eras of martial arts. However, my biggest challenge was the lack of data for fights. With the UFC being the largest MMA promotion in the world, the only available statistics are summary statistics for each fight available on [UFC Stats](http://ufcstats.com/). These stats are highly aggregated—offering totals like significant strikes, control time, or takedowns—but they omit crucial context such as timestamps, strike sequences, positional changes, and fighter movement. Without frame-level or even second-by-second data, it's impossible to build accurate models of fight dynamics or understand the timing and effectiveness of specific techniques. Not to mention that the data gathered during the fights is the byproduct of human "clickers" marking down strikes, submissions, and start/end times for so-called control time. 

Taking some inspiration from a paper, ["Video-Based Detection of Combat Positions and Automatic Scoring in Jiu-jitsu"](https://dl.acm.org/doi/10.1145/3552437.3555707),  I became motivated to build a building real-time, computer vision–based analytics system capable of detecting and classifying fighter actions frame-by-frame during MMA bouts. The granularity of the data yielded from the system can unlock several powerful applications: fighters and coaches can better analyze performance, trends, and tendencies over time(just like the Fighting Nerds; Analysts can track momentum swings and stylistic matchups across bouts; and promoters or commissions could potentially use the data to introduce real-time feedback or scoring overlays during broadcasts.

Another paper that inspired me was ["FightTracker: Real-time predictive analytics for Mixed
Martial Arts bouts"](https://arxiv.org/pdf/2312.11067), which demonstrates how access to in-round, time-series data can significantly improve the transparency and predictive accuracy of MMA judging. The real-time system's video-first, per-frame approach enhances fidelity and opens the door to automated judging systems that are less subjective, more explainable, and more consistent. With every grappling exchange, strike type, and positional control logged in real-time, judges (or algorithms) can be supported by empirical timelines of fighter dominance. Implementing such a system at a larger scale can boost fan engagement by demystifying scorecards and reducing controversy around decisions—making MMA more analytically sound and competitively fair.


## 🔧 Tech Stack

This system is built to perform real-time video analytics on MMA fights with minimal latency, while being modular enough for deployment and future extension. The core components include:

Python + YOLOv8 (Ultralytics)
YOLOv8 serves as the primary object detection model, identifying key fighter actions (e.g., punch, kick, block) frame by frame. Inference runs locally for speed, using ultralytics' efficient APIs.

Roboflow Inference SDK
Used for specialized grappling position detection via a second model hosted on Roboflow. This allows decoupling of lightweight local detection (strikes) and cloud-based inference (grappling), improving maintainability. This is currently in place because I've had issues training a grappling model with good accuracy. As the project develops, this is set for huge improvement🚀

Apache Kafka
Kafka handles high-throughput streaming of video frames from a producer (screen capture) to a consumer (inference pipeline). Messages are serialized as JSON, allowing flexible integration of future metadata (e.g. frame quality, FPS, etc.).

DeepSORT
An online multi-object tracking algorithm that links detection boxes across frames and assigns consistent IDs to fighters. Combined with fighter ID mapping logic, this ensures stable tracking even in fast-moving, occluded scenes.

Flask + D3.js
A lightweight Flask backend serves a dashboard API and static frontend, where D3.js renders real-time charts showing actions, control time, and strike breakdowns per fighter. This combination enables both data capture and interpretation in a unified UI.

 Docker (Apache + Confluent Kafka images)
Kafka, Zookeeper, and related services run in Docker containers using minimal orchestration. Docker provides isolation and reproducibility, while the core inference system runs natively to maintain performance.



---

### 1. Start Docker

Make sure Docker is running:

```bash
$ docker --version
```

---

### 2. Start Zookeeper and Kafka Using Docker Compose

Use the provided `docker-compose.yml` to start Kafka services:

```bash
$ docker-compose up -d
```

---

### 3. Setting Up VENV 

In the following order, run:

```bash
$ python -m venv vid_env
$ source vid_env/bin/activate
$ pip install -r requirements.txt   
```

### 4. Running in Screen (still dev mode)
```bash
$ sudo apt /brew install screen
$ bash bin/start.sh
```
Use Ctrl+A plus shortcuts like " to list windows, N/P to switch, K to kill a window, and screen -X -S mma_project quit to fully exit.

---

## 🔄 Resetting Kafka Topics

To clear data from topics (e.g., when restarting a demo), run:

```bash
$ bash bin/clear_topics.sh
```
---

## 📊 Dashboard Features

- Real-time bar graph of **control time** per fighter
- Dynamic display of **strikes absorbed** (punches, kicks)
- Real-time data stream

---

## Further Considerations and Tasks for Improvement 
- [ ] Train and implement a better grappling model
- [ ] Resolve Deepsort inconsistencies
- [ ] Improve visualization style 
- [ ] Add round-by-round breakdowns
- [ ] Log confidence scores for predictions( perhaps predictions for scoring the bout?)
- [ ] Include total damage tracking (aggregate actions)






