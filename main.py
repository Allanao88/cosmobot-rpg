import discord
from discord.ext import commands
import json
import random
import asyncio
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

# --- Configuração do bot ---
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- Banco de dados simples (JSON) ---
os.makedirs('data', exist_ok=True)
DATA_FILE = os.path.join('data', 'cosmo_data.json')

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'players': {}, 'npcs': {}, 'xp_log': {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Dados e mitigação por patente ---
PATENT_DICE = {
    'Aspirante': 4,
    'Bronze': 6,
    'Prata': 8,
    'Ouro': 10,
    'Semideus': 12,
    'Divindade': 20
}

MITIGATION = {
    'Bronze': 2,
    'Prata': 4,
    'Ouro': 6,
    'Semideus': 8,
    'Divindade': 10
}

# --- Eventos do bot ---
@bot.event
async def on_ready():
    print(f'CosmoBot conectado como {bot.user} - Pronto para a Guerra Santa!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"📩 Mensagem recebida: {message.content} - Autor: {message.author}")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    print(f"❌ Erro no comando: {error}")
    try:
        await ctx.send(f"⚠️ Erro: {error}")
    except Exception:
        pass

# --- COMANDOS DE NPC ---
@bot.command()
async def create_npc(ctx, npc_id: int, name, patent, forca: int, agi: int, cos: int, von: int, pv: int):
    data = load_data()
    if str(npc_id) in data['npcs']:
        await ctx.send("❌ NPC com esse ID já existe!")
        return
    npc = {
        'name': name,
        'patent': patent,
        'for': forca,
        'agi': agi,
        'cos': cos,
        'von': von,
        'pv': pv
    }
    data['npcs'][str(npc_id)] = npc
    save_data(data)
    await ctx.send(f"🛡️ NPC criado: {name} | ID: {npc_id}")

@bot.command()
async def view_npc(ctx, npc_id: int):
    data = load_data()
    npc = data['npcs'].get(str(npc_id))
    if not npc:
        await ctx.send("❌ NPC não encontrado!")
        return
    embed = discord.Embed(title=f"📋 NPC: {npc['name']} | ID: {npc_id}", color=0xFFD700)
    embed.add_field(name="Patente", value=npc['patent'], inline=True)
    embed.add_field(name="Atributos", value=f"FOR {npc['for']} | AGI {npc['agi']} | COS {npc['cos']} | VON {npc['von']}", inline=True)
    embed.add_field(name="PV", value=npc['pv'], inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def delete_npc(ctx, npc_id: int):
    data = load_data()
    if str(npc_id) in data['npcs']:
        name = data['npcs'][str(npc_id)]['name']
        del data['npcs'][str(npc_id)]
        save_data(data)
        await ctx.send(f"🗑️ NPC '{name}' deletado com sucesso!")
    else:
        await ctx.send("❌ NPC não encontrado!")

# --- COMANDOS DE JOGADOR ---
@bot.command()
async def create_character(ctx, name, sign, patent, forca: int, agi: int, cos: int, von: int):
    if patent not in PATENT_DICE:
        await ctx.send("❌ Patente inválida! Opções: Aspirante, Bronze, Prata, Ouro, Semideus, Divindade.")
        return
    total_attrs = forca + agi + cos + von
    if patent == 'Aspirante' and total_attrs > 10:
        await ctx.send("❌ Aspirantes: máx. 10 pontos totais em atributos!")
        return
    data = load_data()
    pv = round((forca + cos) * 1.8)
    character = {
        'name': name,
        'sign': sign,
        'patent': patent,
        'for': forca,
        'agi': agi,
        'cos': cos,
        'von': von,
        'pv': pv,
        'xp': 0,
        'talents': [],
        'special_moves': []
    }
    data['players'][str(ctx.author.id)] = character
    save_data(data)
    embed = discord.Embed(title=f"🛡️ Ficha Criada: {name} de {sign}", color=0xFFD700)
    embed.add_field(name="Patente", value=patent, inline=True)
    embed.add_field(name="Atributos", value=f"FOR {forca} | AGI {agi} | COS {cos} | VON {von}", inline=True)
    embed.add_field(name="PV Inicial", value=pv, inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def sheet(ctx):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Crie uma ficha com !create_character primeiro!")
        return
    char = data['players'][player_id]
    embed = discord.Embed(title=f"📋 Ficha: {char['name']} de {char['sign']}", color=0xFFD700)
    embed.add_field(name="Patente", value=char['patent'], inline=True)
    embed.add_field(name="Atributos", value=f"FOR {char['for']} | AGI {char['agi']} | COS {char['cos']} | VON {char['von']}", inline=True)
    embed.add_field(name="PV / XP", value=f"{char['pv']} / {char['xp']}", inline=True)
    embed.add_field(name="Talentos", value=', '.join(char['talents']) or 'Nenhum', inline=False)
    embed.add_field(name="Golpes", value=', '.join(char['special_moves']) or 'Nenhum', inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def add_move(ctx, *, move_name):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Crie uma ficha primeiro com !create_character")
        return
    data['players'][player_id]['special_moves'].append(move_name)
    save_data(data)
    await ctx.send(f"✅ Golpe especial '{move_name}' adicionado!")

@bot.command()
async def add_talent(ctx, *, talent_name):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Crie uma ficha primeiro com !create_character")
        return
    data['players'][player_id]['talents'].append(talent_name)
    save_data(data)
    await ctx.send(f"✅ Talento '{talent_name}' adicionado!")

@bot.command()
async def remove_move(ctx, *, move_name):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    if move_name in data['players'][player_id]['special_moves']:
        data['players'][player_id]['special_moves'].remove(move_name)
        save_data(data)
        await ctx.send(f"✅ Golpe '{move_name}' removido!")
    else:
        await ctx.send("❌ Golpe não encontrado!")

@bot.command()
async def update_hp(ctx, new_hp: int):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    data['players'][player_id]['pv'] = new_hp
    save_data(data)
    await ctx.send(f"✅ PV atualizado para {new_hp}!")

# --- COMANDOS DE AÇÃO ---
@bot.command()
async def roll(ctx, attribute, *, description="Ação genérica"):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    allowed_attrs = {'for', 'agi', 'cos', 'von'}
    attr_key = attribute.lower()
    if attr_key not in allowed_attrs:
        await ctx.send("❌ Atributo inválido! Use FOR, AGI, COS ou VON.")
        return
    attr_value = char.get(attr_key, 0)
    die = PATENT_DICE.get(char['patent'], 6)
    roll_value = random.randint(1, die)
    result = roll_value + attr_value
    critical = roll_value == die
    fumble = roll_value == 1
    message = f"🎲 **{char['name']} rola {attr_key.upper()} ({description})**\n1d{die} ({roll_value}) + {attr_key.upper()} ({attr_value}) = **{result}**"
    if critical:
        message += "\n💥 **Crítico!** +2 dano ou bônus narrativo."
    elif fumble:
        message += "\n😓 **Falha Crítica!** Complicação (ex.: Cosmo instável)."
    await ctx.send(message)

@bot.command()
async def initiative(ctx):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    die = PATENT_DICE.get(char['patent'], 6)
    roll_value = random.randint(1, die)
    result = roll_value + char['von']
    await ctx.send(f"⚡ **Iniciativa de {char['name']}**: 1d{die} ({roll_value}) + VON ({char['von']}) = **{result}**")

@bot.command()
async def attack_physical(ctx, target_id: int):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    die = PATENT_DICE.get(char['patent'], 6)
    hit_roll = random.randint(1, die) + char['agi']
    damage_roll = random.randint(1, 4) + char['for']
    target = data['npcs'].get(str(target_id), {'agi': 5, 'pv': 20, 'patent': 'Bronze'})
    target_agi = target.get('agi', 5)
    mitigation = MITIGATION.get(target.get('patent', 'Bronze'), 0)
    if hit_roll >= target_agi:
        final_damage = max(0, damage_roll - mitigation)
        target['pv'] = max(0, target.get('pv', 20) - final_damage)
        data['npcs'][str(target_id)] = target
        save_data(data)
        await ctx.send(f"👊 **{char['name']} acerta!** Dano: {damage_roll} - Mitig. ({mitigation}) = **{final_damage}** | PV alvo: {target['pv']}")
    else:
        await ctx.send(f"👊 **{char['name']} erra!** Rolagem: {hit_roll} vs AGI {target_agi}")

@bot.command()
async def special_move(ctx, *, move_info):
    parts = move_info.split()
    if len(parts) < 2:
        await ctx.send("❌ Use: !special_move [nome] [target_id]")
        return
    move_name = ' '.join(parts[:-1])
    try:
        target_id = int(parts[-1])
    except ValueError:
        await ctx.send("❌ Target_id deve ser um número!")
        return
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    if char['patent'] == 'Aspirante':
        await ctx.send("❌ Aspirantes não usam golpes especiais!")
        return
    die = PATENT_DICE.get(char['patent'], 6)
    will_test = random.randint(1, die) + char['von']
    target = data['npcs'].get(str(target_id), {'patent': 'Bronze', 'pv': 20})
    target_patent = target.get('patent', 'Bronze')
    patent_order = list(PATENT_DICE.keys())
    dc = 10 + patent_order.index(target_patent) * 2 if target_patent in patent_order else 10
    if will_test >= dc:
        dice_count_map = {'Bronze': 2, 'Prata': 3, 'Ouro': 3, 'Semideus': 4, 'Divindade': 5}
        dice_count = dice_count_map.get(char['patent'], 2)
        damage = sum(random.randint(1, 4) for _ in range(dice_count)) + char['cos'] + (char['cos'] // 3)
        mitigation = MITIGATION.get(target_patent, 0)
        final_damage = max(0, damage - mitigation)
        target['pv'] = max(0, target.get('pv', 20) - final_damage)
        data['npcs'][str(target_id)] = target
        save_data(data)
        await ctx.send(f"🌌 **{char['name']} usa {move_name}!** Sucesso! Dano: **{final_damage}** | PV alvo: {target['pv']}")
    else:
        bonus_damage = char['cos'] // 2
        await ctx.send(f"🌌 **{char['name']} falha em {move_name}!** Rolagem: {will_test} vs DC {dc} | Dano fraco: {bonus_damage}")

@bot.command()
async def add_xp(ctx, *args):
    data = load_data()
    total_xp = 0
    for xp_str in args:
        try:
            total_xp += int(xp_str)
        except ValueError:
            await ctx.send(f"❌ Valor inválido: {xp_str}")
            return
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    data['players'][player_id]['xp'] += total_xp
    if data['players'][player_id]['xp'] > 150:
        data['players'][player_id]['xp'] = 150
        await ctx.send("⚠️ XP limitado a 150 por sessão!")
    save_data(data)
    await ctx.send(f"✅ +{total_xp} XP para {data['players'][player_id]['name']}! Total: {data['players'][player_id]['xp']}")

@bot.command()
async def calc_master_xp(ctx):
    data = load_data()
    players_xp = [char['xp'] for char in data['players'].values() if char.get('xp', 0) > 0]
    if not players_xp:
        await ctx.send("❌ Nenhum XP de jogadores!")
        return
    avg_xp = sum(players_xp) / len(players_xp)
    master_xp = round(avg_xp / 2)
    gold_xp = round(avg_xp / 3)
    embed = discord.Embed(title="📊 Cálculo Semanal de XP", color=0xFFD700)
    embed.add_field(name="Média Jogadores", value=f"{avg_xp:.1f}", inline=True)
    embed.add_field(name="Mestre", value=master_xp, inline=True)
    embed.add_field(name="Cavaleiro de Ouro", value=gold_xp, inline=True)
    await ctx.send(embed=embed)

# --- COMANDO DE AJUDA ---
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📜 CosmoBot - Lista de Comandos",
        description="Comandos para o RPG de Cavaleiros do Zodíaco. Use `!` antes de cada um.",
        color=0xFFD700
    )
    # Comandos jogador
    embed.add_field(name="!create_character [nome] [signo] [patente] [for] [agi] [cos] [von]", value="Cria uma ficha", inline=False)
    embed.add_field(name="!sheet", value="Exibe sua ficha", inline=False)
    embed.add_field(name="!add_move [nome_do_golpe]", value="Adiciona golpe especial", inline=False)
    embed.add_field(name="!add_talent [nome_do_talento]", value="Adiciona talento", inline=False)
    embed.add_field(name="!remove_move [nome_do_golpe]", value="Remove golpe especial", inline=False)
    embed.add_field(name="!update_hp [novo_pv]", value="Atualiza PV", inline=False)
    embed.add_field(name="!roll [atributo] [descrição]", value="Rola dado", inline=False)
    embed.add_field(name="!initiative", value="Calcula iniciativa", inline=False)
    embed.add_field(name="!attack_physical [target_id]", value="Ataque físico", inline=False)
    embed.add_field(name="!special_move [nome] [target_id]", value="Golpe especial", inline=False)
    embed.add_field(name="!add_xp [valores]", value="Adiciona XP", inline=False)
    embed.add_field(name="!calc_master_xp", value="XP para Mestre/Ouro", inline=False)

    # Comandos NPC
    embed.add_field(name="!create_npc [id] [nome] [patente] [for] [agi] [cos] [von] [pv]", value="Cria NPC", inline=False)
    embed.add_field(name="!view_npc [id]", value="Exibe NPC", inline=False)
    embed.add_field(name="!delete_npc [id]", value="Deleta NPC", inline=False)

    embed.set_footer(text="CosmoBot - Protegendo Athena!")
    try:
        await ctx.author.send(embed=embed)
        await ctx.send(f"📩 {ctx.author.mention}, comandos enviados por DM!")
    except discord.Forbidden:
        await ctx.send("⚠️ Ative DMs de servidores para ver os comandos!")

# --- MANTER BOT ATIVO NO REPLIT ---
keep_alive()

# --- INICIAR BOT ---
token = os.getenv("BOT_TOKEN")
print("Token carregado:", token)
bot.run(token)

