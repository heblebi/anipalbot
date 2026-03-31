"""
Anipal — Level rollerini sunucuya ekler.
Bir kez çalıştır, biter.
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

LEVEL_ROLES = [
    # (isim, renk, level)
    ("🌱 Anipal Acemisi",   discord.Color.from_rgb(144, 238, 144), 0),
    ("🌿 Anipal Gezgini",   discord.Color.from_rgb(60,  179, 113), 5),
    ("⭐ Anipal Yıldızı",   discord.Color.from_rgb(255, 215, 0),   10),
    ("🌟 Anipal Ustası",    discord.Color.from_rgb(255, 165, 0),   15),
    ("💫 Anipal Efsanesi",  discord.Color.from_rgb(255, 105, 180), 20),
    ("🔥 Anipal Kahraman",  discord.Color.from_rgb(255, 69,  0),   25),
    ("💎 Anipal Elmas",     discord.Color.from_rgb(0,   191, 255), 30),
    ("🏆 Anipal Sampiyonu", discord.Color.from_rgb(218, 165, 32),  35),
    ("🌙 Anipal Efendisi",  discord.Color.from_rgb(147, 112, 219), 40),
    ("⚡ Anipal Efsane",    discord.Color.from_rgb(255, 255, 0),   45),
    ("🎌 Anipal Tanrisi",   discord.Color.from_rgb(220, 20,  60),  50),
]


@bot.event
async def on_ready():
    print(f"Baglandi: {bot.user}")
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        print("Sunucu bulunamadi!")
        await bot.close()
        return

    mevcut_roller = [r.name for r in guild.roles]
    print(f"Sunucu: {guild.name}")
    print("-" * 40)

    for name, color, level in LEVEL_ROLES:
        if name in mevcut_roller:
            print(f"  Zaten var: {name}")
            continue
        await guild.create_role(
            name=name,
            color=color,
            hoist=True,       # Sağ panelde göster (level rolleri hoist olacak)
            mentionable=True,
            permissions=discord.Permissions(send_messages=True, read_messages=True),
        )
        print(f"  Olusturuldu: {name} (Level {level})")
        await asyncio.sleep(0.5)

    print("-" * 40)
    print("Tamamlandi!")
    await bot.close()


if __name__ == "__main__":
    bot.run(TOKEN)
