import os
import io
import re
import string
import random
import time
import requests
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN", "TOKEN")
PRETTY_MODE = True
XHIDER_API_TOKEN = "edb5c387a9aa19c8d6ec496565db731f"
XHIDER_URL = "https://xhider.xyz/"
FREE_USER_ID = 1219951796982648913
TASK_URL = "https://link4m.net/go/TI87SLwl"
COST = 10
INITIAL_COINS = 10

COIN_DATABASE = {}

def get_coins(user_id):
    return COIN_DATABASE.get(str(user_id), INITIAL_COINS)

def set_coins(user_id, amount):
    COIN_DATABASE[str(user_id)] = amount

app = Flask('')

@app.route('/')
def home():
    return "Bot is live"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

def compress_loadstring_patterns(lua_code):
    url_pattern = r'(\w+)\s*=\s*\{\s*game:[hH]ttp[gG]et\(\s*["\'](https?://[^\s"\']+)["\']\s*\)\s*\}\s*;?'
    urls_found = re.findall(url_pattern, lua_code)
    
    for var_name, url in urls_found:
        loadstring_pattern = r'(\w+)\s*=\s*loadstring\(\s*\w+\(\s*' + var_name + r'\s*\)\s*\)\s*;?'
        if re.search(loadstring_pattern, lua_code):
            replacement_code = f'local Loader = loadstring(game:HttpGet("{url}"))'
            lua_code = re.sub(loadstring_pattern, replacement_code, lua_code)
            lua_code = re.sub(r'\b' + var_name + r'\s*=\s*\{\s*game:[hH]ttp[gG]et\(\s*["\']' + re.escape(url) + r'["\']\s*\)\s*\)\s*;?', '', lua_code)

    lua_code = re.sub(r'\n\s*\n', '\n', lua_code)
    return lua_code

def heuristic_metatable_decoder(lua_code):
    lookup_pattern = r'\(\s*["\'](?:\\.|[^"\'])*["\']\s*\)\[\s*\d{5,}\s*\]'
    lua_code = re.sub(lookup_pattern, 'nil', lua_code)
    dynamic_pattern = r'\(\s*(["\'](?:\\.|[^"\'])*["\'])\s*\)\[\s*[^\]]+\s*\]'
    lua_code = re.sub(dynamic_pattern, r'\1', lua_code)
    lua_code = re.sub(r'\.CFrame\s*\*\s*[0-9]{10,}', '.CFrame', lua_code)
    return lua_code

def sanitize_junk_expressions(lua_code):
    lines = lua_code.splitlines()
    for i, line in enumerate(lines):
        if ".Connect(" in line:
            lines[i] = re.sub(r'([\w_]+)\.([\w_]+)\.Connect\(\s*[\w_.]+\s*,\s*([\w_]+)\s*\)', r'\1.\2:Connect(\3)', line)
        
    lua_code = "\n".join(lines)

    junk_call_pattern = r'\([0-9]{10,}\)\s*\([^)]*\);?'
    lua_code = re.sub(junk_call_pattern, "", lua_code)
    junk_assignment_pattern = r'\b\w+\s*=\s*\(?[0-9]{10,}\)?\s*;?'
    lua_code = re.sub(junk_assignment_pattern, "", lua_code)
    junk_callback_pattern = r'\b\w+\s*\(\s*[0-9]{10,}\s*,\s*[0-9]{10,}\s*\);?'
    lua_code = re.sub(junk_callback_pattern, "", lua_code)

    cleaned_lines = []
    for line in lua_code.splitlines():
        stripped = line.strip()
        if not stripped or stripped == ";" or stripped.endswith("="):
            continue
        if "== " in line and " then " in line and not stripped.startswith("if"):
            line = re.sub(r'^(\s*)', r'\1 if ', line)
            if not line.endswith("end") and "local" in line:
                line = line + " end"
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def normalize_variables(lua_code):
    obfuscated_patterns = [
        r'\b[a-zA-Z_]\w*_ref\d*\b',
        r'\b[a-zA-Z_]\w*_fn\b',
        r'\br\d+\b',
        r'\bn\d+\b',
        r'\bv\d+\b'
    ]
    
    ui_and_lua_blacklist = [
        "game", "workspace", "pairs", "unpack", "table", "wait", "env",
        "Color3", "string", "loadstring", "pcall", "true", "false",
        "items", "text", "flag", "state", "callback", "name", "value", 
        "options", "default", "min", "max", "scroll", "visible", "enabled"
    ]
    
    found_vars = []
    for pattern in obfuscated_patterns:
        for match in re.findall(pattern, lua_code):
            if match not in found_vars and match not in ui_and_lua_blacklist:
                found_vars.append(match)

    placeholder_map = {}
    for idx, old_var in enumerate(found_vars, start=1):
        placeholder = f"___TEMP_VAR_XYZ_{idx}___"
        placeholder_map[placeholder] = f"var_{idx}"
        lua_code = re.sub(r'\b' + re.escape(old_var) + r'\b', placeholder, lua_code)
        
    for placeholder, clean_name in placeholder_map.items():
        lua_code = lua_code.replace(placeholder, clean_name)
        
    global_rename_map = {}

    service_capture_pattern = r'(?:(local\s+)?(\w+)\s*=\s*)?(?:game|cloneref\s*\(\s*game\s*\))[.:][gG]etService\s*\(\s*(?:game\s*,\s*)?["\'](\w+)["\']\s*\)'
    lines = lua_code.splitlines()
    for i, line in enumerate(lines):
        match = re.search(service_capture_pattern, line)
        if match:
            assigned_var = match.group(2)
            service_name = match.group(3)
            if assigned_var:
                global_rename_map[assigned_var] = service_name
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f'{indent}local {service_name} = game:GetService("{service_name}")'
            else:
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f'{indent}local {service_name} = game:GetService("{service_name}")'

    lua_code = "\n".join(lines)
    
    lines = lua_code.splitlines()
    for i, line in enumerate(lines):
        alias_match = re.search(r'(?:local\s+)?\b(var_\d+|v\d+)\b\s*=\s*\b(\w+)\b\s*;?', line)
        if alias_match:
            bad_alias = alias_match.group(1)
            good_service = alias_match.group(2)
            
            valid_services = [
                "Players", "ReplicatedStorage", "RunService", "UserInputService", 
                "Lighting", "Workspace", "CoreGui", "Teams", "SoundService", 
                "StarterGui", "TweenService", "HttpService", "TeleportService"
            ]
            
            if good_service in global_rename_map.values() or good_service in valid_services:
                global_rename_map[bad_alias] = good_service
                lines[i] = "" 
                
    lua_code = "\n".join(lines)

    lines = lua_code.splitlines()
    local_player_pattern = r'(?:(local\s+)?(\b(\w+)\b\s*=\s*)?)?\b(\w+)\b\.LocalPlayer\b'
    for i, line in enumerate(lines):
        lp_match = re.search(local_player_pattern, line)
        if lp_match:
            assigned_lp_var = lp_match.group(2)
            player_service_var = lp_match.group(4)
            service_display = "Players" if player_service_var and player_service_var.startswith("var_") else (player_service_var if player_service_var else "Players")
            if assigned_lp_var:
                global_rename_map[assigned_lp_var] = "LocalPlayer"
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f'{indent}local LocalPlayer = {service_display}.LocalPlayer'

    lua_code = "\n".join(lines)
    lines = lua_code.splitlines()

    instance_pattern = r'(?:(local\s+)?(\w+)\s*=\s*)?Instance\.new\s*\(\s*["\'](\w+)["\']\s*(?:,\s*[^)]+)?\)'
    instance_counters = {}
    for i, line in enumerate(lines):
        inst_match = re.search(instance_pattern, line)
        if inst_match:
            assigned_inst_var = inst_match.group(2)
            class_name = inst_match.group(3)
            if assigned_inst_var:
                if class_name not in instance_counters:
                    instance_counters[class_name] = 1
                else:
                    instance_counters[class_name] += 1
                clean_instance_name = f"{class_name}_{instance_counters[class_name]}"
                global_rename_map[assigned_inst_var] = clean_instance_name
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f'{indent}local {clean_instance_name} = Instance.new("{class_name}")'

    lua_code = "\n".join(lines)

    player_gui_pattern = r'\b(\w+)(?:[.:]WaitForChild\s*\(\s*["\']PlayerGui["\']\s*\)|\.PlayerGui)\b'
    for player_var in re.findall(player_gui_pattern, lua_code):
        if player_var.startswith("var_"):
            global_rename_map[player_var] = "LocalPlayer"

    player_gui_assignment = r'\b(\w+)\s*=\s*(?:LocalPlayer|\w+)(?:[.:]WaitForChild\s*\(\s*["\']PlayerGui["\']\s*\)|\.PlayerGui)'
    for pg_match in re.findall(player_gui_assignment, lua_code):
        if pg_match.startswith("var_"):
            global_rename_map[pg_match] = "PlayerGui"

    env_pattern = r'\benv\.(\w+)\s*=\s*(\w+)\b'
    for env_match in re.findall(env_pattern, lua_code):
        env_var, local_var = env_match
        target_name = global_rename_map.get(local_var, global_rename_map.get(env_var))
        if target_name:
            global_rename_map[env_var] = target_name
            global_rename_map[local_var] = target_name

    for old_name, new_name in global_rename_map.items():
        if old_name in ui_and_lua_blacklist:
            continue
        lua_code = re.sub(r'\b' + re.escape(old_name) + r'\b(?=(?:[^"\']*["\'][[^"\']*["\'])*[^"\']*$)', new_name, lua_code)

    cleaned_lines = []
    for line in lua_code.splitlines():
        if re.search(r'\bPlayerGui\s*=\s*UDim2\.new', line):
            continue
        if not line.strip(): 
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

def unflatten_control_flow(lua_code):
    block_pattern = re.compile(
        r'(?:if|elseif)\s+\w+\s*==\s*([0-9\x22\x27\w]+)\s+then\s*(.*?)(?=\s*(?:elseif|else|end\s*$))', 
        re.DOTALL
    )
    state_mutation_pattern = re.compile(r'\w+\s*=\s*([0-9\x22\x27\w]+)\s*$')

    blocks = block_pattern.findall(lua_code)
    if not blocks:
        return lua_code
        
    block_map = {}
    start_state = None
    
    state_init = re.search(r'local\s+\w+\s*=\s*([0-9\x22\x27\w]+)', lua_code)
    if state_init:
        start_state = state_init.group(1)

    for state_val, block_content in blocks:
        block_content_stripped = block_content.strip()
        lines = block_content_stripped.splitlines()
        
        next_state = None
        if lines:
            last_line = lines[-1].strip()
            mutation_match = state_mutation_pattern.search(last_line)
            if mutation_match:
                next_state = mutation_match.group(1)
                block_content_stripped = "\n".join(lines[:-1]).strip()

        block_map[state_val] = {
            "content": block_content_stripped,
            "next": next_state
        }
        if not start_state:
            start_state = state_val

    reconstructed_lines = []
    current_state = start_state
    visited_states = set()

    while current_state in block_map and current_state not in visited_states:
        visited_states.add(current_state)
        node = block_map[current_state]
        if node["content"]:
            reconstructed_lines.append(node["content"])
        current_state = node["next"]

    if reconstructed_lines:
        return "\n".join(reconstructed_lines)
        
    return lua_code

def decode_bytecode_escapes(lua_code):
    def replace_decimal(match):
        full_str = match.group(0)
        escapes = re.findall(r'\\([0-9]{3})', full_str)
        if not escapes:
            return full_str
            
        try:
            decoded = "".join(chr(int(num)) for num in escapes)
            decoded = decoded.replace('"', '\\"').replace('\n', '\\n')
            return f'"{decoded}"'
        except Exception:
            return full_str

    lua_code = re.sub(r'"(?:[^"\\]|\\.)*"', replace_decimal, lua_code)
    lua_code = re.sub(r"'(?:[^'\\]|\\.)*'", replace_decimal, lua_code)
    return lua_code

def beautify_lua(content):
    deobfuscated_output = None
    try:
        response = requests.post(
            "https://relua.lua.cz/deobfuscate",
            json={
                "filename": "script.lua",
                "source": content,
                "lua_version": "Lua51",
                "pretty": PRETTY_MODE
            },
            timeout=12
        )
        response.raise_for_status()
        result = response.json()
        if "output" in result:
            deobfuscated_output = result["output"]
    except Exception:
        deobfuscated_output = content

    step0 = decode_bytecode_escapes(deobfuscated_output)
    step1 = unflatten_control_flow(step0)
    step2 = heuristic_metatable_decoder(step1)
    step3 = sanitize_junk_expressions(step2)
    step4 = normalize_variables(step3)
    final_clean = compress_loadstring_patterns(step4)
    
    return final_clean

def fetch_url(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Failed to fetch URL: {e}")
        return None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=".", 
    intents=intents,
    activity=discord.Activity(type=discord.ActivityType.watching, name=" 8xmj | obf and dump tools")
)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

@bot.tree.command(name="addcoin", description="Add coins to a user")
async def add_coin(interaction: discord.Interaction, member: discord.Member, amount: int):
    if interaction.user.id != FREE_USER_ID:
        await interaction.response.send_message("You do not have permission!", ephemeral=True)
        return
    current = get_coins(member.id)
    new_total = current + amount
    set_coins(member.id, new_total)
    await interaction.response.send_message(f"Added {amount} coins to {member.name}. Total: {new_total}", ephemeral=True)

@bot.command(name="buycoin")
async def buy_coin(ctx):
    embed = discord.Embed(title="Purchase Coins", description="Click the button below to complete the task and receive 100 coins.", color=discord.Color.green())
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Complete Task", url=TASK_URL, style=discord.ButtonStyle.link))
    await ctx.send(embed=embed, view=view)

@bot.command(name="coin")
async def check_coin(ctx):
    if ctx.author.id == FREE_USER_ID:
        await ctx.send("Your current coin balance: **Infinite**")
    else:
        amount = get_coins(ctx.author.id)
        await ctx.send(f"Your current coin balance: **{amount}**")

@bot.command(name="topcoin")
async def top_coin(ctx):
    sorted_coins = sorted(
        [(uid, amt) for uid, amt in COIN_DATABASE.items() if int(uid) != FREE_USER_ID], 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    if not sorted_coins:
        await ctx.send("No users have coins yet!")
        return
    embed = discord.Embed(title="Top 10 Coin Leaderboard", color=discord.Color.gold())
    description = ""
    for i, (uid, amt) in enumerate(sorted_coins, 1):
        try:
            user = await bot.fetch_user(int(uid))
            description += f"{i}. {user.name}: {amt} coins\n"
        except:
            continue
    embed.description = description
    await ctx.send(embed=embed)

@bot.command(name="dump")
async def deobfuscate_cmd(ctx, *, args: str = None):
    balance = get_coins(ctx.author.id)
    if balance < COST:
        await ctx.message.reply(f"Insufficient funds! You need {COST} coins to perform this action. You currently have {balance}.")
        return
    content = None
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(('.lua', '.txt')):
            await ctx.message.reply("Please send a .lua or .txt file")
            return
        try:
            content_bytes = await attachment.read()
            content = content_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            await ctx.message.reply(f"Failed: {e}")
            return
    elif args:
        stripped_args = args.strip()
        if stripped_args.startswith(("http://", "https://")):
            url = stripped_args.strip("`")
            content = fetch_url(url)
            if not content:
                await ctx.message.reply("Failed")
                return
        else:
            content = re.sub(r'^```[a-zA-Z]*\n|```$', '', stripped_args, flags=re.MULTILINE)
    if not content or not content.strip():
        await ctx.message.reply("Please add a file / raw link")
        return
    status_msg = await ctx.message.reply("wait a moment ")
    output = beautify_lua(content)
    if not output:
        await status_msg.edit(content=f"{ctx.author.mention} Failed")
        return
    set_coins(ctx.author.id, balance - COST)
    final_output = f"-- This file was created by 8xmj https://discord.gg/swjkGWeDM --\n\n{output}"
    file_stream = io.BytesIO(final_output.encode('utf-8'))
    discord_file = discord.File(fp=file_stream, filename="message.txt")
    await status_msg.delete()
    await ctx.message.reply(content=f"{ctx.author.mention} Done. 10 coins have been deducted.", file=discord_file)

@bot.command(name="obf")
async def obfuscate_lua(ctx, *, text_code: str = None):
    balance = get_coins(ctx.author.id)
    if balance < COST:
        await ctx.send(f"Insufficient funds! You need {COST} coins to perform this action. You currently have {balance}.")
        return
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
            await ctx.send("Please add .lua / .txt file")
            return
    elif text_code:
        lua_content = text_code.strip().strip("`").replace("lua\n", "", 1)
    else:
        await ctx.send("Please add .txt / .lua file")
        return
    progress_msg = await ctx.send("wait a moment")
    payload = {"action": "create_obf", "api_token": XHIDER_API_TOKEN, "preset": "Evil", "content": lua_content, "output": "console"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(XHIDER_URL, data=payload) as response:
                if response.status == 200:
                    obfuscated_code = await response.text()
                    if not obfuscated_code or not obfuscated_code.strip():
                        await progress_msg.edit(content="Error")
                        return
                    set_coins(ctx.author.id, balance - COST)
                    fixed_code = obfuscated_code.replace("--// This file was created by XHider v1.2 [https://discord.gg/hATuHQaQRb]", "-- This file was created by 8xmj https://discord.gg/swjkGWeDM --")
                    file_data = io.BytesIO(fixed_code.encode("utf-8"))
                    discord_file = discord.File(fp=file_data, filename="obfuscated.lua")
                    await progress_msg.delete()
                    await ctx.send(content=f"Obfuscated successfully, {ctx.author.mention}! 10 coins have been deducted.", file=discord_file)
                else:
                    await progress_msg.edit(content=f"Error (Status: {response.status})")
        except Exception as e:
            await progress_msg.edit(content=f"Error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
    
