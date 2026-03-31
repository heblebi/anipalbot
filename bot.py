"""
Anipal Discord Botu — Sürekli çalışan ana bot.
Kurulum için önce setup_server.py'yi çalıştırın.
"""

import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members         = True
intents.message_content = True
intents.reactions       = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ── Reaksiyon rol haritaları ──────────────────────────────────────────────────
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

ALL_EMOJI_ROLE_MAP: dict[str, str] = {
    **CINSIYET_EMOJILER,
    **RENK_EMOJILER,
    **UNVAN_EMOJILER,
}

# Cinsiyet ve renk gruplarında aynı anda yalnızca 1 rol olabilir
EXCLUSIVE_GROUPS = [
    list(CINSIYET_EMOJILER.values()),
    list(RENK_EMOJILER.values()),
]

# Setup script tarafından kaydedilen mesaj ID'leri
REACTION_MSG_IDS: set[int] = set()

def load_reaction_ids():
    try:
        with open("reaction_roles.json", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.values())
    except FileNotFoundError:
        print("⚠️  reaction_roles.json bulunamadı. Önce setup_server.py çalıştır.")
        return set()


# ══════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    global REACTION_MSG_IDS
    REACTION_MSG_IDS = load_reaction_ids()
    print(f"✅ {bot.user} çevrimiçi! ({len(REACTION_MSG_IDS)} rol mesajı yüklendi)")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🎌 Anipal",
        )
    )


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    # Varsayılan rol yok — kuralları okuyana kadar bekliyorlar
    hos_geldin = discord.utils.get(guild.text_channels, name="hos-geldin")
    if not hos_geldin:
        return

    embed = discord.Embed(
        title=f"🎉 Hoş Geldin, {member.display_name}!",
        description=(
            f"**Anipal**'a hoş geldin {member.mention}! 🎌\n\n"
            "📜 Önce kuralları oku → <#kurallar>\n"
            "🎭 Rolünü seç → <#rol-al>\n"
            "🙋 Kendini tanıt → <#kendini-tanit>"
        ),
        color=discord.Color.from_rgb(255, 100, 100),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Sunucuda şu an {guild.member_count} üye var!")
    await hos_geldin.send(embed=embed)


# ── Reaksiyon eklendi ─────────────────────────────────────────────────────────
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id not in REACTION_MSG_IDS:
        return
    if payload.user_id == bot.user.id:
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

    # Aynı grubun eski rolünü kaldır (exclusive gruplar)
    for group in EXCLUSIVE_GROUPS:
        if role_name in group:
            for other_name in group:
                if other_name != role_name:
                    other_role = discord.utils.get(guild.roles, name=other_name)
                    if other_role and other_role in member.roles:
                        await member.remove_roles(other_role)

    await member.add_roles(role)
    print(f"  ➕ {member.display_name} → {role_name}")


# ── Reaksiyon kaldırıldı ──────────────────────────────────────────────────────
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
        print(f"  ➖ {member.display_name} → {role_name} kaldırıldı")


# ══════════════════════════════════════════════════════════════════════════════
#  KOMUTLAR
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="duyur")
@commands.has_role("👑 Anipal Yöneticisi")
async def duyur(ctx, *, mesaj: str):
    """Duyurular kanalına @everyone duyurusu gönderir."""
    ch = discord.utils.get(ctx.guild.text_channels, name="duyurular")
    if not ch:
        await ctx.send("❌ #duyurular kanalı bulunamadı.")
        return
    embed = discord.Embed(title="📢 Duyuru", description=mesaj, color=discord.Color.from_rgb(255, 165, 0))
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="Anipal Ekibi")
    await ch.send("@everyone", embed=embed)
    await ctx.message.delete()


@bot.command(name="guncelle")
@commands.has_role("👑 Anipal Yöneticisi")
async def guncelle(ctx, *, mesaj: str):
    """Güncellemeler kanalına güncelleme mesajı gönderir."""
    ch = discord.utils.get(ctx.guild.text_channels, name="guncellemeler")
    if not ch:
        await ctx.send("❌ #guncellemeler kanalı bulunamadı.")
        return
    embed = discord.Embed(title="🔄 Güncelleme", description=mesaj, color=discord.Color.from_rgb(88, 101, 242))
    embed.set_footer(text="Anipal Geliştirici Ekibi")
    await ch.send(embed=embed)
    await ctx.message.delete()


@bot.command(name="yayin")
@commands.has_permissions(manage_roles=True)
async def yayin_ver(ctx, member: discord.Member):
    """Üyeye Yayın Yetkisi rolü verir. Kullanım: !yayin @kullanıcı"""
    role = discord.utils.get(ctx.guild.roles, name="📡 Yayın Yetkisi")
    if not role:
        await ctx.send("❌ Yayın Yetkisi rolü bulunamadı.")
        return
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"📡 {member.mention} yayın yetkisi **kaldırıldı**.")
    else:
        await member.add_roles(role)
        await ctx.send(f"📡 {member.mention} artık sesli kanallarda **yayın açabilir**.")


@bot.command(name="rol")
@commands.has_permissions(manage_roles=True)
async def rol_ver(ctx, member: discord.Member, *, rol_adi: str):
    """Üyeye rol verir. Kullanım: !rol @kullanıcı Rol Adı"""
    role = discord.utils.get(ctx.guild.roles, name=rol_adi)
    if not role:
        await ctx.send(f"❌ `{rol_adi}` adında bir rol bulunamadı.")
        return
    await member.add_roles(role)
    await ctx.send(f"✅ {member.mention} → **{rol_adi}**")


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi."):
    await member.ban(reason=sebep)
    await ctx.send(f"🔨 {member.mention} yasaklandı. Sebep: {sebep}")


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi."):
    await member.kick(reason=sebep)
    await ctx.send(f"👢 {member.mention} atıldı. Sebep: {sebep}")


@bot.command(name="temizle")
@commands.has_permissions(manage_messages=True)
async def temizle(ctx, miktar: int = 10):
    """Kanaldan mesaj siler. Kullanım: !temizle 20"""
    await ctx.channel.purge(limit=miktar + 1)
    msg = await ctx.send(f"🗑️ {miktar} mesaj silindi.")
    await msg.delete(delay=3)


@bot.command(name="bilgi")
async def bilgi(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed  = discord.Embed(title=f"👤 {member.display_name}", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Kullanıcı", value=str(member), inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(
        name="Katılış",
        value=member.joined_at.strftime("%d.%m.%Y") if member.joined_at else "?",
        inline=True,
    )
    embed.add_field(
        name="Roller",
        value=", ".join(r.name for r in member.roles[1:]) or "Yok",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="yardim")
async def yardim(ctx):
    embed = discord.Embed(title="🤖 Anipal Bot Komutları", color=discord.Color.from_rgb(255, 100, 100))
    embed.add_field(name="!duyur [mesaj]",     value="Duyuru gönderir *(Yönetici)*",       inline=False)
    embed.add_field(name="!guncelle [mesaj]",  value="Güncelleme gönderir *(Yönetici)*",   inline=False)
    embed.add_field(name="!yayin @kişi",       value="Yayın yetkisi verir/alır *(Mod)*",   inline=False)
    embed.add_field(name="!rol @kişi [rol]",   value="Rol verir *(Mod)*",                  inline=False)
    embed.add_field(name="!ban @kişi [sebep]", value="Yasaklar *(Mod)*",                   inline=False)
    embed.add_field(name="!kick @kişi [sebep]", value="Atar *(Mod)*",                      inline=False)
    embed.add_field(name="!temizle [sayı]",    value="Mesaj siler *(Mod)*",                inline=False)
    embed.add_field(name="!bilgi [@kişi]",     value="Kullanıcı bilgisi *(Herkes)*",       inline=False)
    await ctx.send(embed=embed)


# ── Hata yönetimi ─────────────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Bu komutu kullanma yetkin yok.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Yeterli yetkin bulunmuyor.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Kullanıcı bulunamadı.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ Hata: {error}")


if __name__ == "__main__":
    bot.run(TOKEN)
