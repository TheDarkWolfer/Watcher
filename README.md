# WATCHER
---
## What's in this repository

This tool aims to notify you when connections are attempted on your device on specific ports, and sends that information to you through a discord bot with the IP, the timestamp, and the affected service. Those informations are also logged in a file of your choosing (default being `whois_results.log`) 
There is also a small script (`get_whois_d_lmao.sh`) that you can use in order to automatically poll whois servers and ipinfo.io in order to gather information on the IPs that attempted to connect, gathered from the aforementionned logs.
If necessary, there is also an example of how the .env file for this project should be written, with the variables being already available and just needing to fill in the blanks.
---
## How to use

First, clone this repository using git and cd into it:
```
git clone https://github.com/TheDarkWolfer/Watcher
cd Watcher
```

You'll find all the necessary files, which are `main.py` and `get_whois_d_lmao.sh`. 
If you don't already, you'll need to install python v3, and the discord.py library :
```
sudo dnf install python3    # Fedora-based distros
sudo apt install python3    # Debian-based distros
sudo pacman -S python3      # Arch-based distros
pip3 install discord.py
```

After that, you'll need to create your `.env` file so that both the discord bot `main.py` and `get_whois_d_lmao.sh` can access necessary informations :

**Discord Token**
This token is necessary for the discord bot to exist. For that, you'll have to head to discord's [developper portal](https://discord.com/developers/applications), create a bot, and save the token that's provided to you in your .env file under the variable `DISCORD_TOKEN`

**User ID**
This is the ID of your DMs with the bot, which will be used to send messages directly to you. You can find that by clicking on your icon and selecting "Copy user ID". You'll need to save this as `USER_ID` in the `.env` file

**ipinfo.io token**
In order to not get rate-limited with ipinfo.io, you'll need to get a token. This can be done by logging in to ipinfo.io and copying the token they provide you as `IPINFO_TOKEN` in the `.env` file.

**Result file's name**
Pretty straightforward, you just provide the name you want to give the resulting file in the `RESULT_FILE` variable in the `.env` file.

**Ports to monitor, and alert level**
You will need to specify the ports you want the bot to watch over through the .env file. It should be formated as a json dictionnary, as such `PORTS_TO_SCAN={<port n°>:<alert level>}`, with the port number being self-explanatory and the alert level being an integer from 1 to 3, such that :
- 1 <> INFO     for non-critical services like a chatroom
- 2 <> WARNING  when the service in question should be more carefully monitored
- 3 <> ALERT    when the service is critical and access to it should be controlled as tightly as possible


You can use the `.env-EXAMPLE` file from this repository, fill in the blanks yourself, and rename it to just `.env` before use

You now have the choice between running the bot (and/or the script) from your current shell, or use the provided service file. If you choose to use a systemd service, here is what to do (Just be careful with this, the consequences are worse if you mess up with systemd) :

1. Modify the `watcher.service` file to suit your device
Look for these lines under the `[Service]` section of the file, and modify them with :
-ExecStart          : replace `/path/to/main.py` with the **absolute path** to the `main.py` file (the discord bot)
-User               : The user under whose privileges the bot should run (usually your current user) 
-WorkingDirectory   : Replace /path/to/bot/directory with the **absolute** path to the directory you cloned from github
```
...
[Service]
...
ExecStart=/usr/bin/python3 /path/to/main.py
...
User=your_username
WorkingDirectory=/path/to/bot/directory
...
```

2. Copy the `.service` file to the correct folder :
```
sudo cp watcher.service /etc/systemd/system/
```

3. Reload systemd daemon
```
sudo systemctl daemon-reload
```

4. Enable and start the bot
```
sudo systemctl enable --now watcher
```
---
## What to do with the logs ?

The logs created will be under the format `YYY-MM-DD-watcher.log`, one for each day. The bot only opens them when writing and closes them immediately after, so *in theory* you should be able to remove, move or write into them even when the bot is running. *In practice*, I advice against that, just to be safe.

You can either comb through the logs yourself, or you could use the `get_whois_d_lmao.sh` script to do that for you. It'll poll whois servers and ipinfo.io (if you have a token) and save the results of all of these queries in a file. 
Running the `get_whois_d_lmao.sh` script :
```
chmod +x get_whois_d_lmao.sh
./get_whois_d_lmao.sh
```

If you don't want to poll the servers and only log the IP addresses, use
```
./get_whois_d_lmao.sh -np # Or --no-poll
```

If you want to check every IP address even if they were already whois'd in a previous run, use
```
./get_whois_d_lmao.sh -fs # Or --from-scratch
```

It is also possible to use the maths.py script to see the source of the connections in a pie graph.
To do so, you can use the script as follows :

This will open a window containing the graph and it's legend
```
python3 ./maths.py <json file of IPs>
```

This will save the graph to the given file name (Note that a default save name would be graph-YYYY-MM-DD-HH-MM-SS.png)
```
python3 ./maths.py <json file of IPs> -s <save name> 
# You can also use --save instead of -s
```

## To-Do list
-[x] Separate WHOIS and ipinfo.io results
-[x] Add data plotting of the IP's information

## Running in a non-interactive environment

The `get_whois_d_lmao.sh` script isn't meant to be run in a non-interactive environment (cron job, etc...) but it should be possible if you ever need to automate. It will avoid printing progress information other than the runtime of the program, which you can choose to log to a file, let your system's journaling component do the work, or just send to `/dev/null` to get rid of it. Keep in mind that you'll need to make sure the script still has access to both the `.env` file and the logs created by the logging bot, as it won't function otherwise.