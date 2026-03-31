"""
Anipal — Yönetim ve Anipal kanallarına tilki emojisi ekler.
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

RENAMES = {
    # Yönetim kanalları
    "👑│yonetim-genel":      "🦊│yonetim-genel",
    "🛡️│moderasyon":         "🦊│moderasyon",
    "📋│log":                "🦊│log",
    # Duyuru / Anipal kanalları
    "📢│duyurular":          "🦊│duyurular",
    "🔄│guncellemeler":      "🦊│guncellemeler",
    "🌐│site-haberleri":     "🦊│site-haberleri",
    "💬│anipal-sohbet":      "🦊│anipal-sohbet",
    "🆘│site-destek":        "🦊│site-destek",
    "🐛│hata-bildirimi":     "🦊│hata-bildirimi",
    "💡│oneri-kutusu":       "🦊│oneri-kutusu",
}

VOICE_RENAMES = {
    "🏛️│Anipal Toplantı": "🦊│Anipal Toplantı",
}


@bot.event
async def on_ready():
    print(f"Baglandi: {bot.user}")
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        print("Sunucu bulunamadi!")
        await bot.close()
        return

    print(f"Sunucu: {guild.name}")
    print("-" * 40)

    for ch in guild.text_channels:
        if ch.name in RENAMES:
            yeni = RENAMES[ch.name]
            await ch.edit(name=yeni)
            print(f"  #{ch.name} -> #{yeni}")
            await asyncio.sleep(0.5)

    for ch in guild.voice_channels:
        if ch.name in VOICE_RENAMES:
            yeni = VOICE_RENAMES[ch.name]
            await ch.edit(name=yeni)
            print(f"  {ch.name} -> {yeni}")
            await asyncio.sleep(0.5)

    print("-" * 40)
    print("Tamamlandi!")
    await bot.close()


if __name__ == "__main__":
    bot.run(TOKEN)
