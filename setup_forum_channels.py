"""
hata-bildirimi ve oneri-kutusu kanallarını forum kanalına dönüştürür.
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

bot = commands.Bot(command_prefix="\x00", intents=intents)


@bot.event
async def on_ready():
    guild    = bot.get_guild(GUILD_ID)
    everyone = guild.default_role

    normal_everyone = {
        everyone: discord.PermissionOverwrite(send_messages=True, read_messages=True),
    }

    # Site kategorisini bul
    category = discord.utils.get(guild.categories, name="🌐 ANİPAL SİTE")
    if not category:
        print("Kategori bulunamadi, genel oluşturulacak.")

    forum_configs = [
        {
            "eski_isim_aramalari": ["🐛│hata-bildirimi", "hata-bildirimi"],
            "yeni_isim":  "🐛│hata-bildirimi",
            "topic":      "Site hatalarını buraya bildir. Her hata için yeni konu aç.",
            "tags": [
                discord.ForumTag(name="🔴 Kritik"),
                discord.ForumTag(name="🟡 Orta"),
                discord.ForumTag(name="🟢 Düşük"),
                discord.ForumTag(name="✅ Çözüldü"),
            ],
            "default_reaction": "🐛",
        },
        {
            "eski_isim_aramalari": ["💡│oneri-kutusu", "oneri-kutusu"],
            "yeni_isim":  "💡│oneri-kutusu",
            "topic":      "Site için önerilerini paylaş. Her öneri için yeni konu aç.",
            "tags": [
                discord.ForumTag(name="💡 Öneri"),
                discord.ForumTag(name="🎨 Tasarım"),
                discord.ForumTag(name="⚙️ Özellik"),
                discord.ForumTag(name="✅ Onaylandı"),
                discord.ForumTag(name="❌ Reddedildi"),
            ],
            "default_reaction": "💡",
        },
    ]

    for config in forum_configs:
        # Eski kanalı bul ve sil
        eski_kanal = None
        for isim in config["eski_isim_aramalari"]:
            eski_kanal = discord.utils.get(guild.text_channels, name=isim)
            if eski_kanal:
                break

        if eski_kanal:
            position = eski_kanal.position
            await eski_kanal.delete()
            print(f"  Silindi: #{eski_kanal.name}")
            await asyncio.sleep(0.5)
        else:
            position = 0
            print(f"  Eski kanal bulunamadi, yeni oluşturuluyor.")

        # Forum kanalı oluştur
        forum = await guild.create_forum(
            name=config["yeni_isim"],
            category=category,
            topic=config["topic"],
            available_tags=config["tags"],
            overwrites=normal_everyone,
        )
        print(f"  Forum olusturuldu: #{forum.name}")
        await asyncio.sleep(0.5)

    print("Tamamlandi!")
    await bot.close()


if __name__ == "__main__":
    bot.run(TOKEN)
