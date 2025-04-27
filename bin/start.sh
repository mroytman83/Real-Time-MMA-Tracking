#!/bin/bash


screen -dmS mma_project

#each consumer
screen -S mma_project -X screen -t CONSUMER bash -c "source vid_env/bin/activate; python consumer.py; exec bash"
screen -S mma_project -X screen -t PRODUCER bash -c "source vid_env/bin/activate; python producer.py; exec bash"
screen -S mma_project -X screen -t SERVER bash -c "source vid_env/bin/activate; python server.py; exec bash"

echo "All services started in mma_project!"
echo "To attach: screen -r mma_project"