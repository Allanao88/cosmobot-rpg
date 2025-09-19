import discord
from discord.ext import commands
import json
import random
import asyncio
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

# Configuração do bot
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Banco de dados simples (JSON) - Persiste fichas e XP
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

# Dados por patente
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

# Comando: Ajuda (atualizado com novos comandos)
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
        name="!add_move [nome_do_golpe]",
        value="Adiciona golpe especial. Ex: `!add_move Meteoro de Pégaso`",
        inline=False
    )
    embed.add_field(
        name="!add_talent [nome_do_talento]",
        value="Adiciona talento. Ex: `!add_talent Sentido Cosmo`",
        inline=False
    )
    embed.add_field(
        name="!remove_move [nome_do_golpe]",
        value="Remove golpe especial. Ex: `!remove_move Meteoro`",
        inline=False
    )
    embed.add_field(
        name="!update_hp [novo_pv]",
        value="Atualiza PV. Ex: `!update_hp 100`",
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

# --- Resto dos comandos já está com a identação correta ---
# (create_character, sheet, add_move, add_talent, remove_move, update_hp,
# roll, initiative, attack_physical, special_move, add_xp, calc_master_xp, etc.)

# Logs para diagnóstico
@bot.event
async def on_message(message):
    print(f"📩 Mensagem recebida: {message.content} - Autor: {message.author}")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    print(f"❌ Erro no comando: {error}")

keep_alive()

token = os.getenv("BOT_TOKEN")
if token is None:
    print("❌ ERRO: BOT_TOKEN não encontrado!")
else:
    print("✅ Token encontrado, iniciando bot...")
    bot.run(token)
