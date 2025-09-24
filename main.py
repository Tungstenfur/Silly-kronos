import os
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import pandas as pd
import sqlite3
import random

db= sqlite3.connect('main.db')
cursor = db.cursor()
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
@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="init", description="Initialize the database")
async def init(interaction: discord.Interaction):
    server_id = interaction.guild.id
    table_name = f"points_{server_id}"  # Dynamically name the table
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" (user_id INTEGER PRIMARY KEY, points INTEGER, pending INTEGER)')
    db.commit()
    await interaction.response.send_message(f"Database initialized for server {server_id}.")
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)} ms")

@bot.tree.command(name="boop", description="boop")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Boop :3")

@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="schedule", description="Schedule an event :3 (uses UNIX time)")
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
    elif event == "Special": color = discord.Color.red()
    else: event = "Unknown"
    embed = discord.Embed(
        title=f"Scheduled new event",
        description="Event type: " + event + "\n Host: " + host.mention + "\n Time: " + "<t:"+str(time)+">" + "\n Description: " + description,
        color=color
    )
    await to.send(embed=embed)
    await interaction.response.send_message(
        f"Scheduled {event} at {time} with host {host.name}."
    )

@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="addpoints", description="Add points to a user")
async def addpoints(
    interaction: discord.Interaction,
    user: discord.User,
    points: int
):
    table= f"points_{interaction.guild.id}"
    cursor.execute(f'INSERT OR IGNORE INTO "{table}" (user_id, points) VALUES (?, ?)', (user.id, 0))
    cursor.execute(f'UPDATE {table} SET points = points + ? WHERE user_id = ?', (points, user.id))
    db.commit()
    cursor.execute(f'SELECT "{table}" FROM points WHERE user_id = ?', (user.id,))
    total_points = cursor.fetchone()[0]
    await interaction.response.send_message(f"Added {points} points to {user.name}. Total points: {total_points}")

@bot.tree.command(name="mypoints", description="Check your points")
async def mypoints(interaction: discord.Interaction):
    table= f"points_{interaction.guild.id}"
    cursor.execute(f'INSERT OR IGNORE INTO "{table}" (user_id, points) VALUES (?, ?)', (interaction.user.id, 0))
    cursor.execute(f'SELECT points FROM "{table}" WHERE user_id = ?', (interaction.user.id,))
    total_points = cursor.fetchone()[0]
    await interaction.response.send_message(f"You have {total_points} points.")

@app_commands.default_permissions(manage_events=True)
@bot.tree.command(name="addpendingpoints", description="Add points to a user that will be needed to get synced by an admin")
async def addpendingpoints(
    interaction: discord.Interaction,
    user: discord.User,
    points: int
):
    table= f"points_{interaction.guild.id}"
    cursor.execute(f'INSERT OR IGNORE INTO "{table}" (user_id, pending) VALUES (?, ?)', (user.id, 0))
    cursor.execute(f'UPDATE {table} SET pending = pending + ? WHERE user_id = ?', (points, user.id))
    db.commit()
    cursor.execute(f'SELECT pending FROM "{table}" WHERE user_id = ?', (user.id,))
    total_pending = cursor.fetchone()[0]
    await interaction.response.send_message(f"Added {points} pending points to {user.name}. Total pending points: {total_pending}")
@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="syncpoints", description="Sync pending points to actual points")
async def syncpoints(
    interaction: discord.Interaction,
    user: discord.User
):
    table= f"points_{interaction.guild.id}"
    cursor.execute(f'INSERT OR IGNORE INTO "{table}" (user_id, points, pending) VALUES (?, ?, ?)', (user.id, 0, 0))
    cursor.execute(f'SELECT pending FROM "{table}" WHERE user_id = ?', (user.id,))
    pending_points = cursor.fetchone()[0]
    cursor.execute(f'UPDATE "{table}" SET points = points + ?, pending = 0 WHERE user_id = ?', (pending_points, user.id))
    db.commit()
    cursor.execute(f'SELECT points FROM "{table}" WHERE user_id = ?', (user.id,))
    total_points = cursor.fetchone()[0]
    await interaction.response.send_message(f"Synchronized {pending_points} pending points to {user.name}. Total points: {total_points}")

@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="listpending", description="Lists users with pending points")
async def listpending(interaction: discord.Interaction):
    table= f"points_{interaction.guild.id}"
    cursor.execute(f'SELECT user_id, pending FROM "{table}" WHERE pending != 0')
    rows = cursor.fetchall()
    if not rows:
        await interaction.response.send_message("No users with pending points.")
        return
    message = "Users with pending points:\n"
    for user_id, pending in rows:
        user = interaction.guild.get_member(user_id)
        if user:
            message += f"{user.name}: {pending} pending points\n"
        else:
            message += f"User ID {user_id}: {pending} pending points\n"
    await interaction.response.send_message(message)

@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="exporttable", description="Export the points table as CSV")
async def exporttable(interaction: discord.Interaction):
    table= f"points_{interaction.guild.id}"
    cursor.execute(f'SELECT user_id, points, pending FROM "{table}"')
    rows = cursor.fetchall()
    if not rows:
        await interaction.response.send_message("No data to export.")
        return
    df = pd.DataFrame(rows, columns=['user_id', 'points', 'pending'])
    csv_file = f'points_{interaction.guild.id}.csv'
    df.to_csv(csv_file, index=False)
    await interaction.response.send_message(file=discord.File(csv_file))
    os.remove(csv_file)

@bot.tree.command(name="moth")
async def moth(interaction: discord.Interaction):
    moths = os.listdir('moths')
    if not moths:
        await interaction.response.send_message("No moth images found.")
        return
    moth_image = random.choice(moths)
    await interaction.response.send_message(file=discord.File(moth_image))

bot.run(os.getenv("DISCORD_TOKEN"))
