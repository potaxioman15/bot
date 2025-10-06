import discord
from discord.ext import commands
from google import genai
from dotenv import load_dotenv
import os
import asyncio

load_dotenv("wahh.env")

gemini_api_key = os.getenv("GEMINI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")
if not gemini_api_key or not discord_token:
    raise SystemExit("Faltan GEMINI_API_KEY o DISCORD_TOKEN en wahh.env")

client_gemini = genai.Client(api_key=gemini_api_key)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ----- CONFIG -----
MAX_PROMPT_CHARS = 6000
PERSONALIDADES_PATH = "./personalidades"

# Historial: {user_id: [{"role":"user"/"bot","content": "..."} , ...]}
historial = {}

# ---- FUNCIONES -----
def load_personalidades():
    global PERSONALIDADES
    nueva = {}
    if os.path.isdir(PERSONALIDADES_PATH):
        for archivo in os.listdir(PERSONALIDADES_PATH):
            if archivo.endswith(".txt"):
                nombre = archivo[:-4].lower()
                with open(os.path.join(PERSONALIDADES_PATH, archivo), "r", encoding="utf-8") as f:
                    nueva[nombre] = f.read().strip()
    PERSONALIDADES = nueva
    return PERSONALIDADES

PERSONALIDADES = load_personalidades()
current_personality_name = next(iter(PERSONALIDADES.keys()), None)
personalidad_actual_content = PERSONALIDADES.get(current_personality_name, "")

def build_prompt(user_id: int, new_user_message: str) -> str:
    entries = historial.get(user_id, []).copy()
    entries.append({"role": "user", "content": new_user_message})

    def render(entries_list):
        parts = [personalidad_actual_content.strip(), ""]
        for e in entries_list:
            parts.append(f"Usuario: {e['content']}" if e["role"] == "user" else f"Bot: {e['content']}")
        return "\n".join(parts)

    prompt = render(entries)
    while len(prompt) > MAX_PROMPT_CHARS and len(entries) > 1:
        entries.pop(0)
        prompt = render(entries)
    return prompt

# ----- EVENTOS -----
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    print(f"Personalidades disponibles: {', '.join(PERSONALIDADES.keys())}")
    print(f"Personalidad inicial: {current_personality_name}")

# ----- COMANDOS -----
@bot.command()
async def gemini(ctx, *, prompt: str):
    user_id = ctx.author.id
    try:
        prompt_completo = build_prompt(user_id, prompt)
        response = client_gemini.models.generate_content(model="gemini-2.5-flash", contents=prompt_completo)
        respuesta = getattr(response, "text", None) or str(response)
        respuesta = respuesta.strip()
        if not respuesta:
            await ctx.send("El modelo no devolvió texto.")
            return
        historial.setdefault(user_id, []).append({"role": "user", "content": prompt})
        historial.setdefault(user_id, []).append({"role": "bot", "content": respuesta})
        for i in range(0, len(respuesta), 2000):
            await ctx.send(respuesta[i:i+2000])
            await asyncio.sleep(0.15)
    except Exception as e:
        print("Error en gemini:", e)
        await ctx.send("Ocurrió un error al llamar a la API.")

@bot.command(name="switchpersonality")
async def switch_personality(ctx, nombre: str = None):
    global current_personality_name, personalidad_actual_content
    if not nombre:
        await ctx.send(f"❌ Debes indicar una personalidad. Disponibles: {', '.join(PERSONALIDADES.keys())}")
        return
    nombre = nombre.lower()
    if nombre in PERSONALIDADES:
        current_personality_name = nombre
        personalidad_actual_content = PERSONALIDADES[nombre]
        await ctx.send(f"✅ Personalidad cambiada a **{nombre}**")
    else:
        await ctx.send(f"❌ No existe la personalidad '{nombre}'. Disponibles: {', '.join(PERSONALIDADES.keys())}")

@bot.command(name="listpersonalities")
async def list_personalities(ctx):
    names = ", ".join(PERSONALIDADES.keys()) or "(ninguna)"
    await ctx.send(f"Personalidades: {names}")

@bot.command(name="reloadpersonalities")
async def reload_personalities_cmd(ctx):
    global current_personality_name, personalidad_actual_content
    load_personalidades()
    if current_personality_name not in PERSONALIDADES:
        current_personality_name = next(iter(PERSONALIDADES.keys()), None)
    personalidad_actual_content = PERSONALIDADES.get(current_personality_name, "")
    await ctx.send(f"✅ Personalidades recargadas. Disponibles: {', '.join(PERSONALIDADES.keys())}")

@bot.command(name="histlen")
async def hist_len(ctx):
    l = len(historial.get(ctx.author.id, []))
    await ctx.send(f"Tienes {l} entradas en el historial (user+bot cuentan por separado).")

@bot.command(name="reset")
async def reset_history(ctx, member: discord.Member = None):
    target = member or ctx.author
    if member and not ctx.author.guild_permissions.manage_messages:
        await ctx.send("No tienes permiso para reiniciar el historial de otra persona.")
        return
    if historial.pop(target.id, None) is None:
        await ctx.send(f"No había historial para {target.display_name}.")
    else:
        await ctx.send(f"Historial de {target.display_name} reiniciado ✅")

import random  # Solo si no lo tienes ya importado

# ---------- COMANDOS DE ENTRETENIMIENTO ----------

# Comando 8ball
@bot.command(name="8ball")
async def eight_ball(ctx, *, pregunta: str):
    respuestas = [
        "Sí",
        "No",
        "Tal vez",
        "Definitivamente sí",
        "Definitivamente no",
        "Pregunta otra vez más tarde",
        "cállate."
    ]
    respuesta = random.choice(respuestas)
    await ctx.send(respuesta)

# Comando ruleta rusa
@bot.command(name="ruleta")
async def ruleta_rusa(ctx):
    disparo = random.randint(1, 6)
    if disparo == 1:
        await ctx.send("BOOM! Has perdido...")
    else:
        await ctx.send("Puf, estás vivo... por ahora.")

# Comando dado
@bot.command(name="dado")
async def tirar_dado(ctx):
    resultado = random.randint(1, 6)
    await ctx.send(f"Has sacado un {resultado}.")

# Comando moneda
@bot.command(name="moneda")
async def lanzar_moneda(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    await ctx.send(f"Has lanzado la moneda: {resultado}")

bot.run(DISCORD_TOKEN)
