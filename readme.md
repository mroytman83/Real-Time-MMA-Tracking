# 🥋 Real-Time MMA Prediction Dashboard

This project captures screen frames, performs real-time inference using YOLO, and visualizes fighter activity via a live web dashboard.

## 🔧 Tech Stack

- Python (YOLOv8, Roboflow Inference SDK)
- Kafka (Apache + Confluent Docker images)
- Flask (for dashboard + API)
- D3.js (frontend visualizations)
- DeepSORT (tracking)
- Docker Virtualization

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
$ sudo/brew install screen
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
- Built with D3.js + Flask
- Kafka powers the real-time data stream

---

## TODO / Improvements

- [ ] Persist predictions using SQLite(most likely or Redis overkill)
- [ ] Add round-by-round breakdowns
- [ ] Log confidence scores for predictions
- [ ] Include total damage tracking (aggregate actions)





