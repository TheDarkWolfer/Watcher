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

# Load environment variables from .env file
load_dotenv()

# Get the token and user ID from the environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))  # Ensure USER_ID is an integer

# Extract the ports to monitor from the .env file's PORTS_TO_SCAN entry.
# The ports are expected as a comma-separated string, which we split, 
# convert to integers, and store as a list.
# Extract ports to monitor from the PORTS_TO_SCAN entry in the .env file.
# The ports are expected to be a json dictionnary like {port n°:alert level}
try:
    PORTS_TO_SCAN = ast.literal_eval(os.getenv("PORTS_TO_SCAN", "{}"))
except (ValueError, SyntaxError):
    raise ValueError("PORTS_TO_SCAN must be a valid Python dictionary.")

# Ensure all keys in PORTS_TO_SCAN are integers
PORTS_TO_SCAN = {int(k): v for k, v in PORTS_TO_SCAN.items()}


CHECK_INTERVAL = 5  # Check every 5 seconds

# Create a Discord bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def log2file(ip, rport, lport, level):
    with open(f"{datetime.now().strftime('%Y-%m-%d')}-watcher.log", "a") as f:  # Use "a" mode to append
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {level}] > Connection attempt from {ip} from remote port {rport} to local port {lport}\n")

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
                        level = "ATTRIBUTION ERROR"

                    # Craft the message using python's f-strings, with useful info like the ort number,
                    # remote IP address and port, timestamp, and of course the warning level.
                    message = (f"[{level}] New connection on port {conn.laddr.port} "
                               f"from {conn.raddr.ip}:{conn.raddr.port} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(message)
                    await send_dm_notification(message)
                    log2file(conn.raddr.ip,conn.raddr.port,conn.laddr.port,"INFO")


        # Update known connections
        known_connections = current_connections

        # Wait before checking again
        await asyncio.sleep(CHECK_INTERVAL)

# Function to send a notification to Discord DMs
async def send_dm_notification(message):
    user = await bot.fetch_user(USER_ID)
    if user:
        await user.send(message)
    else:
        print(f"[ERROR] Unable to find user with ID {USER_ID}")

# Bot event: On ready
@bot.event
async def on_ready():
    print(f"[INFO] Logged in as {bot.user}")
    print("[INFO] Monitoring started. Press Ctrl+C to stop.")
    await send_dm_notification(f"Bot ready at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ma'am!")
    bot.loop.create_task(check_connections())

# Start the bot
if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped.")