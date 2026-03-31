"""
Anipal Discord Sunucu Kurulum Scripti
Bir kez çalıştır, tüm roller / kategoriler / kanallar otomatik oluşur.
"""

import discord
from discord.ext import commands
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.guilds  = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ══════════════════════════════════════════════════════════════════════════════
#  ROLLER
# ══════════════════════════════════════════════════════════════════════════════

ROLE_DEFS = [
    # ── Yönetim ──────────────────────────────────────────────────────────────
    {
        "name": "👑 Anipal Yöneticisi",
        "color": discord.Color.from_rgb(255, 165, 0),
        "permissions": discord.Permissions(administrator=True),
        "hoist": True, "mentionable": True,
    },
    {
        "name": "🛡️ Anipal Discord Moderatör",
        "color": discord.Color.from_rgb(87, 242, 135),
        "permissions": discord.Permissions(
            manage_messages=True, kick_members=True, ban_members=True,
            mute_members=True, view_audit_log=True, manage_nicknames=True,
        ),
        "hoist": True, "mentionable": True,
    },
    # ── Özel yetki ───────────────────────────────────────────────────────────
    {
        "name": "📡 Yayın Yetkisi",
        "color": discord.Color.from_rgb(255, 50, 50),
        "permissions": discord.Permissions(stream=True, connect=True, speak=True),
        "hoist": False, "mentionable": False,
    },
    # ── Kullanıcı unvanları ──────────────────────────────────────────────────
    {
        "name": "🎌 Anipal Otakusu",
        "color": discord.Color.from_rgb(255, 80, 80),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": True, "mentionable": True,
    },
    {
        "name": "☕ Anipal Müdavimi",
        "color": discord.Color.from_rgb(193, 126, 60),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": True, "mentionable": True,
    },
    {
        "name": "🌸 Anime Aşığı",
        "color": discord.Color.from_rgb(255, 150, 200),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": True,
    },
    {
        "name": "👁️ Seyreden",
        "color": discord.Color.from_rgb(130, 130, 130),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    # ── Cinsiyet rolleri ─────────────────────────────────────────────────────
    {
        "name": "🚺 Kadın",
        "color": discord.Color.from_rgb(255, 105, 180),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "🚹 Erkek",
        "color": discord.Color.from_rgb(70, 130, 255),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    # ── Renk rolleri ─────────────────────────────────────────────────────────
    {
        "name": "❤️ Kırmızı",
        "color": discord.Color.from_rgb(220, 50,  50),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "💙 Mavi",
        "color": discord.Color.from_rgb(50,  100, 220),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "💚 Yeşil",
        "color": discord.Color.from_rgb(50,  200, 80),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "💛 Sarı",
        "color": discord.Color.from_rgb(240, 210, 40),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "💜 Mor",
        "color": discord.Color.from_rgb(160, 60,  220),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "🧡 Turuncu",
        "color": discord.Color.from_rgb(240, 130, 30),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "🖤 Siyah",
        "color": discord.Color.from_rgb(40,  40,  40),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
    {
        "name": "🩷 Pembe",
        "color": discord.Color.from_rgb(255, 180, 210),
        "permissions": discord.Permissions(send_messages=True, read_messages=True),
        "hoist": False, "mentionable": False,
    },
]


async def setup_roles(guild: discord.Guild) -> dict[str, discord.Role]:
    print("🎭 Roller oluşturuluyor...")
    roles: dict[str, discord.Role] = {}

    for d in ROLE_DEFS:
        role = await guild.create_role(
            name=d["name"],
            color=d["color"],
            permissions=d["permissions"],
            hoist=d["hoist"],
            mentionable=d["mentionable"],
        )
        roles[d["name"]] = role
        print(f"  ✅ {d['name']}")
        await asyncio.sleep(0.4)

    return roles


# ══════════════════════════════════════════════════════════════════════════════
#  KATEGORİLER & KANALLAR
# ══════════════════════════════════════════════════════════════════════════════

async def setup_channels(guild: discord.Guild, roles: dict[str, discord.Role]):
    print("\n📁 Kategoriler ve kanallar oluşturuluyor...")

    everyone   = guild.default_role
    yonetici   = roles["👑 Anipal Yöneticisi"]
    moderator  = roles["🛡️ Anipal Discord Moderatör"]
    yayin      = roles["📡 Yayın Yetkisi"]

    # ── İzin şablonları ───────────────────────────────────────────────────────
    # Sadece yönetici yazabilir
    yonetici_yazar = {
        everyone:  discord.PermissionOverwrite(send_messages=False, read_messages=True),
        yonetici:  discord.PermissionOverwrite(send_messages=True,  read_messages=True),
        moderator: discord.PermissionOverwrite(send_messages=False, read_messages=True),
    }
    # Herkes okur/yazar
    herkes = {
        everyone: discord.PermissionOverwrite(send_messages=True, read_messages=True),
    }
    # Sadece yönetim görür
    gizli = {
        everyone:  discord.PermissionOverwrite(read_messages=False),
        yonetici:  discord.PermissionOverwrite(read_messages=True, send_messages=True),
        moderator: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    # Sesli: herkes bağlanır, sadece yayın yetkisi olanlar yayın açar
    sesli_normal = {
        everyone: discord.PermissionOverwrite(connect=True, speak=True, stream=False, use_voice_activation=True),
        yayin:    discord.PermissionOverwrite(connect=True, speak=True, stream=True),
        yonetici: discord.PermissionOverwrite(connect=True, speak=True, stream=True),
    }
    # Yönetim sesli: sadece yönetim bağlanır
    sesli_yonetim = {
        everyone:  discord.PermissionOverwrite(connect=False),
        yonetici:  discord.PermissionOverwrite(connect=True, speak=True, stream=True),
        moderator: discord.PermissionOverwrite(connect=True, speak=True),
    }

    # ── 1. DUYURULAR ──────────────────────────────────────────────────────────
    cat1 = await guild.create_category("📢 DUYURULAR & GÜNCELLEMELER")
    print("\n  📁 DUYURULAR & GÜNCELLEMELER")
    for name, topic in [
        ("duyurular",     "Anipal resmi duyuruları — sadece yöneticiler yazar."),
        ("guncellemeler", "Site güncellemeleri — sadece yöneticiler yazar."),
        ("site-haberleri","Anipal ile ilgili genel haberler."),
    ]:
        await guild.create_text_channel(name, category=cat1, overwrites=yonetici_yazar, topic=topic)
        print(f"    ✅ #{name}")
        await asyncio.sleep(0.3)

    # ── 2. YÖNETİM (gizli) ────────────────────────────────────────────────────
    cat2 = await guild.create_category("🔒 YÖNETİM", overwrites=gizli)
    print("\n  📁 YÖNETİM (gizli)")
    for name, topic in [
        ("yonetim-genel", "Yönetim genel tartışma kanalı."),
        ("moderasyon",    "Moderatör kararları ve notlar."),
        ("log",           "Bot logları ve moderasyon geçmişi."),
    ]:
        await guild.create_text_channel(name, category=cat2, overwrites=gizli, topic=topic)
        print(f"    ✅ #{name}")
        await asyncio.sleep(0.3)

    await guild.create_voice_channel("🏛️ Anipal Toplantı", category=cat2, overwrites=sesli_yonetim)
    print("    ✅ 🏛️ Anipal Toplantı (ses)")
    await asyncio.sleep(0.3)

    # ── 3. KARŞILAMA ──────────────────────────────────────────────────────────
    cat3 = await guild.create_category("👋 KARŞILAMA")
    print("\n  📁 KARŞILAMA")
    karsilama_kanallar = [
        ("kurallar",      {everyone: discord.PermissionOverwrite(send_messages=False, read_messages=True)}, "Sunucu kuralları."),
        ("hos-geldin",    {everyone: discord.PermissionOverwrite(send_messages=False, read_messages=True)}, "Yeni üyelere hoş geldin!"),
        ("kendini-tanit", herkes, "Kendini tanıt!"),
        ("rol-al",        herkes, "Reaksiyon vererek rol al."),
    ]
    rol_al_ch = None
    for name, ow, topic in karsilama_kanallar:
        ch = await guild.create_text_channel(name, category=cat3, overwrites=ow, topic=topic)
        if name == "rol-al":
            rol_al_ch = ch
        print(f"    ✅ #{name}")
        await asyncio.sleep(0.3)

    # ── 4. ANİPAL SOHBET ──────────────────────────────────────────────────────
    cat4 = await guild.create_category("💬 ANİPAL SOHBET")
    print("\n  📁 ANİPAL SOHBET")

    await guild.create_text_channel("anipal-sohbet",  category=cat4, overwrites=herkes, topic="Genel sohbet kanalı.")
    await guild.create_text_channel("bot-komutlari",  category=cat4, overwrites=herkes, topic="Bot komutlarını buraya yaz.")
    print("    ✅ #anipal-sohbet")
    print("    ✅ #bot-komutlari")

    for i in range(1, 11):
        await guild.create_voice_channel(f"Sohbet {i}", category=cat4, overwrites=sesli_normal)
        print(f"    ✅ Sohbet {i} (ses)")
        await asyncio.sleep(0.3)

    # ── 5. ANİME ──────────────────────────────────────────────────────────────
    cat5 = await guild.create_category("🎌 ANİME")
    print("\n  📁 ANİME")
    for name, topic in [
        ("anime-onerileri",    "Anime önerilerini paylaş."),
        ("sezon-tartismalari", "Bu sezon yayınlanan animeler."),
        ("izleme-listesi",     "İzleme listeni paylaş."),
        ("favori-karakterler", "En sevdiğin karakterler."),
        ("spoiler-zone",       "⚠️ Spoiler içerir! Dikkatli ol."),
        ("anime-muzikleri",    "OP/ED paylaşımları."),
    ]:
        await guild.create_text_channel(name, category=cat5, overwrites=herkes, topic=topic)
        print(f"    ✅ #{name}")
        await asyncio.sleep(0.3)

    # ── 6. MEDYA ──────────────────────────────────────────────────────────────
    cat6 = await guild.create_category("🎨 MEDYA")
    print("\n  📁 MEDYA")
    for name, topic in [
        ("fan-art",           "Fan art paylaşımları."),
        ("ekran-goruntuleri", "Anime ekran görüntüleri."),
        ("gif-meme",          "Komik gifler ve memeler."),
    ]:
        await guild.create_text_channel(name, category=cat6, overwrites=herkes, topic=topic)
        print(f"    ✅ #{name}")
        await asyncio.sleep(0.3)

    # ── 7. SİTE DESTEK ────────────────────────────────────────────────────────
    cat7 = await guild.create_category("🌐 ANİPAL SİTE")
    print("\n  📁 ANİPAL SİTE")
    for name, topic in [
        ("site-destek",    "Site ile ilgili yardım."),
        ("hata-bildirimi", "Hata bulursan buraya yaz."),
        ("oneri-kutusu",   "Site için önerilerin."),
    ]:
        await guild.create_text_channel(name, category=cat7, overwrites=herkes, topic=topic)
        print(f"    ✅ #{name}")
        await asyncio.sleep(0.3)

    return rol_al_ch


# ══════════════════════════════════════════════════════════════════════════════
#  ROL ALMA MESAJLARI
# ══════════════════════════════════════════════════════════════════════════════

CINSIYET_EMOJILER = {
    "🚺": "🚺 Kadın",
    "🚹": "🚹 Erkek",
}

RENK_EMOJILER = {
    "❤️":  "❤️ Kırmızı",
    "💙":  "💙 Mavi",
    "💚":  "💚 Yeşil",
    "💛":  "💛 Sarı",
    "💜":  "💜 Mor",
    "🧡":  "🧡 Turuncu",
    "🖤":  "🖤 Siyah",
    "🩷":  "🩷 Pembe",
}

UNVAN_EMOJILER = {
    "🎌":  "🎌 Anipal Otakusu",
    "☕":  "☕ Anipal Müdavimi",
    "🌸":  "🌸 Anime Aşığı",
    "👁️": "👁️ Seyreden",
}


async def send_role_messages(guild: discord.Guild, rol_al_ch: discord.TextChannel) -> dict:
    """#rol-al kanalına anket mesajları gönderir, mesaj ID'lerini döner."""
    print("\n🎭 Rol alma mesajları gönderiliyor...")
    message_ids = {}

    # Cinsiyet
    embed1 = discord.Embed(
        title="🚻 Cinsiyet Rolü",
        description=(
            "Aşağıdaki emojiye tıklayarak cinsiyet rolü alabilirsin.\n\n"
            "🚺 → Kadın\n"
            "🚹 → Erkek"
        ),
        color=discord.Color.from_rgb(255, 150, 200),
    )
    msg1 = await rol_al_ch.send(embed=embed1)
    for emoji in CINSIYET_EMOJILER:
        await msg1.add_reaction(emoji)
    message_ids["cinsiyet"] = msg1.id
    print("  ✅ Cinsiyet anketi gönderildi")
    await asyncio.sleep(1)

    # Renk
    embed2 = discord.Embed(
        title="🎨 Renk Rolü",
        description=(
            "En sevdiğin renge tıkla!\n\n"
            "❤️ Kırmızı  |  💙 Mavi  |  💚 Yeşil  |  💛 Sarı\n"
            "💜 Mor  |  🧡 Turuncu  |  🖤 Siyah  |  🩷 Pembe"
        ),
        color=discord.Color.from_rgb(180, 100, 255),
    )
    msg2 = await rol_al_ch.send(embed=embed2)
    for emoji in RENK_EMOJILER:
        await msg2.add_reaction(emoji)
    message_ids["renk"] = msg2.id
    print("  ✅ Renk anketi gönderildi")
    await asyncio.sleep(1)

    # Unvan
    embed3 = discord.Embed(
        title="🎌 Unvan Rolü",
        description=(
            "Kendine uygun unvanı seç!\n\n"
            "🎌 → Anipal Otakusu *(anime tutkunu)*\n"
            "☕ → Anipal Müdavimi *(her gün burada)*\n"
            "🌸 → Anime Aşığı *(anime yaşam tarzım)*\n"
            "👁️ → Seyreden *(sessiz seyrederim)*"
        ),
        color=discord.Color.from_rgb(255, 100, 100),
    )
    msg3 = await rol_al_ch.send(embed=embed3)
    for emoji in UNVAN_EMOJILER:
        await msg3.add_reaction(emoji)
    message_ids["unvan"] = msg3.id
    print("  ✅ Unvan anketi gönderildi")

    return message_ids


# ══════════════════════════════════════════════════════════════════════════════
#  KURALLAR EMBED
# ══════════════════════════════════════════════════════════════════════════════

async def send_rules(guild: discord.Guild):
    kurallar_ch = discord.utils.get(guild.text_channels, name="kurallar")
    if not kurallar_ch:
        return

    embed = discord.Embed(
        title="🎌 Anipal Discord — Sunucu Kuralları",
        color=discord.Color.from_rgb(255, 100, 100),
    )
    embed.add_field(name="1️⃣ Saygı", value="Herkese saygılı davran. Hakaret, küfür ve ayrımcılık yasaktır.", inline=False)
    embed.add_field(name="2️⃣ Spam", value="Aynı mesajı tekrarlamak veya flood yapmak yasaktır.", inline=False)
    embed.add_field(name="3️⃣ Reklam", value="İzinsiz reklam ve sunucu davetiyesi paylaşmak yasaktır.", inline=False)
    embed.add_field(name="4️⃣ Spoiler", value="Spoiler içeriklerini yalnızca #spoiler-zone kanalında paylaş.", inline=False)
    embed.add_field(name="5️⃣ NSFW", value="18+ içerik kesinlikle yasaktır.", inline=False)
    embed.add_field(name="6️⃣ Moderatörlere uy", value="Yönetici ve moderatörlerin kararlarına uy.", inline=False)
    embed.set_footer(text="Anipal Ekibi • Eğlenceli seyirler! 🍿")
    await kurallar_ch.send(embed=embed)
    print("\n📜 Kurallar gönderildi.")


# ══════════════════════════════════════════════════════════════════════════════
#  BOT EVENTS
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"\n🤖 {bot.user} bağlandı.")
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        print("❌ Sunucu bulunamadı! GUILD_ID'yi kontrol et.")
        await bot.close()
        return

    print(f"🏠 {guild.name}\n{'=' * 50}")

    roles    = await setup_roles(guild)
    rol_al_ch = await setup_channels(guild, roles)
    msg_ids  = await send_role_messages(guild, rol_al_ch)
    await send_rules(guild)

    # Mesaj ID'lerini kaydet (bot.py okuyacak)
    with open("reaction_roles.json", "w", encoding="utf-8") as f:
        json.dump(msg_ids, f, ensure_ascii=False, indent=2)
    print("\n💾 reaction_roles.json kaydedildi.")

    print(f"\n{'=' * 50}")
    print("✅ Kurulum tamamlandı! Discord sunucunu kontrol et.")
    await bot.close()


if __name__ == "__main__":
    bot.run(TOKEN)
