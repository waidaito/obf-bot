import os
import io
import re
import string
import random
import json
import requests
import discord
from discord.ext import commands
from discord import app_commands
from datetime import date
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN", "TOKEN")
PRETTY_MODE = True

FREE_USER_ID = 1219951796982648913
TASK_URL = "https://link4m.net/go/TI87SLwl"
COST_WEAREDEV = 10
COST_8XMS = 3000
DATA_FILE = "data.json"

def load_data():
   if os.path.exists(DATA_FILE):
       with open(DATA_FILE, "r") as f:
           try: return json.load(f)
           except: return {"coins": {}, "last_claim": {}, "settings": {}}
   return {"coins": {}, "last_claim": {}, "settings": {}}

def save_data(data):
   with open(DATA_FILE, "w") as f:
       json.dump(data, f)

DATA = load_data()

def get_coins(user_id):
   if int(user_id) == FREE_USER_ID: return 999999999
   return DATA["coins"].get(str(user_id), 50)

def set_coins(user_id, amount):
   DATA["coins"][str(user_id)] = amount
   save_data(DATA)

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
   if not lua_code: return ""
   url_pattern = r'(\w+)\s*=\s*\{\s*game:[hH]ttp[gG]et\(\s*["\'](https?://[^\s"\']+)["\']\s*\)\s*\r*\}\s*;?'
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
   if not lua_code: return ""
   lookup_pattern = r'\(\s*["\'](?:\\.|[^"\'])*["\']\s*\)\[\s*\d{5,}\s*\]'
   lua_code = re.sub(lookup_pattern, 'nil', lua_code)
   dynamic_pattern = r'\(\s*(["\'](?:\\.|[^"\'])*["\'])\s*\)\[\s*[^\]]+\s*\]'
   lua_code = re.sub(dynamic_pattern, r'\1', lua_code)
   lua_code = re.sub(r'\.CFrame\s*\*\s*[0-9]{10,}', '.CFrame', lua_code)
   return lua_code

def sanitize_junk_expressions(lua_code):
   if not lua_code: return ""
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
   if not lua_code: return ""
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
   if not lua_code: return ""
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
   if not lua_code: return ""
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
   if not content or not content.strip(): return None
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

   if not deobfuscated_output: return None
   step0 = decode_bytecode_escapes(deobfuscated_output)
   step1 = unflatten_control_flow(step0)
   step2 = heuristic_metatable_decoder(step1)
   step3 = sanitize_junk_expressions(step2)
   step4 = normalize_variables(step3)
   final_clean = compress_loadstring_patterns(step4)
   
   return final_clean

def safe_math_eval(expr):
   expr = "".join(expr.split())
   if not re.match(r'^[0-9xX_a-fA-F+\-*/()<>|&^~.%]+$', expr):
       return None
   try:
       allowed_chars = set("0123456789abcdefABCDEFxX+-*/() ")
       if not all(c in allowed_chars for c in expr):
           return None
       return int(eval(expr, {"__builtins__": None}, {}))
   except:
       return None

def dump_8xms_v10_6(obfuscated_code):
   try:
       hex_block_match = re.search(r'\[=\[[A-Z]{3}:([0-9A-Fa-f]+)\]=\]', obfuscated_code)
       if hex_block_match:
           hex_payload = hex_block_match.group(1)
           key_math_match = re.search(r'tonumber\([^)]+\);\s*local\s+\w+=\w+\(\w+,\s*([0-9xXa-fA-F+\-()*\/.\s]+)\);', obfuscated_code)
           if not key_math_match:
               key_math_match = re.search(r'=\w+\(\w+,\s*([0-9xXa-fA-F+\-()*\/.\s]+)\);\s*\w+=\w+\.\.string\.char', obfuscated_code)
           if not key_math_match:
               return "Error: Failed to extract Secret Key mathematical expression."
               
           math_expression = key_math_match.group(1).strip().rstrip(';')
           secret_key = safe_math_eval(math_expression)
           
           if secret_key is None:
               return "Error: Mathematical expression contained unsafe tokens."
               
           if not (0 <= secret_key <= 255):
               return f"Error: Invalid system Key detected ({secret_key})."

           decoded_bytes = bytearray()
           for i in range(0, len(hex_payload), 2):
               hex_pair = hex_payload[i:i+2]
               cipher_byte = int(hex_pair, 16)
               plain_byte = cipher_byte ^ secret_key
               decoded_bytes.append(plain_byte)
               
           return decoded_bytes.decode('utf-8', errors='ignore')
       else:
           return "Error: Target code does not contain a valid 8xms v10.6 hex block payload."
   except Exception as e:
       return f"Deobfuscation process error: {str(e)}"

def fetch_url(url):
   try:
       response = requests.get(url, timeout=30)
       if response.status_code == 200:
           return response.text
       return None
   except Exception:
       return None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
   command_prefix=".", 
   intents=intents,
   activity=discord.Activity(type=discord.ActivityType.watching, name=" 𝟴𝘅𝗺s | dump tools"),
   help_command=None
)

class DumpSelectionView(discord.ui.View):
   def __init__(self, ctx, content, status_msg=None, is_channel_mode=False):
       super().__init__(timeout=60)
       self.ctx = ctx
       self.content = content
       self.status_msg = status_msg
       self.is_channel_mode = is_channel_mode

   async def on_timeout(self):
       try:
           if self.status_msg:
               await self.status_msg.delete()
       except:
           pass

   async def process_wearedev(self, interaction):
       if self.ctx.author.id != FREE_USER_ID and get_coins(self.ctx.author.id) < COST_WEAREDEV:
           await self.status_msg.delete()
           if self.is_channel_mode:
               await self.ctx.reply(embed=discord.Embed(description=f"Insufficient funds. You need at least {COST_WEAREDEV} coins.", color=discord.Color.red()))
           else:
               await self.ctx.reply(f"Insufficient funds. You need at least {COST_WEAREDEV} coins.")
           return

       output = beautify_lua(self.content)
       if output and output.strip() and output != self.content:
           lines = output.splitlines()
           if len(lines) > 0:
               top_limit = min(60, len(lines))
               top_part = "\n".join(lines[:top_limit])
               bottom_part = "\n".join(lines[top_limit:])
               dynamic_garbage_pattern = r'^.*for\s+i\s*=\s*1\s*,\s*var_\d+\.len\(arg1\)\s*,\s*1\s+do.*?end\s*;?'
               top_part = re.sub(dynamic_garbage_pattern, '', top_part, flags=re.DOTALL | re.MULTILINE).strip()
               if top_part.startswith("local lookup"):
                   static_pattern = r'local\s+lookup\s*=\s*\{\}\s*;?.*?local\s+var_8\s*=\s*function\(.*?\).*?repeat\s*until\s+false\s*;?.*?(?=local\s+\w+\s*=\s*game|loadstring|return|\Z)'
                   top_part = re.sub(static_pattern, '', top_part, flags=re.DOTALL).strip()
               output = top_part + "\n" + bottom_part if bottom_part else top_part

           final_output = f"-- This file was created by 8xms discord.gg/8mktK8HtT --\n\n{output.strip()}"
           file_stream = io.BytesIO(final_output.encode('utf-8'))
           discord_file = discord.File(fp=file_stream, filename="message.txt")
           
           if self.is_channel_mode:
               try:
                   await self.ctx.author.send(content=f"{self.ctx.author.mention} file here", file=discord_file)
                   dm_success = True
               except:
                   dm_success = False

               if dm_success:
                   if self.ctx.author.id != FREE_USER_ID:
                       set_coins(self.ctx.author.id, get_coins(self.ctx.author.id) - COST_WEAREDEV)
                   await self.status_msg.delete()
                   await self.ctx.reply(embed=discord.Embed(description=f"{self.ctx.author.mention} has sent the file to your DM", color=discord.Color.green()))
               else:
                   await self.status_msg.delete()
                   await self.ctx.reply(embed=discord.Embed(description=f"{self.ctx.author.mention} Cannot send DM. Please open your Direct Messages!", color=discord.Color.red()))
           else:
               if self.ctx.author.id != FREE_USER_ID:
                   set_coins(self.ctx.author.id, get_coins(self.ctx.author.id) - COST_WEAREDEV)
               await self.status_msg.delete()
               await self.ctx.reply(content=f"{self.ctx.author.mention} Done.", file=discord_file)
       else:
           await self.status_msg.delete()
           if self.is_channel_mode:
               await self.ctx.reply(embed=discord.Embed(description=f"{self.ctx.author.mention} Failed to process this input.", color=discord.Color.red()))
           else:
               await self.ctx.reply(f"{self.ctx.author.mention} Failed to deobfuscate code")

   async def process_8xms(self, interaction):
       if self.ctx.author.id != FREE_USER_ID and get_coins(self.ctx.author.id) < COST_8XMS:
           await self.status_msg.delete()
           if self.is_channel_mode:
               await self.ctx.reply(embed=discord.Embed(description=f"Insufficient funds. You need at least {COST_8XMS} coins.", color=discord.Color.red()))
           else:
               await self.ctx.reply(f"Insufficient funds. You need at least {COST_8XMS} coins.")
           return

       result = dump_8xms_v10_6(self.content)
       if result.startswith("Error"):
           await self.status_msg.delete()
           if self.is_channel_mode:
               await self.ctx.reply(embed=discord.Embed(description=result, color=discord.Color.red()))
           else:
               await self.ctx.reply(result)
       else:
           final_output = f"-- This file was created by 8xms discord.gg/8mktK8HtT --\n\n{result.strip()}"
file_stream = io.BytesIO(final_output.encode('utf-8'))
           discord_file = discord.File(fp=file_stream, filename="dumped_output.lua")
           
           if self.is_channel_mode:
               try:
                   await self.ctx.author.send(content=f"{self.ctx.author.mention} file here", file=discord_file)
                   dm_success = True
               except:
                   dm_success = False

               if dm_success:
                   if self.ctx.author.id != FREE_USER_ID:
                       set_coins(self.ctx.author.id, get_coins(self.ctx.author.id) - COST_8XMS)
                   await self.status_msg.delete()
                   await self.ctx.reply(embed=discord.Embed(description=f"{self.ctx.author.mention} has sent the file to your DM", color=discord.Color.green()))
               else:
                   await self.status_msg.delete()
                   await self.ctx.reply(embed=discord.Embed(description=f"{self.ctx.author.mention} Cannot send DM. Please open your Direct Messages!", color=discord.Color.red()))
           else:
               if self.ctx.author.id != FREE_USER_ID:
                   set_coins(self.ctx.author.id, get_coins(self.ctx.author.id) - COST_8XMS)
               await self.status_msg.delete()
               await self.ctx.reply(content=f"{self.ctx.author.mention} Done.", file=discord_file)

   @discord.ui.button(label="wearedev", style=discord.ButtonStyle.success)
   async def wearedevs_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
       if interaction.user.id != self.ctx.author.id:
           await interaction.response.send_message("This is not your session.", ephemeral=True)
           return
       await interaction.response.defer()
       await self.process_wearedev(interaction)

   @discord.ui.button(label="8xms", style=discord.ButtonStyle.success)
   async def _8xms_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
       if interaction.user.id != self.ctx.author.id:
           await interaction.response.send_message("This is not your session.", ephemeral=True)
           return
       await interaction.response.defer()
       await self.process_8xms(interaction)

@bot.event
async def on_ready():
   await bot.tree.sync()
   print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
   if message.author.bot: return
   
   uid = str(message.author.id)
   today = date.today().isoformat()
   if DATA["last_claim"].get(uid) != today:
       current = get_coins(message.author.id)
       if int(message.author.id) != FREE_USER_ID:
           set_coins(message.author.id, current + 50)
       DATA["last_claim"][uid] = today
       save_data(DATA)
       try: 
           await message.author.send("You received 50 daily coins!")
       except: 
           pass

   if message.content.strip().startswith("."):
       await bot.process_commands(message)
       return

   target_channel_id = DATA.get("settings", {}).get("dump_channel_id")
   
   if target_channel_id and message.channel.id == int(target_channel_id):
       content = None
       is_valid_input = False

       if message.attachments:
           attachment = message.attachments[0]
           if attachment.filename.endswith(('.lua', '.txt')):
               try:
                   content_bytes = await attachment.read()
                   content = content_bytes.decode("utf-8", errors="ignore")
                   is_valid_input = True
               except: 
                   pass
       else:
           stripped_args = message.content.strip()
           if stripped_args.startswith(("http://", "https://")):
               url = stripped_args.strip("`")
               if url.startswith(("https://pastefy.app/", "https://xhider.xyz/raw/", "https://raw.githubusercontent.com/")):
                   content = fetch_url(url)
                   is_valid_input = True

       if content and content.strip() and is_valid_input:
           choice_embed = discord.Embed(title="Choice", description="Choose the dump lua method", color=discord.Color.green())
           ctx = await bot.get_context(message)
           status_msg = await message.reply(embed=choice_embed)
           view = DumpSelectionView(ctx, content, status_msg, is_channel_mode=True)
           await status_msg.edit(view=view)

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
       await ctx.message.reply("coin: Unlimited")
   else: 
       await ctx.message.reply("coin: " + str(get_coins(ctx.author.id)))

@bot.command(name="topcoin")
async def top_coin(ctx):
   sorted_coins = sorted(DATA["coins"].items(), key=lambda x: x[1], reverse=True)[:10]
   desc = "\n".join([f"{i+1}. <@{uid}>: {amt} coins" for i, (uid, amt) in enumerate(sorted_coins)])
   embed = discord.Embed(title="list of user coins", description=desc, color=0xffd700)
   await ctx.send(embed=embed)

@bot.command(name="dump")
async def deobfuscate_cmd(ctx, *, args: str = None):
   content = None

   if ctx.message.attachments:
       attachment = ctx.message.attachments[0]
       if not attachment.filename.endswith(('.lua', '.txt')):
           await ctx.message.reply("Please send the txt / lua file")
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
           if url.startswith(("https://pastefy.app/","https://xhider.xyz/raw/","https://raw.githubusercontent.com/")):
               content = fetch_url(url)
               if not content or not content.strip():
                   await ctx.message.reply("Failed to fetch link content")
                   return
           else:
               await ctx.message.reply("Failed: Link not supported")
               return
       else:
           content = re.sub(r'^```[a-zA-Z]*\n|```$', '', stripped_args, flags=re.MULTILINE)

   if not content or not content.strip():
       await ctx.message.reply("Please add the file / link raw")
       return

   choice_embed = discord.Embed(title="Choice", description="Choose the dump lua method", color=discord.Color.green())
   status_msg = await ctx.message.reply(embed=choice_embed)
   view = DumpSelectionView(ctx, content, status_msg, is_channel_mode=False)
   await status_msg.edit(view=view)

@bot.command(name="detect")
async def detect_obfuscator(ctx, *, args: str = None):
   content = None

   if ctx.message.attachments:
       attachment = ctx.message.attachments[0]
       if not attachment.filename.endswith(('.lua', '.txt')):
           await ctx.message.reply("Please send  .lua / .txt file.")
           return
       try:
           content_bytes = await attachment.read()
           content = content_bytes.decode("utf-8", errors="ignore")
       except Exception as e:
           await ctx.message.reply(f"Failed to read file: {e}")
           return

   elif args:
       stripped_args = args.strip()
       if stripped_args.startswith(("http://", "https://")):
           url = stripped_args.strip("`")
           if url.startswith(("https://pastefy.app/", "https://raw.githubusercontent.com/","https://xhider.xyz/raw/")):
               content = fetch_url(url)
               if not content or not content.strip():
                   await ctx.message.reply("Failed to fetch content from url")
                   return
           else:
               content = fetch_url(url)
               if not content:
                   content = stripped_args
       else:
           content = re.sub(r'^```[a-zA-Z]*\n|```$', '', stripped_args, flags=re.MULTILINE)

   if not content or not content.strip():
       await ctx.message.reply("Please provide a file, txt / raw link.")
       return

   result = "undetermined"

   if re.search(r"return\s*\(\s*function\s*\([^\)]*\)\s*local\s+[a-zA-Z0-9_,\s]+do\s+local\s+[a-zA-Z0-9_,\s]+=\s*(?:math|string)", content):
       result = "8xms thinks this is luraph"
       
   elif re.search(r"return\s*\(\s*function\s*\([^\)]*\)\s*local\s+[a-zA-Z0-9_]\s*=\s*\{\s*['\"]\\[0-9]+", content):
       result = "8xms thinks this is wearedev"

   elif re.search(r":gsub\s*\(\s*['\"].\+['\"]\s*,\s*\(\s*function", content):
       result = "8xms thinks this is moonsecv3"
       
   elif re.search(r"local\s+[a-zA-Z0-9_,\s]+=\s*(?:bit32\.bxor|getmetatable|pairs|type)", content):
       result = "8xms thinks this is moonveil"

   elif re.search(r"local\s+v0\s*[,=]", content):
       result = "8xms thinks this is luaobfuscator"
       
   elif "This file was created by XHider" in content or " thinks this is xhider" in content:
       result = "8xms thinks this is xhider"
       
   elif re.search(r"return\s*\(\s*function\s*\([^\)]*\)\s*local\s+[a-zA-Z0-9_,\s]+do\s+local\s+[a-zA-Z0-9_,\s]+=\s*math\.floor.*-\s*[0-9]+\s*-\s*\(\s*-\s*[0-9]+", content):
       result = "8xms thinks this is 8xms"

   msg_embed = discord.Embed(
       title="analysis",
       description=f"Result: **{result}**",
       color=discord.Color.red()
   )
   
   await ctx.message.reply(embed=msg_embed)

@bot.command(name="help")
async def help_cmd(ctx):
   help_text = (
       "`.help`\n"
       "`.coin`  check your coin\n"
       "`.topcoin`  list of user coins\n"
       "`.buycoin`  get task link to earn coins\n"
       "`.detect`  detect obfuscators type\n"
       "`.dump`  deobfuscator script (Cost: 10 or 3000 coins)"
   )
   
   msg_embed = discord.Embed(
       title="Command",
       description=help_text,
       color=discord.Color.red()
   )
   await ctx.message.reply(embed=msg_embed)

@bot.command(name="set")
async def set_channel_cmd(ctx, channel: discord.TextChannel = None):
   if ctx.author.id != FREE_USER_ID:
       await ctx.message.reply("You do not have permission!")
       return
       
   if not channel:
       await ctx.message.reply("Please mention a channel. Example: `.set #channel`")
       return

   try:
       await ctx.message.delete()
   except:
       pass

   if "settings" not in DATA:
       DATA["settings"] = {}
       
   DATA["settings"]["dump_channel_id"] = channel.id
   save_data(DATA)
   
   await ctx.send("already set")

if __name__ == "__main__":
   keep_alive()
   bot.run(TOKEN)