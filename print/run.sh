#!/bin/bash
. settings.sh
SCRIPTDIR=$(dirname "$(readlink -f "$0")")

while true; do
  pushd "$SCRIPTDIR" > /dev/null
  ./fetch.sh "$REG_HOST"
  ./create_badges.py
  ./print.sh
  popd > /dev/null
  echo sleep $SLEEP_INTERVAL
  sleep $SLEEP_INTERVAL
  echo about to start
  sleep 2
done

