#!/bin/bash

BROKER=localhost:9092
TOPICS=("screen-frames" "ml-results")

echo " clearing: ${TOPICS[*]}"

for TOPIC in "${TOPICS[@]}"
do
    echo "set for deletion: $TOPIC"

    #exec and set retention
    docker exec kafka kafka-configs --bootstrap-server $BROKER --alter \
      --entity-type topics --entity-name $TOPIC \
      --add-config retention.ms=0

    sleep 2

   
    docker exec kafka kafka-configs --bootstrap-server $BROKER --alter \
      --entity-type topics --entity-name $TOPIC \
      --delete-config retention.ms

    echo "Cleared out $TOPIC"
done

echo "All topics cleared"
