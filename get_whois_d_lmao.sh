#!/bin/bash

START=$(date +%s)

# Source .env file to avoid hardcoding tokens
source .env

# Arguments handling with a case statement and a for loop
for arg in "$@"; do
    case $arg in
        # This one tells the program to re-process IPs regardless of 
        # whether or not they are present in the last output file(s)
        --from-scratch|-fs)
            FROM_SCRATCH=true
            echo -e "Ignoring previous results..."
            ;;

        # This one tells the program to not poll ipinfo.io and whois servers,
        # useful for testing or if you just need IPs
        --no-poll|-np)
            NO_POLL=true
            RESULT_FILE="IPs.log"
            echo -e "IPs will be logged to IPs.log with no polling of whois servers or ipinfo"
            ;;
    esac
done

# Extract IPs from logs
# So this one's big because we use some regex to cleanup the IPs so that it's
# easier to handle them later. First thing we do is extract the raw IP, which is easy 
# to do with awk since it's always the 9th element of the line. We then extract the 
# IPv4 address using SED, remove any local IPs as they wouldn't yield useful informations,
# remove the IPv4 to IPv6 identifier, and store all of that in the IPS variable
IPS=$(cat ./*-watcher.log | awk '{print $9}' | sed -nE '/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/p' | grep -E -v '^(10\.|127\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1]))' | sed 's/^::ffff://' | sort | uniq)

# Count how may we have, used later to provide info on overall progress
TOTAL_IPS=$(echo "$IPS" | wc -l)

# In case we have no valid IPs
if [ "$TOTAL_IPS" -eq 0 ]; then
    echo "No valid IPs found in logs."
    exit 1
fi

# Counter for all processed IPs
DONE=0

# Check for already processed IPs
if [[ $FROM_SCRATCH = "true" ]] ; then
    echo "Starting from scratch - ignoring previous results..."
else:
    # If the result file exists
    if [ -f "$RESULT_FILE" ]; then
        # We extract any block that matches "IP=[...]" from it 
        # and store them as already processed
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

    # Calculate percentage of work already done 
    PERCENT=$((DONE * 100 / TOTAL_IPS))
    
    # Only echo the percetage if in an interactive environment
    [[ -t 1 ]] && echo -ne "Progress: $PERCENT% - $DONE out of $TOTAL_IPS\r"

    # Check if polling is disabled
    if ! [[ "$NO_POLL" = "true" ]] ; then

        # Get informations from whois servers and ipinfo (the latter will work better with a token)
        WHOIS_RESULT=$(whois "$ip")
        IPINFO_RESULT=$(curl -s "ipinfo.io/$ip?token=$IPINFO_TOKEN")
    
        # Format the code result in a pleasant to read format
        {
            echo "=======[$IP]======="
            echo "IP=$ip"
            echo "-------"
            echo "WHOIS=$WHOIS_RESULT"
            echo "-------"
            echo "IPINFO=$IPINFO_RESULT"
            echo "=======[---]======="
        } >> "$RESULT_FILE" # Save it to a file
    
    # This runs if polling is indeed disabled
    else 

        # We just save the IP if polling is disabled
        {
            echo "n°$DONE - $ip"
        } >> "$RESULT_FILE"
    
    fi

    # Increment the amount of work done by one
    DONE=$((DONE + 1))

    # Calculate and display the amount of work done once again to 
    # give precise informations to the user (once again only in 
    # interactive environments)
    PERCENT=$((DONE * 100 / TOTAL_IPS))
    [[ -t 1 ]] && echo -ne "Progress: $PERCENT% - $DONE out of $TOTAL_IPS\r"
done <<< "$IPS" # We feed the list of IPs we got into the for loop

# Calculate the program's runtime
END=$(date +%s)
DURATION=$((END - START))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

# Display the runtime to the user (also shows up in non-interactive environments)
echo -e "\nScript runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s"

[[ -t 1 ]] && echo -e "\nDone!"
