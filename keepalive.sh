#! /bin/bash

LOG_FILE="/home/langestefan/projects/haweatherstation/haweatherstation.txt"

case "$(pidof python3 | wc -w)" in

0)  echo "Restarting weatherstation process: $(date)" >> "$LOG_FILE"
    cd ~/projects && source haweatherstation/weatherstation/bin/activate && nohup python3 -m haweatherstation &
    ;;
1)  # all ok
    ;;
*)  echo "Removed duplicate weatherstation: $(date)" >> "$LOG_FILE"
	pid=$(pidof python3 | awk '{print $1}')
    kill "$pid" >> "$LOG_FILE" 2>&1
    ;;
esac
