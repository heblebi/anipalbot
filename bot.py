"""
Anipal Discord Botu — Leveling sistemi dahil.
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members         = True
intents.message_content = True
intents.reactions       = True
intents.voice_states    = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ══════════════════════════════════════════════════════════════════════════════
#  LEVEL SİSTEMİ — VERİ
# ══════════════════════════════════════════════════════════════════════════════

LEVELS_FILE = "levels.json"

# Level → Rol adı
LEVEL_ROLES: dict[int, str] = {
    0:  "🌱 Anipal Acemisi",
    5:  "🌿 Anipal Gezgini",
    10: "⭐ Anipal Yıldızı",
    15: "🌟 Anipal Ustası",
    20: "💫 Anipal Efsanesi",
    25: "🔥 Anipal Kahraman",
    30: "💎 Anipal Elmas",
    35: "🏆 Anipal Sampiyonu",
    40: "🌙 Anipal Efendisi",
    45: "⚡ Anipal Efsane",
    50: "🎌 Anipal Tanrisi",
}
ALL_LEVEL_ROLE_NAMES = set(LEVEL_ROLES.values())

# Mesaj başına XP bekleme süresi (saniye)
MSG_COOLDOWN = 60

# Seste dakika başı XP
VOICE_XP_PER_MIN = 5

# Seste takip: {user_id: join_timestamp}
voice_join_times: dict[int, float] = {}


def load_levels() -> dict:
    if os.path.exists(LEVELS_FILE):
        with open(LEVELS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_levels(data: dict):
    with open(LEVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(data: dict, uid: int) -> dict:
    key = str(uid)
    if key not in data:
        data[key] = {
            "xp": 0,
            "level": 0,
            "total_xp": 0,
            "voice_minutes": 0,
            "last_msg": 0,
        }
    return data[key]


def xp_required(level: int) -> int:
    """Bu leveldan bir sonrakine geçmek için gereken XP."""
    return 100 + level * 50


def get_level_role_name(level: int) -> str:
    role_level = 0
    for lvl in sorted(LEVEL_ROLES.keys(), reverse=True):
        if level >= lvl:
            role_level = lvl
            break
    return LEVEL_ROLES[role_level]


def progress_bar(current: int, total: int, length: int = 12) -> str:
    filled = int(length * current / total) if total > 0 else 0
    bar    = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


# ══════════════════════════════════════════════════════════════════════════════
#  LEVEL ATLAMA
# ══════════════════════════════════════════════════════════════════════════════

async def add_xp(member: discord.Member, xp_amount: int, channel: discord.TextChannel = None):
    data    = load_levels()
    user    = get_user(data, member.id)
    old_lvl = user["level"]

    user["xp"]       += xp_amount
    user["total_xp"] += xp_amount

    # Level atlama kontrolü
    leveled_up = False
    while user["xp"] >= xp_required(user["level"]):
        user["xp"]    -= xp_required(user["level"])
        user["level"] += 1
        leveled_up     = True

    save_levels(data)

    if leveled_up and old_lvl != user["level"]:
        await update_level_role(member, user["level"])

        if channel:
            role_name = get_level_role_name(user["level"])
            embed = discord.Embed(
                title="🎉 Level Atladı!",
                description=(
                    f"{member.mention} **Level {user['level']}** oldu!\n"
                    f"🦊 Yeni unvan: **{role_name}**"
                ),
                color=discord.Color.from_rgb(255, 165, 0),
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed, delete_after=15)


async def update_level_role(member: discord.Member, level: int):
    """Eski level rollerini kaldırır, yeni rolü ekler."""
    guild        = member.guild
    new_role_name = get_level_role_name(level)

    # Eski level rollerini kaldır
    roles_to_remove = [r for r in member.roles if r.name in ALL_LEVEL_ROLE_NAMES]
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)

    # Yeni rolü ekle
    new_role = discord.utils.get(guild.roles, name=new_role_name)
    if new_role:
        await member.add_roles(new_role)


# ══════════════════════════════════════════════════════════════════════════════
#  REAKSIYON ROL HARİTASI
# ══════════════════════════════════════════════════════════════════════════════

CINSIYET_EMOJILER = {"🚺": "🚺 Kadın",    "🚹": "🚹 Erkek"}
RENK_EMOJILER     = {
    "❤️": "❤️ Kırmızı", "💙": "💙 Mavi",    "💚": "💚 Yeşil",
    "💛": "💛 Sarı",     "💜": "💜 Mor",     "🧡": "🧡 Turuncu",
    "🖤": "🖤 Siyah",    "🩷": "🩷 Pembe",
}
UNVAN_EMOJILER = {
    "🎌": "🎌 Anipal Otakusu", "☕": "☕ Anipal Müdavimi",
    "🌸": "🌸 Anime Aşığı",   "👁️": "👁️ Seyreden",
}
ALL_EMOJI_ROLE_MAP = {**CINSIYET_EMOJILER, **RENK_EMOJILER, **UNVAN_EMOJILER}
EXCLUSIVE_GROUPS   = [list(CINSIYET_EMOJILER.values()), list(RENK_EMOJILER.values())]

REACTION_MSG_IDS: set[int] = set()


def load_reaction_ids():
    try:
        with open("reaction_roles.json", encoding="utf-8") as f:
            return set(json.load(f).values())
    except FileNotFoundError:
        return set()


# ══════════════════════════════════════════════════════════════════════════════
#  BACKGROUND TASK — Ses XP
# ══════════════════════════════════════════════════════════════════════════════

@tasks.loop(minutes=1)
async def voice_xp_task():
    """Her dakika seste olan kullanıcılara XP verir."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    now = time.time()
    for uid, join_time in list(voice_join_times.items()):
        if now - join_time >= 60:
            member = guild.get_member(uid)
            if member:
                data = load_levels()
                user = get_user(data, uid)
                user["voice_minutes"] += 1
                save_levels(data)
                await add_xp(member, VOICE_XP_PER_MIN)
            voice_join_times[uid] = now


# ══════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    global REACTION_MSG_IDS
    REACTION_MSG_IDS = load_reaction_ids()
    voice_xp_task.start()

    # Slash komutlarını senkronize et
    guild_obj = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild_obj)
    await bot.tree.sync(guild=guild_obj)

    print(f"Anipal Bot cevrimici!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🎌 Anipal",
        )
    )


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    # Acemi rolü ver
    acemi = discord.utils.get(guild.roles, name="🌱 Anipal Acemisi")
    if acemi:
        await member.add_roles(acemi)

    hos_geldin = discord.utils.get(guild.text_channels, name="👋│hos-geldin")
    if not hos_geldin:
        hos_geldin = discord.utils.get(guild.text_channels, name="hos-geldin")
    if hos_geldin:
        embed = discord.Embed(
            title=f"🎉 Hoş Geldin, {member.display_name}!",
            description=(
                f"**Anipal**'a hoş geldin {member.mention}! 🎌\n\n"
                "📜 Kurallarımızı oku → <#kurallar>\n"
                "🎭 Rolünü seç → <#rol-al>\n"
                "🙋 Kendini tanıt → <#kendini-tanit>"
            ),
            color=discord.Color.from_rgb(255, 100, 100),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Sunucuda şu an {guild.member_count} üye var!")
        await hos_geldin.send(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # Mesaj XP
    data = load_levels()
    user = get_user(data, message.author.id)
    now  = time.time()

    if now - user["last_msg"] >= MSG_COOLDOWN:
        xp_gain         = random.randint(15, 25)
        user["last_msg"] = now
        save_levels(data)
        await add_xp(message.author, xp_gain, message.channel)

    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return

    joined = before.channel is None and after.channel is not None
    left   = before.channel is not None and after.channel is None

    if joined:
        voice_join_times[member.id] = time.time()
    elif left:
        voice_join_times.pop(member.id, None)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id not in REACTION_MSG_IDS or payload.user_id == bot.user.id:
        return
    guild  = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member:
        return
    emoji     = str(payload.emoji)
    role_name = ALL_EMOJI_ROLE_MAP.get(emoji)
    if not role_name:
        return
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        return
    for group in EXCLUSIVE_GROUPS:
        if role_name in group:
            for other_name in group:
                if other_name != role_name:
                    other_role = discord.utils.get(guild.roles, name=other_name)
                    if other_role and other_role in member.roles:
                        await member.remove_roles(other_role)
    await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id not in REACTION_MSG_IDS:
        return
    guild  = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member:
        return
    emoji     = str(payload.emoji)
    role_name = ALL_EMOJI_ROLE_MAP.get(emoji)
    if not role_name:
        return
    role = discord.utils.get(guild.roles, name=role_name)
    if role and role in member.roles:
        await member.remove_roles(role)


# ══════════════════════════════════════════════════════════════════════════════
#  SLASH KOMUT — /stats
# ══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="stats", description="Seviye ve XP istatistiklerini gösterir.")
@app_commands.describe(uye="İstatistiklerini görmek istediğin üye (boş bırakırsan kendinki)")
async def stats(interaction: discord.Interaction, uye: discord.Member = None):
    member = uye or interaction.user
    data   = load_levels()
    user   = get_user(data, member.id)
    save_levels(data)

    level       = user["level"]
    current_xp  = user["xp"]
    total_xp    = user["total_xp"]
    voice_mins  = user["voice_minutes"]
    needed_xp   = xp_required(level)
    role_name   = get_level_role_name(level)
    bar         = progress_bar(current_xp, needed_xp)

    voice_h = voice_mins // 60
    voice_m = voice_mins % 60

    # Level emoji
    if level < 5:
        lvl_emoji = "🌱"
    elif level < 10:
        lvl_emoji = "🌿"
    elif level < 15:
        lvl_emoji = "⭐"
    elif level < 20:
        lvl_emoji = "🌟"
    elif level < 25:
        lvl_emoji = "💫"
    elif level < 30:
        lvl_emoji = "🔥"
    elif level < 35:
        lvl_emoji = "💎"
    elif level < 40:
        lvl_emoji = "🏆"
    elif level < 45:
        lvl_emoji = "🌙"
    elif level < 50:
        lvl_emoji = "⚡"
    else:
        lvl_emoji = "🎌"

    embed = discord.Embed(
        title=f"📊 {member.display_name} — İstatistikler",
        color=member.color if member.color.value else discord.Color.from_rgb(255, 100, 100),
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name=f"{lvl_emoji} Seviye",
        value=f"**{level}**",
        inline=True,
    )
    embed.add_field(
        name="🦊 Unvan",
        value=f"**{role_name}**",
        inline=True,
    )
    embed.add_field(
        name="\u200b",
        value="\u200b",
        inline=True,
    )
    embed.add_field(
        name="✨ Seviye XP",
        value=f"{bar}\n`{current_xp}` / `{needed_xp}` XP",
        inline=False,
    )
    embed.add_field(
        name="🏅 Toplam XP",
        value=f"`{total_xp}` XP",
        inline=True,
    )
    embed.add_field(
        name="🔊 Seste Geçirilen Süre",
        value=f"`{voice_h}s {voice_m}dk`",
        inline=True,
    )

    if level < 50:
        embed.set_footer(text=f"Sonraki level için {needed_xp - current_xp} XP gerekiyor!")
    else:
        embed.set_footer(text="Maksimum levele ulaştın! 🎌")

    await interaction.response.send_message(embed=embed)


# ══════════════════════════════════════════════════════════════════════════════
#  SLASH KOMUTLAR
# ══════════════════════════════════════════════════════════════════════════════

def yetkisiz(interaction: discord.Interaction) -> bool:
    """Yönetici izni veya administrator yetkisi var mı kontrol eder."""
    return interaction.user.guild_permissions.administrator

def moderator_mi(interaction: discord.Interaction) -> bool:
    perms = interaction.user.guild_permissions
    return perms.administrator or perms.manage_messages or perms.kick_members or perms.ban_members


@bot.tree.command(name="duyur", description="Duyurular kanalına @everyone duyurusu gönderir.")
@app_commands.describe(mesaj="Duyuru metni")
async def duyur(interaction: discord.Interaction, mesaj: str):
    if not yetkisiz(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    ch = discord.utils.get(interaction.guild.text_channels, name="🦊│duyurular") or \
         discord.utils.get(interaction.guild.text_channels, name="duyurular")
    if not ch:
        await interaction.response.send_message("❌ Duyurular kanalı bulunamadı.", ephemeral=True)
        return
    embed = discord.Embed(title="📢 Duyuru", description=mesaj, color=discord.Color.from_rgb(255, 165, 0))
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="Anipal Ekibi")
    await ch.send("@everyone", embed=embed)
    await interaction.response.send_message("✅ Duyuru gönderildi.", ephemeral=True)


@bot.tree.command(name="guncelle", description="Güncellemeler kanalına güncelleme mesajı gönderir.")
@app_commands.describe(mesaj="Güncelleme metni")
async def guncelle(interaction: discord.Interaction, mesaj: str):
    if not yetkisiz(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    ch = discord.utils.get(interaction.guild.text_channels, name="🦊│guncellemeler") or \
         discord.utils.get(interaction.guild.text_channels, name="guncellemeler")
    if not ch:
        await interaction.response.send_message("❌ Güncellemeler kanalı bulunamadı.", ephemeral=True)
        return
    embed = discord.Embed(title="🔄 Güncelleme", description=mesaj, color=discord.Color.from_rgb(88, 101, 242))
    embed.set_footer(text="Anipal Geliştirici Ekibi")
    await ch.send(embed=embed)
    await interaction.response.send_message("✅ Güncelleme gönderildi.", ephemeral=True)


@bot.tree.command(name="yayin", description="Üyeye yayın yetkisi verir veya alır.")
@app_commands.describe(uye="Yayın yetkisi verilecek üye")
async def yayin(interaction: discord.Interaction, uye: discord.Member):
    if not moderator_mi(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name="📡 Yayın Yetkisi")
    if not role:
        await interaction.response.send_message("❌ Yayın Yetkisi rolü bulunamadı.", ephemeral=True)
        return
    if role in uye.roles:
        await uye.remove_roles(role)
        await interaction.response.send_message(f"📡 {uye.mention} yayın yetkisi **kaldırıldı**.")
    else:
        await uye.add_roles(role)
        await interaction.response.send_message(f"📡 {uye.mention} artık sesli kanalda **yayın açabilir**!")


@bot.tree.command(name="rol", description="Üyeye rol verir.")
@app_commands.describe(uye="Rol verilecek üye", rol_adi="Verilecek rolün tam adı")
async def rol_ver(interaction: discord.Interaction, uye: discord.Member, rol_adi: str):
    if not moderator_mi(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name=rol_adi)
    if not role:
        await interaction.response.send_message(f"❌ `{rol_adi}` adında bir rol bulunamadı.", ephemeral=True)
        return
    await uye.add_roles(role)
    await interaction.response.send_message(f"✅ {uye.mention} → **{rol_adi}**")


@bot.tree.command(name="ban", description="Üyeyi sunucudan yasaklar.")
@app_commands.describe(uye="Yasaklanacak üye", sebep="Yasaklama sebebi")
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmedi."):
    if not moderator_mi(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    await uye.ban(reason=sebep)
    await interaction.response.send_message(f"🔨 {uye.mention} yasaklandı. Sebep: {sebep}")


@bot.tree.command(name="kick", description="Üyeyi sunucudan atar.")
@app_commands.describe(uye="Atılacak üye", sebep="Atma sebebi")
async def kick(interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmedi."):
    if not moderator_mi(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    await uye.kick(reason=sebep)
    await interaction.response.send_message(f"👢 {uye.mention} atıldı. Sebep: {sebep}")


@bot.tree.command(name="temizle", description="Kanaldan mesaj siler.")
@app_commands.describe(miktar="Silinecek mesaj sayısı (varsayılan: 10)")
async def temizle(interaction: discord.Interaction, miktar: int = 10):
    if not moderator_mi(interaction):
        await interaction.response.send_message("❌ Bu komutu kullanma yetkin yok.", ephemeral=True)
        return
    await interaction.response.send_message(f"🗑️ {miktar} mesaj siliniyor...", ephemeral=True)
    await interaction.channel.purge(limit=miktar)


@bot.tree.command(name="bilgi", description="Kullanıcı bilgisi ve level durumunu gösterir.")
@app_commands.describe(uye="Bilgisi görüntülenecek üye")
async def bilgi(interaction: discord.Interaction, uye: discord.Member = None):
    member = uye or interaction.user
    data   = load_levels()
    user   = get_user(data, member.id)
    embed  = discord.Embed(title=f"👤 {member.display_name}", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🏅 Level",     value=str(user["level"]),    inline=True)
    embed.add_field(name="✨ Toplam XP", value=str(user["total_xp"]), inline=True)
    embed.add_field(name="🎭 Roller", value=", ".join(r.name for r in member.roles[1:]) or "Yok", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="yardim", description="Tüm bot komutlarını listeler.")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 Anipal Bot Komutları", color=discord.Color.from_rgb(255, 100, 100))
    embed.add_field(name="/stats [@uye]",       value="Seviye istatistikleri",         inline=False)
    embed.add_field(name="/bilgi [@uye]",        value="Kullanıcı bilgisi",             inline=False)
    embed.add_field(name="/duyur [mesaj]",       value="Duyuru gönder *(Yönetici)*",    inline=False)
    embed.add_field(name="/guncelle [mesaj]",    value="Güncelleme gönder *(Yönetici)*",inline=False)
    embed.add_field(name="/yayin @kisi",         value="Yayın yetkisi ver/al *(Mod)*",  inline=False)
    embed.add_field(name="/rol @kisi [rol]",     value="Rol ver *(Mod)*",               inline=False)
    embed.add_field(name="/ban @kisi [sebep]",   value="Yasakla *(Mod)*",               inline=False)
    embed.add_field(name="/kick @kisi [sebep]",  value="At *(Mod)*",                    inline=False)
    embed.add_field(name="/temizle [sayi]",      value="Mesaj sil *(Mod)*",             inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
