import discord
from discord.ext import commands
import json
import random
import asyncio
import os
from dotenv import load_dotenv
from keep_alive import keep_alive  # <-- Adicione esta linha

load_dotenv()


# Configuração do bot
intents = discord.Intents.default()
intents.messages = True
# intents.message_content = True  # Comentado para versões antigas
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Banco de dados simples (JSON) - Persiste fichas e XP
DATA_FILE = 'cosmo_data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'players': {}, 'npcs': {}, 'xp_log': {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Dados por patente (do Manual do Sistema)
PATENT_DICE = {
    'Aspirante': 4,
    'Bronze': 6,
    'Prata': 8,
    'Ouro': 10,
    'Semideus': 12,
    'Divindade': 20
}

# Mitigação por patente
MITIGATION = {
    'Bronze': 2,
    'Prata': 4,
    'Ouro': 6,
    'Semideus': 8,
    'Divindade': 10
}

@bot.event
async def on_ready():
    print(f'CosmoBot conectado como {bot.user} - Pronto para a Guerra Santa!')

# Comando: Ajuda (enviado por DM)
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📜 CosmoBot - Lista de Comandos",
        description="Comandos para o RPG de Cavaleiros do Zodíaco. Use `!` antes de cada um.",
        color=0xFFD700
    )
    embed.add_field(
        name="!create_character [nome] [signo] [patente] [for] [agi] [cos] [von]",
        value="Cria uma ficha. Ex: `!create_character Seiya Pégaso Aspirante 3 3 2 2`",
        inline=False
    )
    embed.add_field(
        name="!sheet",
        value="Exibe sua ficha. Ex: `!sheet`",
        inline=False
    )
    embed.add_field(
        name="!roll [atributo] [descrição]",
        value="Rola dado. Ex: `!roll COS Explosão estelar`",
        inline=False
    )
    embed.add_field(
        name="!initiative",
        value="Calcula iniciativa. Ex: `!initiative`",
        inline=False
    )
    embed.add_field(
        name="!attack_physical [target_id]",
        value="Ataque físico. Ex: `!attack_physical 123`",
        inline=False
    )
    embed.add_field(
        name="!special_move [nome] [target_id]",
        value="Golpe especial. Ex: `!special_move Meteoro 123`",
        inline=False
    )
    embed.add_field(
        name="!add_xp [valores]",
        value="Adiciona XP. Ex: `!add_xp 40 10`",
        inline=False
    )
    embed.add_field(
        name="!calc_master_xp",
        value="XP para Mestre/Ouro. Ex: `!calc_master_xp`",
        inline=False
    )
    embed.set_footer(text="CosmoBot - Protegendo Athena!")
    try:
        await ctx.author.send(embed=embed)
        await ctx.send(f"📩 {ctx.author.mention}, comandos enviados por DM!")
    except discord.Forbidden:
        await ctx.send("⚠️ Ative DMs de servidores para ver os comandos!")

# Comando: Criar ficha (com validação robusta do Manual)
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
    pv = round((forca + cos) * 1.8)  # Fórmula do Manual
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

# Comando: Ficha (com formatação melhorada)
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

# Comando: Roll (com críticos/falhas do sistema)
@bot.command()
async def roll(ctx, attribute, *, description="Ação genérica"):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    patent = char['patent']
    attr_value = getattr(char, attribute.lower(), 0)
    if attr_value == 0:
        await ctx.send("❌ Atributo inválido! Use FOR, AGI, COS ou VON.")
        return
    die = PATENT_DICE[patent]
    roll_value = random.randint(1, die)
    result = roll_value + attr_value
    critical = roll_value == die
    fumble = roll_value == 1
    message = f"🎲 **{char['name']} rola {attribute.upper()} ({description})**\n1d{die} ({roll_value}) + {attribute.upper()} ({attr_value}) = **{result}**"
    if critical:
        message += "\n💥 **Crítico!** +2 dano ou bônus narrativo."
    elif fumble:
        message += "\n😓 **Falha Crítica!** Complicação (ex.: Cosmo instável)."
    await ctx.send(message)

# Comando: Iniciativa
@bot.command()
async def initiative(ctx):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    die = PATENT_DICE[char['patent']]
    roll_value = random.randint(1, die)
    result = roll_value + char['von']
    await ctx.send(f"⚡ **Iniciativa de {char['name']}**: 1d{die} ({roll_value}) + VON ({char['von']}) = **{result}**")

# Comando: Ataque Físico (simplificado, com mitigação)
@bot.command()
async def attack_physical(ctx, target_id: int):
    data = load_data()
    player_id = str(ctx.author.id)
    if player_id not in data['players']:
        await ctx.send("❌ Ficha não encontrada!")
        return
    char = data['players'][player_id]
    die = PATENT_DICE[char['patent']]
    hit_roll = random.randint(1, die) + char['agi']
    damage_roll = random.randint(1, 4) + char['for']
    target = data['npcs'].get(str(target_id), {'agi': 5, 'pv': 20, 'patent': 'Bronze'})
    target_agi = target['agi']
    mitigation = MITIGATION.get(target['patent'], 0)
    if hit_roll >= target_agi:
        final_damage = max(0, damage_roll - mitigation)
        target['pv'] = max(0, target['pv'] - final_damage)
        data['npcs'][str(target_id)] = target
        save_data(data)
        await ctx.send(f"👊 **{char['name']} acerta!** Dano: {damage_roll} - Mitig. ({mitigation}) = **{final_damage}** | PV alvo: {target['pv']}")
    else:
        await ctx.send(f"👊 **{char['name']} erra!** Rolagem: {hit_roll} vs AGI {target_agi}")

# Comando: Golpe Especial (com teste de Vontade)
@bot.command()
async def special_move(ctx, *, move_info):
    # Parse: "NomeDoGolpe target_id"
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
    die = PATENT_DICE[char['patent']]
    will_test = random.randint(1, die) + char['von']
    target = data['npcs'].get(str(target_id), {'patent': 'Bronze', 'pv': 20})
    target_patent = target['patent']
    dc = 10 + list(PATENT_DICE.keys()).index(target_patent) * 2
    if will_test >= dc:
        dice_count = {'Bronze': 2, 'Prata': 3, 'Ouro': 3, 'Semideus': 4, 'Divindade': 5}[char['patent']]
        damage = sum(random.randint(1, 4) for _ in range(dice_count)) + char['cos'] + (char['cos'] // 3)
        mitigation = MITIGATION.get(target_patent, 0)
        final_damage = max(0, damage - mitigation)
        target['pv'] = max(0, target['pv'] - final_damage)
        data['npcs'][str(target_id)] = target
        save_data(data)
        await ctx.send(f"🌌 **{char['name']} usa {move_name}!** Sucesso! Dano: **{final_damage}** | PV alvo: {target['pv']}")
    else:
        bonus_damage = char['cos'] // 2
        await ctx.send(f"🌌 **{char['name']} falha em {move_name}!** Rolagem: {will_test} vs DC {dc} | Dano fraco: {bonus_damage}")

# Comando: Adicionar XP (com limite de sessão do Manual)
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
    if data['players'][player_id]['xp'] > 150:  # Máx. por sessão
        data['players'][player_id]['xp'] = 150
        await ctx.send("⚠️ XP limitado a 150 por sessão!")
    save_data(data)
    await ctx.send(f"✅ +{total_xp} XP para {data['players'][player_id]['name']}! Total: {data['players'][player_id]['xp']}")

# Comando: Calcular XP Mestre/Ouro (média semanal)
@bot.command()
async def calc_master_xp(ctx):
    data = load_data()
    players_xp = [char['xp'] for char in data['players'].values() if char['xp'] > 0]
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

# REMOVA a parte do Flask do seu código atual e use isso no final:
keep_alive()  # <-- Inicia o servidor Flask

from config import BOT_TOKEN as token
if token is None:
    print("❌ ERRO: BOT_TOKEN não encontrado!")
else:
    print("✅ Token encontrado, iniciando bot...")
    bot.run(token)