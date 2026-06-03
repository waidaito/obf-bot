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
COST = 10
COST_8XMS = 3000
DATA_FILE = "data.json"

def load_data():
   if os.path.exists(DATA_FILE):
       with open(DATA_FILE, "r") as f:
           try: return json.load(f)
           except: return {"coins": {}, "last_claim": {}}
   return {"coins": {}, "last_claim": {}}

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

def random_var(length=6):
   first = random.choice(string.ascii_letters)
   rest = ''.join(random.choices(string.ascii_letters + string.digits, k=length-1))
   return first + rest

def obfuscate_to_mixed_math(target):
   current_val = target
   ops_pool = []
   
   for _ in range(random.randint(2, 4)):
       op = random.choice(['+', '-'])
       rand_num = random.randint(100000, 1500000)
       
       if op == '+':
           current_val = current_val - rand_num
           display_style = random.choice(['normal', 'negative', 'hex'])
           if display_style == 'normal':
               ops_pool.append(f"+{rand_num}")
           elif display_style == 'negative':
               ops_pool.append(f"-(-{rand_num})")
           else:
               ops_pool.append(f"+{hex(rand_num)}")
       elif op == '-':
           current_val = current_val + rand_num
           display_style = random.choice(['normal', 'negative', 'hex'])
           if display_style == 'normal':
               ops_pool.append(f"-{rand_num}")
           elif display_style == 'negative':
               ops_pool.append(f"+(-{rand_num})")
           else:
               ops_pool.append(f"-{hex(rand_num)}")
           
   start_style = random.choice(['normal', 'hex'])
   expr = hex(current_val) if start_style == 'hex' else str(current_val)
   
   for action in reversed(ops_pool):
       expr = f"({expr}{action})"
   return expr

def ironbrew_total_wrapped_v10_6(source_code):
   secret_key = random.randint(100, 250)
   
   encrypted_hex_list = []
   for byte in source_code.encode('utf-8'):
       cipher_byte = byte ^ secret_key
       encrypted_hex_list.append(f"{cipher_byte:02X}")
       
   hex_payload = "".join(encrypted_hex_list)
   fake_signature = "".join(random.choices(string.ascii_uppercase, k=3))
   bytecode_string_block = f"[=[{fake_signature}:{hex_payload}]=]"
   
   # Mã hóa ngầm loadstring và load thành Hex XOR
   hex_loadstring = "".join([f"{ord(c) ^ secret_key:02X}" for c in "loadstring"])
   hex_load = "".join([f"{ord(c) ^ secret_key:02X}" for c in "load"])
   
   # LẤY ĐỘ DÀI TRƯỚC ĐỂ FIX LỖI LỒNG F-STRING PHÍA DƯỚI
   len_ls = len(hex_loadstring)
   len_l = len(hex_load)
   
   v_bit_func, v_w, v_m, v_x, v_i, v_j, v_res = [random_var() for _ in range(7)]
   v_bytecode, v_buffer, v_func, v_run = [random_var() for _ in range(4)]
   v_idx, v_pair, v_num, v_dec = [random_var() for _ in range(4)]
   v_loop_idx, v_env = random_var(), random_var()
   
   v_str1, v_str2, v_t_idx, v_t_pair = [random_var() for _ in range(4)]
   v_h_ls, v_h_l = random_var(), random_var()

   junk_pieces = []
   for _ in range(2000):
       v_junk = random_var()
       rand_target = random.randint(50, 99999)
       junk_pieces.append(f"local {v_junk}={obfuscate_to_mixed_math(rand_target)}")
       
   half = len(junk_pieces) // 2
   junk_top = ";".join(junk_pieces[:half])
   junk_bottom = ";".join(junk_pieces[half:])

   bit_and_interpreter_core = (
       f"local function {v_bit_func}({v_i},{v_j}) "
       f"local {v_x}=0; "
       f"for {v_m}=0,7 do "
       f"local {v_w}=({v_i}/{obfuscate_to_mixed_math(2)}^{v_m})%2; "
       f"local {v_res}=({v_j}/{obfuscate_to_mixed_math(2)}^{v_m})%2; "
       f"if {v_w}-{v_w}%1~={v_res}-{v_res}%1 then "
       f"{v_x}={v_x}+{obfuscate_to_mixed_math(2)}^{v_m} "
       f"end "
       f"end "
       f"return {v_x} "
       f"end; "
       f"local {v_bytecode}={bytecode_string_block}; "
       f"local {v_h_ls}=\"{hex_loadstring}\"; "
       f"local {v_h_l}=\"{hex_load}\"; "
       f"local {v_buffer}=\"\"; "
       f"for {v_loop_idx}={obfuscate_to_mixed_math(1)},{obfuscate_to_mixed_math(2)} do "
       f"if {v_loop_idx}=={obfuscate_to_mixed_math(1)} then "
       f"local h_clean=string.sub({v_bytecode},5); "
       f"for {v_idx}=1,#h_clean,2 do "
       f"local {v_pair}=string.sub(h_clean,{v_idx},{v_idx}+1); "
       f"local {v_num}=tonumber({v_pair},16); "
       f"local {v_dec}={v_bit_func}({v_num},{obfuscate_to_mixed_math(secret_key)}); "
       f"{v_buffer}={v_buffer}..string.char({v_dec}) "
       f"end "
       f"elseif {v_loop_idx}=={obfuscate_to_mixed_math(2)} then "
       f"local {v_str1}, {v_str2} = \"\", \"\"; "
       f"for {v_t_idx}=1,{obfuscate_to_mixed_math(len_ls)},2 do "
       f"local {v_t_pair}=string.sub({v_h_ls},{v_t_idx},{v_t_idx}+1); "
       f"if #{v_t_pair}==2 then "
       f"{v_str1}={v_str1}..string.char({v_bit_func}(tonumber({v_t_pair},16),{obfuscate_to_mixed_math(secret_key)})) "
       f"end "
       f"end; "
       f"for {v_t_idx}=1,{obfuscate_to_mixed_math(len_l)},2 do "
       f"local {v_t_pair}=string.sub({v_h_l},{v_t_idx},{v_t_idx}+1); "
       f"if #{v_t_pair}==2 then "
       f"{v_str2}={v_str2}..string.char({v_bit_func}(tonumber({v_t_pair},16),{obfuscate_to_mixed_math(secret_key)})) "
       f"end "
       f"end; "
       f"local {v_env}=getfenv(); "
       f"local {v_func}={v_env}[{v_str1}] or {v_env}[{v_str2}]; "
       f"local {v_run}={v_func}({v_buffer}); "
       f"if {v_run} then {v_run}(...) end "
       f"end "
       f"end"
   )

   total_payload = f"{junk_top};{bit_and_interpreter_core};{junk_bottom}"
   
   clean_payload = " ".join(total_payload.splitlines()).strip()
   clean_payload = re.sub(r'\s*;\s*', ';', clean_payload)
   clean_payload = re.sub(r'\s*=\s*', '=', clean_payload)
   
   return f"-- This file was created by 8xms v2.0 discord.gg/a8rJjxFaE  --\nreturn(function(...) {clean_payload} end)(...)"

def compress_loadstring_patterns(lua_code):
   if not lua_code: return ""
   url_pattern = r'(\w+)\s*=\s*\{\s*game:[hH]ttp[gG]et\(\s*["\'](https?://[^\s"\']+)["\']\s*\)\s*\r*\}\s*;?'
   urls_found = re.findall(url_pattern, lua_code)
   
   for var_name, url in urls_found:
       loadstring_pattern = r'(\w+)\s*=\s*loadstring\(\s*\w+\(\s*' + var_name + r'\s*\)\s*\)\s*;?'
       if re.search(loadstring_pattern, lua_code):
           replacement_code = f'local Loader = loadstring(game:HttpGet("{url}"))'
           lua_code = re.sub(loadstring_pattern, replacement_code, lua_code)
           lua_code = re.sub(r'\b' + var_name + r'\s*=\s*\{\s*game:[hH]ttp[gG]et\(\s*["\']' + re.escape(url) + r'["\']\s*\)\s*\s*;?', '', lua_code)

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

def fetch_url(url):
   try:
       response = requests.get(url, timeout=30)
       if response.status_code == 200:
           return response.text
       return None
   except Exception:
       return None

class DumpSelectionView(discord.ui.View):
   def __init__(self, author, content, status_msg=None, ctx=None):
       super().__init__(timeout=60)
       self.author = author
       self.content = content
       self.status_msg = status_msg
       self.ctx = ctx

   async def interaction_check(self, interaction: discord.Interaction) -> bool:
       if interaction.user.id != self.author.id:
           await interaction.response.send_message("Đây không phải bảng điều khiển của bạn!", ephemeral=True)
           return False
       return True

   async def execute_dump(self, interaction: discord.Interaction, cost_amount, dump_type):
       if self.author.id != FREE_USER_ID and get_coins(self.author.id) < cost_amount:
           embed = discord.Embed(description=f"Insufficient funds. You need at least {cost_amount} coins.", color=discord.Color.red())
           if self.status_msg:
               await self.status_msg.edit(embed=embed, view=None)
           else:
               await interaction.response.send_message(embed=embed, ephemeral=True)
           return

       await interaction.response.defer()

       if dump_type == "wearedev":
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

                   if bottom_part:
                       output = top_part + "\n" + bottom_part
                   else:
                       output = top_part

               final_output = f"-- This file was created by 8xms discord.gg/8mktK8HtT --\n\n{output.strip()}"
               file_stream = io.BytesIO(final_output.encode('utf-8'))
               discord_file = discord.File(fp=file_stream, filename="message.txt")
              
               try:
                   await self.author.send(content=f"{self.author.mention} file here", file=discord_file)
                   dm_success = True
               except:
                   dm_success = False

               if dm_success:
                   if self.author.id != FREE_USER_ID:
                       set_coins(self.author.id, get_coins(self.author.id) - cost_amount)

                   success_embed = discord.Embed(description=f"{self.author.mention} has sent the file to your DM", color=discord.Color.green())
                   if self.status_msg:
                       await self.status_msg.edit(embed=success_embed, view=None)
                   elif self.ctx:
                       await self.ctx.send(embed=success_embed)
               else:
                   error_embed = discord.Embed(description=f"{self.author.mention} Cannot send DM. Please open your Direct Messages!", color=discord.Color.red())
                   if self.status_msg:
                       await self.status_msg.edit(embed=error_embed, view=None)
                   elif self.ctx:
                       await self.ctx.send(embed=error_embed)
           else:
               fail_embed = discord.Embed(description=f"{self.author.mention} Failed to process this input.", color=discord.Color.red())
               if self.status_msg:
                   await self.status_msg.edit(embed=fail_embed, view=None)
               elif self.ctx:
                   await self.ctx.send(embed=fail_embed)
       else:
           fail_embed = discord.Embed(description=f"{self.author.mention} done", color=discord.Color.orange())
           if self.status_msg:
               await self.status_msg.edit(embed=fail_embed, view=None)
           elif self.ctx:
               await self.ctx.send(embed=fail_embed)

   @discord.ui.button(label="wearedev", style=discord.ButtonStyle.primary)
   async def wearedev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.execute_dump(interaction, COST, "wearedev")

   @discord.ui.button(label="8xms", style=discord.ButtonStyle.danger)
   async def eightxms_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
       await self.execute_dump(interaction, COST_8XMS, "8xms")


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
   command_prefix=".", 
   intents=intents,
   activity=discord.Activity(type=discord.ActivityType.watching, name=" 𝟴𝘅𝗺s | obf and dump tools"),
   help_command=None
)

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
           embed_select = discord.Embed(title="select", description="Choose a dump method below. :", color=0x000000)
           status_msg = await message.reply(embed=embed_select)
           view = DumpSelectionView(author=message.author, content=content, status_msg=status_msg)
           await status_msg.edit(view=view)

   await bot.process_commands(message)

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

   embed_select = discord.Embed(title="select", description="Choose the dump type below:", color=0x000000)
   status_msg = await ctx.message.reply(embed=embed_select)
   view = DumpSelectionView(author=ctx.author, content=content, status_msg=status_msg, ctx=ctx)
   await status_msg.edit(view=view)

@bot.command(name="obf")
async def obfuscate_lua(ctx, *, text_code: str = None):
   if ctx.author.id != FREE_USER_ID:
       if get_coins(ctx.author.id) < COST:
           await ctx.message.reply("Insufficient funds. You need at least 10 coins.")
           return

   lua_content = ""

   if ctx.message.attachments:
       attachment = ctx.message.attachments[0]
       if attachment.filename.endswith(('.lua', '.txt')):
           try:
               lua_content = (await attachment.read()).decode("utf-8", errors="ignore")
           except Exception as e:
               await ctx.send(f"Error reading file: {e}")
               return
       else:
           await ctx.send("please add .lua / .txt file")
           return

   elif text_code:
       lua_content = text_code.strip().strip("`").replace("lua\n", "", 1)

   else:
       await ctx.send("Please add txt / lua file.")
       return

   progress_msg = await ctx.send("<a:loading:1477881141678702603> Processing ")

   try:
       fixed_code = ironbrew_total_wrapped_v10_6(lua_content)

       if ctx.author.id != FREE_USER_ID:
           set_coins(ctx.author.id, get_coins(ctx.author.id) - COST)

       file_data = io.BytesIO(fixed_code.encode("utf-8"))
       discord_file = discord.File(fp=file_data, filename="message.txt")

       await progress_msg.delete()
       await ctx.message.reply(
           content=f" {ctx.author.mention} Done",
           file=discord_file
       )
   except Exception as e:
       try:
           await progress_msg.delete()
       except:
           pass
       await ctx.message.reply(f"erro: {e}")

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
       "`.dump`  deobfuscator(wearedev) script (Cost: 10 coins)\n"
       "`.obf`  obfuscate script using 8xms v2.0 Deployed (Cost: 10 coins)"
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
   bot.run(TOK