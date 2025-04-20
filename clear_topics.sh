#!/bin/bash

BROKER=localhost:9092
TOPICS=("screen-frames" "ml-results")

echo "⚠️  Clearing topics: ${TOPICS[*]}"

for TOPIC in "${TOPICS[@]}"
do
    echo "👉 Clearing topic: $TOPIC"

    # Set retention.ms to 0 to delete messages immediately
    docker exec kafka kafka-configs --bootstrap-server $BROKER --alter \
      --entity-type topics --entity-name $TOPIC \
      --add-config retention.ms=0

    sleep 2

    # Restore default retention
    docker exec kafka kafka-configs --bootstrap-server $BROKER --alter \
      --entity-type topics --entity-name $TOPIC \
      --delete-config retention.ms

    echo "✅ Cleared $TOPIC"
done

echo "🎉 All topics cleared."
