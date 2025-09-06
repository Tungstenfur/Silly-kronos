import os
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
load_dotenv()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()  # Sync slash commands with Discord
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)} ms")

@bot.tree.command(name="boop", description="boop")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Boop :3")

@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="schedule", description="Schedule an event :3")
async def schedule(
    interaction: discord.Interaction,
    event: Literal["Raid", "Patrol", "Gamenight", "Special"],
    time: int,
    host: discord.User,
    to: discord.TextChannel,
    description: str = "No description provided"
):
    color = discord.Color.dark_red()
    if event == "Raid": color = discord.Color.blue()
    elif event == "Patrol": color = discord.Color.green()
    elif event == "Gamenight": color = discord.Color.dark_blue()
    elif event == "Special": color = discord.Color.Red()
    else: event = "Unknown"
    embed = discord.Embed(
        title=f"Scheduled new event (uses UNIX time)",
        description="Event type: " + event + "\n Host: " + host.mention + "\n Time: " + "<t:"+str(time)+">" + "\n Description: " + description,
        color=discord.Color.blue()
    )
    await to.send(embed=embed)
    await interaction.response.send_message(
        f"Scheduled {event} at {time} with host {host.name}."
    )

bot.run(os.getenv("DISCORD_TOKEN"))
