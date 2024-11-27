#!/bin/bash

START=$(date +%s)

#Sourc .env file to get the IPINFO access token
source .env

for arg in "$@"; do
    case $arg in
        --from-scratch|-fs)
            FROM_SCRATCH=true
            break
            ;;
    esac
done

# Extract IPs from logs
IPS=$(cat ./*-watcher.log | awk '{print $9}' | sed -nE '/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/p' | grep -E -v '^(10\.|127\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1]))' | sed 's/^::ffff://' | uniq)

TOTAL_IPS=$(echo "$IPS" | wc -l)

if [ "$TOTAL_IPS" -eq 0 ]; then
    echo "No valid IPs found in logs."
    exit 1
fi

RESULT_FILE="whois_results.log"
DONE=0

# Check for already processed IPs
if [[ $FROM_SCRATCH = "true" ]] ; then
    echo "Starting from scratch - ignoring previous results..."
else:
    if [ -f "$RESULT_FILE" ]; then
        PROCESSED_IPS=$(grep -Eo 'IP=.*' "$RESULT_FILE" | cut -d'=' -f2)
    else
        PROCESSED_IPS=""
    fi
fi

# Main processing loop
while read -r ip; do
    # Skip already processed IPs
    if echo "$PROCESSED_IPS" | grep -qw "$ip"; then
        echo "Skipping already processed IP: $ip"
        continue
    fi

    PERCENT=$((DONE * 100 / TOTAL_IPS))
    [[ -t 1 ]] && echo -ne "Progress: $PERCENT% - $DONE out of $TOTAL_IPS\r"

    WHOIS_RESULT=$(whois "$ip")
    IPINFO_RESULT=$(curl -s "ipinfo.io/$ip?token=$IPINFO_TOKEN")
    
    {
        echo "=======[$IP]======="
        echo "IP=$ip"
        echo "-------"
        echo "WHOIS=$WHOIS_RESULT"
        echo "-------"
        echo "IPINFO=$IPINFO_RESULT"
        echo "=======[---]======="
    } >> "$RESULT_FILE"

    DONE=$((DONE + 1))

    PERCENT=$((DONE * 100 / TOTAL_IPS))
    [[ -t 1 ]] && echo -ne "Progress: $PERCENT% - $DONE out of $TOTAL_IPS\r"
done <<< "$IPS"

END=$(date +%s)
DURATION=$((END - START))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

echo -e "\nScript runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s"

[[ -t 1 ]] && echo -e "\nDone!"
