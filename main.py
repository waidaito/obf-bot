import discord
from discord.ext import commands
import aiohttp
import io
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=".", intents=intents)

XHIDER_API_TOKEN = "edb5c387a9aa19c8d6ec496565db731f"
XHIDER_URL = "https://xhider.xyz/"

@bot.event
async def on_ready():
    print(f"Obfuscator bot {bot.user} is ready!")

@bot.command(name="obf")
async def obfuscate_lua(ctx, *, text_code: str = None):
    lua_content = ""

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            try:
                lua_content = (await attachment.read()).decode("utf-8")
            except Exception as e:
                await ctx.send(f"Error reading file: {e}")
                return
        else:
            await ctx.send("please provide a .lua or .txt file")
            return

    elif text_code:
        lua_content = text_code.strip().strip("`").replace("lua\n", "", 1)

    else:
        await ctx.send("Please add the txt or lua file.")
        return

    progress_msg = await ctx.send("wait a moment.")

    payload = {
        "action": "create_obf",
        "api_token": XHIDER_API_TOKEN,
        "preset": "Evil",
        "content": lua_content,
        "output": "console"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(XHIDER_URL, data=payload) as response:
                if response.status == 200:
                    obfuscated_code = await response.text()

                    if not obfuscated_code or not obfuscated_code.strip():
                        await progress_msg.edit(content="erro")
                        return

                    fixed_code = obfuscated_code.replace(
                        "--// This file was created by XHider v1.2 [https://discord.gg/hATuHQaQRb]",
                        "-- this file was created by 8xmj https://discord.gg/swjkGWeDM --"
                    )

                    file_data = io.BytesIO(fixed_code.encode("utf-8"))
                    discord_file = discord.File(fp=file_data, filename="obfuscated.lua")

                    await progress_msg.delete()
                    await ctx.send(
                        content=f"obfucate successfully, {ctx.author.mention}!",
                        file=discord_file
                    )

                else:
                    await progress_msg.edit(content=f"error (Status: {response.status})")

        except Exception as e:
            await progress_msg.edit(content=f"erro: {e}")

keep_alive()

bot.run(os.getenv("DISCORD_TOKEN"))
