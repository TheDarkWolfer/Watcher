import socket
import threading
from datetime import datetime
import discord
from discord.ext import commands
from requests import get
import psutil
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the token and user ID from the environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
USER_ID = int(os.getenv("USER_ID"))  # Ensure USER_ID is an integer

# Ports to monitor
PORTS = [7, 25565, 7777]  # SSH, Minecraft and SSH-Chat
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
            if conn.status == "ESTABLISHED" and conn.laddr.port in PORTS:
                current_connections.add((conn.laddr.port, conn.raddr.ip, conn.raddr.port))

                if (conn.laddr.port, conn.raddr.ip, conn.raddr.port) not in known_connections:
                    if conn.laddr.port == 7:
                            # New connection detected - SSH, which means BIG ISSUE
                            message = (f"[ALERT] New SSH connection on port {conn.laddr.port} "
                                       f"from {conn.raddr.ip}:{conn.raddr.port} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            print(message)
                            await send_dm_notification(message)
                            log2file(conn.raddr.ip,conn.raddr.port,conn.laddr.port,"ALERT")
                    elif conn.laddr.port == 7777:
                            # New connection detected - Chat, which means "hop on to see what's what"
                            message = (f"[Info] New SSH-Chat connection on port {conn.laddr.port} "
                                       f"from {conn.raddr.ip}:{conn.raddr.port} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            print(message)
                            await send_dm_notification(message)
                            log2file(conn.raddr.ip,conn.raddr.port,conn.laddr.port,"INFO")
                    elif conn.laddr.port == 25565:
                            # New connection detected - Minecraft server, used for keeping track of who's online 
                            # rather than it being a security threat
                            message = (f"[Info] New Minecraft connection on port {conn.laddr.port} "
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