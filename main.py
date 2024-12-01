import socket
import threading
from datetime import datetime
import discord
from discord.ext import commands
from requests import get
import psutil
import asyncio
import os
import json
import ast
from dotenv import load_dotenv

#TODO : Find any bugs and issues that may lurk in the code

#*  -  =  -  =  -  =  -  =  -  =  -  [ - LOGS  - ]  -  =  -  =  -  =  -  =  -  =  *# 
#*The logs are organised as such : [<timestamp> - <level>] > <text>               *#
#*The timestamp is generated automatically and formatted as YYYY-MM-DD HH:MM:SS   *#
#*The level is indicated by the user or the program, and is usually               *#
#*either as follows or whatever you want it to be                                 *#
#*INFO                  :   For information/debug purposes                        *#
#*WARNING               :   For not vital but important informations              *#
#*ALERT                 :   Big issue to take notice of                           *#
#*ERROR                 :   The user misconfigured the environment file           *#
#*  -  =  -  =  -  =  -  =  -  =  -  =  -  =  -  =  -  =  -  =  -  =  -  =  -  =  *#


def printAndLog(text:str,level:str):
    """
    Log the given text to a log file, with the according level and timestamp
    args :
        `text`  (str)   :   the text to log to the file
        `level` (str)   :   the level of the message. 
                            Could be anything, but is "INFO", "WARNING", "ALERT" and "ERROR         " in the code,
                            so you can either use that convention or do your own thing
    """
    message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {level}] > {text}"
    print(message)
    with open(f"{datetime.now().strftime('%Y-%m-%d')}-watcher.log", "a") as f:  # Use "a" mode to append
        f.write(message)
        f.close()

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    printAndLog(text="Discord token missing ! (DISCORD_TOKEN not set in the .env file)",level="ERROR")

try :
    USER_ID = int(os.getenv("USER_ID"))  # Ensure USER_ID is an integer
    if not USER_ID:
        printAndLog(text="User ID missing ! (USER_ID not set in the .env file)",level="ERROR")
except ValueError:
    printAndLog(text="User ID misconfigured ! (USER_ID not an integer in the .env file)",level="ERROR")

    
# Get the check-in interval from the .env file, with 5 as a default value
try:
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"))
    if not CHECK_INTERVAL:
        printAndLog(text="Check-in interval not set, reverting to default value of 5s",level="WARNING")
        CHECK_INTERVAL = 5
except ValueError:
    printAndLog(text="Check-in interval misconfigured ! (CHECK_INTERVAL not an integer in the .env file)",level="ERROR")

# Extract the ports to monitor from the .env file's PORTS_TO_SCAN entry.
# The ports are expected as a comma-separated string, which we split, 
# convert to integers, and store as a list.
# Extract ports to monitor from the PORTS_TO_SCAN entry in the .env file.
# The ports are expected to be a json dictionnary like {port n°:alert level}
try:
    PORTS_TO_SCAN = ast.literal_eval(os.getenv("PORTS_TO_SCAN", "{}"))
except (ValueError, SyntaxError):
    raise ValueError("PORTS_TO_SCAN must be a valid Python dictionary.")
# Get the list of ports to scan and their alert level
# Ensure all keys in PORTS_TO_SCAN are integers, and map them to a dictionnary
PORTS_TO_SCAN = {int(k): v for k, v in PORTS_TO_SCAN.items()}


# Create a Discord bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# Function to send a notification to Discord DMs
async def send_dm_notification(message:str):
    """
    Sends a notification to the given user (USER_ID) with the `message` value as the content
    args : 
        `message` (str) : the message to send the user
    """
    user = await bot.fetch_user(USER_ID)
    if user:
        await user.send(message)
    else:
        print(f"[ERROR] Unable to find user with ID {USER_ID}")


# Function to check active connections on specified ports
async def check_connections():
    known_connections = set()

    while True:
        current_connections = set()
        for conn in psutil.net_connections(kind="inet"):
            if conn.status == "ESTABLISHED" and conn.laddr.port in PORTS_TO_SCAN.keys():
                current_connections.add((conn.laddr.port, conn.raddr.ip, conn.raddr.port))

                if (conn.laddr.port, conn.raddr.ip, conn.raddr.port) not in known_connections:
                    
                    try:
                        level_key = int(PORTS_TO_SCAN[conn.laddr.port])
                    except ValueError:
                        print(f"The alert level should be an integer, not a {type(PORTS_TO_SCAN[conn.laddr.port])} {PORTS_TO_SCAN[conn.laddr.port]} !")

                    # We set the warning level from the PORTS_TO_SCAN dictionnary (using the
                    # port number as the key), with levels going as such :
                    # 1 -- INFO     > not a big deal / look into it when convenient
                    # 2 -- WARNING  > bit of an issue there, better check it out
                    # 3 -- ALERT    > there's currently a REALLY BIG PROBLEM, investigate ASAP
                    if level_key == 3:
                        level = "ALERT"
                    elif level_key == 2:
                        level = "WARNING"
                    elif level_key == 1:
                        level = "INFO"
                    else:
                        level = "ERROR          "

                    # Craft the message using python's f-strings, with useful info like the ort number,
                    # remote IP address and port, timestamp, and of course the warning level.
                    message = (f"[{level}] New connection on port {conn.laddr.port} "
                               f"from {conn.raddr.ip}:{conn.raddr.port} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(message)
                    await send_dm_notification(message)
                    printAndLog(message=message,level=level)


        # Update known connections
        known_connections = current_connections

        # Wait before checking again
        await asyncio.sleep(CHECK_INTERVAL)

# Bot event: On ready
@bot.event
async def on_ready():
    print(f"[INFO] Logged in as {bot.user}")
    print("[INFO] Monitoring started. Press Ctrl+C to stop.")
    await send_dm_notification(f"[INFO] Bot ready at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} !")
    bot.loop.create_task(check_connections())

# Start the bot
if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped.")