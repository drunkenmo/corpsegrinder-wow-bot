import asyncio
import calendar
from datetime import datetime, timedelta, timezone
import json
import logging
import re
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands
from updater_core import mark_ready
from updater_discord import register as register_update_commands
from community_features import ROLE_STYLE, VERSION, visual_name, welcome_embed, announcement_intro_embed, news_embed, update_embed

logging.basicConfig(level=logging.INFO)
CONFIG = json.load(open("/data/options.json", encoding="utf-8"))
TOKEN = CONFIG.get("discord_token", "")
GUILD_ID = int(CONFIG.get("guild_id") or 0)
if not TOKEN or not GUILD_ID:
    raise RuntimeError("discord_token und guild_id in Home Assistant eintragen")

db = sqlite3.connect("/data/corpsegrinder.sqlite")
db.execute("CREATE TABLE IF NOT EXISTS characters (guild INTEGER, user INTEGER, name TEXT COLLATE NOCASE, klass TEXT, level INTEGER, beruf1 TEXT, beruf2 TEXT, PRIMARY KEY(guild,user,name))")
db.execute("CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY AUTOINCREMENT,guild INTEGER,owner INTEGER,kind TEXT,activity TEXT,when_text TEXT,channel INTEGER,message INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS signups (group_id INTEGER,user INTEGER,role TEXT,PRIMARY KEY(group_id,user))")
db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS planned_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, guild INTEGER NOT NULL, owner INTEGER NOT NULL, instance TEXT NOT NULL, start_utc INTEGER NOT NULL, display_time TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', channel INTEGER, message INTEGER, status TEXT NOT NULL DEFAULT 'open')")
db.execute("CREATE TABLE IF NOT EXISTS planned_signups (group_id INTEGER NOT NULL, user INTEGER NOT NULL, role TEXT NOT NULL, PRIMARY KEY(group_id,user))")
db.commit()

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
SERVER = discord.Object(id=GUILD_ID)

CLASSES = ("Krieger", "Schamane", "Druide", "Jäger", "Schurke", "Magier", "Priester", "Hexenmeister")
INTERESTS = ("PvE", "PvP")
TASKS = ("Tank", "Heiler", "DD")
NEWS = ("Dungeon-News", "Raid-News", "PvP-News")
ROLES = ("Community",) + INTERESTS + TASKS + NEWS + CLASSES
EMOJI = {
    "PvE": "⚔️", "PvP": "🏹", "Tank": "🛡️", "Heiler": "💚", "DD": "💥",
    "Dungeon-News": "🏰", "Raid-News": "🐉", "PvP-News": "📣",
    "Krieger": "⚔️", "Schamane": "🌩️", "Druide": "🌿", "Jäger": "🏹",
    "Schurke": "🗡️", "Magier": "✨", "Priester": "🌟", "Hexenmeister": "🔥",
}
STRUCTURE = {
    "🌋 WOW FOREVER | START": [
        ("willkommen", "text"), ("ankündigungen", "text"),
        ("rollenwahl", "text"), ("allgemein", "text")],
    "⚔️ WOW FOREVER | PVE": [
        ("pve-gruppensuche", "text"), ("dungeons", "text"),
        ("raids-und-termine", "text"), ("pve-guides", "text"),
        ("PvE – Leveln", "voice"), ("PvE – Dungeon", "voice"),
        ("PvE – Raid", "voice"), ("➕ PvE-Gruppe erstellen", "voice")],
    "🏹 WOW FOREVER | PVP": [
        ("pvp-gruppensuche", "text"), ("schlachtfelder", "text"),
        ("welt-pvp", "text"), ("pvp-guides", "text"),
        ("PvP – Gruppe", "voice"), ("➕ PvP-Gruppe erstellen", "voice")],
    "🔨 WOW FOREVER | CHARAKTERE": [
        ("charaktere-und-berufe", "text"), ("handel-und-crafting", "text"),
        ("screenshots", "text")],
}

def role(guild, name):
    return (discord.utils.get(guild.roles, name=visual_name(name))
            or discord.utils.get(guild.roles, name=name))

def channel(guild, name):
    return discord.utils.get(guild.channels, name=name)

def setting(key):
    item = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return item[0] if item else None

def save_setting(key, value):
    db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value)))
    db.commit()

async def answer(i, content):
    if i.response.is_done():
        await i.followup.send(content, ephemeral=True)
    else:
        await i.response.send_message(content, ephemeral=True)

def allowed(i):
    return i.guild is not None and i.guild.id == GUILD_ID

def admin(i):
    return allowed(i) and i.user.guild_permissions.administrator

def role_panel():
    embed = discord.Embed(
        title="🩸 CORPSEGRINDER | Deine Rollen",
        description="**Für die Horde!** Community und Gilde spielen gemeinsam. Wähle unabhängig PvE/PvP, Gruppenaufgaben, Klassen und Benachrichtigungen.",
        color=discord.Color.dark_red())
    embed.add_field(name="⚔️ Spielbereiche", value="PvE und PvP können gleichzeitig aktiv sein.", inline=False)
    embed.add_field(name="🛡️ Gruppenaufgaben", value="Tank, Heiler und DD – mehrere möglich.", inline=False)
    embed.add_field(name="🌿 Klassen", value="Wähle deine Klassen über das Menü.", inline=False)
    embed.add_field(name="🔔 Benachrichtigungen", value="Lass dich nur bei gewünschten Themen ansprechen.", inline=False)
    embed.set_footer(text="Erneut anklicken = Rolle entfernen · Meine Auswahl = Übersicht")
    return embed

async def toggle(i, names):
    if not allowed(i):
        return await answer(i, "Dieses Menü ist nur für Corpsegrinder.")
    add, remove, missing = [], [], []
    for name in names:
        target = role(i.guild, name)
        if target is None:
            missing.append(name)
        elif target in i.user.roles:
            remove.append(target)
        else:
            add.append(target)
    try:
        if add:
            await i.user.add_roles(*add, reason="Corpsegrinder Selbstwahl")
        if remove:
            await i.user.remove_roles(*remove, reason="Corpsegrinder Selbstwahl")
    except discord.Forbidden:
        return await answer(i, "Der Bot darf diese Rollen nicht vergeben. Bitte Rollenposition und Rollen verwalten prüfen.")
    except discord.HTTPException:
        logging.exception("Rollenwahl")
        return await answer(i, "Discord hat die Rollenänderung nicht angenommen.")
    output = []
    if add:
        output.append("Hinzugefügt: " + ", ".join(r.name for r in add))
    if remove:
        output.append("Entfernt: " + ", ".join(r.name for r in remove))
    if missing:
        output.append("Nicht gefunden: " + ", ".join(missing))
    await answer(i, "\n".join(output) or "Keine Änderung.")

def own_roles(member):
    names = {r.name for r in member.roles}
    # Namen mit Emoji nach der Rollenumstellung ebenfalls korrekt erkennen.
    names |= {name for name in ROLES if visual_name(name) in names}
    blocks = []
    for title, values in (("Spielbereiche", INTERESTS), ("Gruppenaufgaben", TASKS),
                          ("Klassen", CLASSES), ("News", NEWS)):
        chosen = [EMOJI[x] + " " + x for x in values if x in names]
        blocks.append("**" + title + ":** " + (", ".join(chosen) if chosen else "–"))
    return "\n".join(blocks)

class ToggleSelect(discord.ui.Select):
    def __init__(self, values, description, custom_id, row):
        super().__init__(
            placeholder=description,
            custom_id=custom_id,
            options=[discord.SelectOption(label=name, emoji=EMOJI[name]) for name in values],
            min_values=1, max_values=len(values), row=row)
    async def callback(self, interaction):
        await toggle(interaction, self.values)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for label, row, style in (("PvE", 0, discord.ButtonStyle.primary),
                                  ("PvP", 0, discord.ButtonStyle.primary),
                                  ("Tank", 1, discord.ButtonStyle.secondary),
                                  ("Heiler", 1, discord.ButtonStyle.secondary),
                                  ("DD", 1, discord.ButtonStyle.secondary)):
            button = discord.ui.Button(
                label=label, emoji=EMOJI[label], row=row, style=style,
                custom_id="corpse_toggle_v104_" + label)
            async def handle(i, name=label):
                await toggle(i, [name])
            button.callback = handle
            self.add_item(button)
        self.add_item(ToggleSelect(CLASSES, "🌿 Klassen auswählen", "corpse_classes_v104", 2))
        self.add_item(ToggleSelect(NEWS, "🔔 Benachrichtigungen", "corpse_news_v104", 3))
        button = discord.ui.Button(label="Meine Auswahl", emoji="📋",
            style=discord.ButtonStyle.success, row=4, custom_id="corpse_myroles_v104")
        async def overview(i):
            if allowed(i):
                await answer(i, "**Deine Rollen**\n" + own_roles(i.user))
        button.callback = overview
        self.add_item(button)

class GroupView(discord.ui.View):
    def __init__(self, group_id):
        super().__init__(timeout=None)
        for label in ("Tank", "Heiler", "DD", "Dabei"):
            button = discord.ui.Button(label=label, custom_id="cg_group_" + str(group_id) + "_" + label)
            async def signup(i, value=label):
                if not allowed(i):
                    return
                db.execute("INSERT OR REPLACE INTO signups VALUES (?,?,?)", (group_id, i.user.id, value))
                db.commit()
                await answer(i, "Für Gruppe #" + str(group_id) + " als " + value + " angemeldet.")
            button.callback = signup
            self.add_item(button)

async def publish_panel(guild):
    target = channel(guild, "rollenwahl")
    if not isinstance(target, discord.TextChannel):
        raise RuntimeError("Kanal #rollenwahl fehlt")
    old_id = setting("role_post")
    if old_id:
        try:
            message = await target.fetch_message(int(old_id))
            if message.author.id == bot.user.id:
                await message.edit(content=None, embed=role_panel(), view=RoleView())
                return "Bestehendes Rollenmenü aktualisiert."
        except (discord.NotFound, ValueError):
            pass
    message = await target.send(embed=role_panel(), view=RoleView())
    save_setting("role_post", message.id)
    return "Neues Rollenmenü veröffentlicht."

@bot.event
async def on_ready():
    logging.info("Angemeldet als %s", bot.user)
    # Bei erneuter Verbindung erneut verwaiste temporäre Räume prüfen.
    background(cleanup_leftover_voice_channels())
    if getattr(bot, "initialized", False):
        return
    bot.add_view(RoleView())
    for (group_id,) in db.execute("SELECT id FROM groups WHERE guild=?", (GUILD_ID,)).fetchall():
        bot.add_view(GroupView(group_id))
    # Alle noch aktiven Termin-Schaltflächen überleben Neustarts.
    for (group_id, message_id) in db.execute(
            "SELECT id,message FROM planned_groups WHERE guild=? AND status='open' AND start_utc > ? AND message IS NOT NULL",
            (GUILD_ID, int(datetime.now(timezone.utc).timestamp()) - 3600)).fetchall():
        bot.add_view(PlannedView(group_id), message_id=message_id)
    await bot.tree.sync(guild=SERVER)
    bot.initialized = True
    mark_ready()
    background(apply_all_wow_role_styles_once())
    await post_version_news_once()

@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    community = role(member.guild, "Community")
    if community:
        try:
            await member.add_roles(community)
        except discord.Forbidden:
            logging.warning("Community-Rolle konnte nicht vergeben werden")
    greeting = channel(member.guild, "willkommen")
    if isinstance(greeting, discord.TextChannel):
        await greeting.send("⚔️ Willkommen bei **Corpsegrinder**, " + member.mention + "! Für die Horde! Wähle deine Rollen in #rollenwahl.",
                            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))

# Nur vom Bot erzeugte Sprachkanäle werden in der Datenbank als temporär markiert.
# Weder feste WoW-Räume noch Sprachkanäle anderer Spiele werden automatisch gelöscht.
_background_tasks = set()


def background(coroutine):
    task = asyncio.create_task(coroutine)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def forget_temp_channel(channel_id):
    db.execute("DELETE FROM settings WHERE key=?", ("temp_" + str(channel_id),))
    db.commit()


async def delete_temp_if_empty(channel_id, delay=3):
    await asyncio.sleep(delay)  # Discords Voice-State-Cache und Umzüge auslaufen lassen
    if setting("temp_" + str(channel_id)) != "1":
        return
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    target = guild.get_channel(channel_id)
    if target is None:
        forget_temp_channel(channel_id)
        return
    if not isinstance(target, discord.VoiceChannel):
        logging.warning("Markierter temporärer Kanal %s ist kein VoiceChannel", channel_id)
        return
    if target.members:
        return
    try:
        await target.delete(reason="Corpsegrinder: temporärer Sprachkanal ist leer")
        forget_temp_channel(channel_id)
        logging.info("Leeren temporären Sprachkanal %s gelöscht", channel_id)
    except discord.NotFound:
        forget_temp_channel(channel_id)
    except discord.Forbidden:
        logging.warning("Konnte Sprachkanal %s nicht löschen: Kanäle verwalten fehlt", channel_id)
    except discord.HTTPException:
        logging.exception("Fehler beim Löschen des temporären Sprachkanals %s", channel_id)


async def cleanup_leftover_voice_channels():
    # Auch nach einem Neustart bleiben Kanal-IDs gespeichert und können bereinigt werden.
    rows = db.execute(
        "SELECT key FROM settings WHERE key LIKE 'temp_%' AND value='1'"
    ).fetchall()
    for (key,) in rows:
        try:
            channel_id = int(key.removeprefix("temp_"))
        except ValueError:
            continue
        background(delete_temp_if_empty(channel_id, delay=12))


@bot.event
async def on_voice_state_update(member, before, after):
    if member.guild.id != GUILD_ID:
        return
    if after.channel is not None and after.channel != before.channel and after.channel.name in (
            "➕ PvE-Gruppe erstellen", "➕ PvP-Gruppe erstellen"):
        kind = "PvE" if "PvE" in after.channel.name else "PvP"
        parent = after.channel.category
        if parent is None:
            logging.warning("Gruppenerstellungskanal hat keine Kategorie")
            return
        new_channel = None
        try:
            new_channel = await parent.create_voice_channel(
                (kind + " | " + member.display_name)[:90],
                user_limit=5 if kind == "PvE" else 10,
                reason="Corpsegrinder: temporäre " + kind + "-Gruppe")
            save_setting("temp_" + str(new_channel.id), "1")
            await member.move_to(new_channel, reason="Temporäre " + kind + "-Gruppe")
        except discord.HTTPException:
            logging.exception(
                "Temporären Sprachkanal nicht erstellt/Spieler nicht verschoben. "
                "Berechtigungen 'Kanäle verwalten' und 'Mitglieder verschieben' prüfen.")
            # Ein erzeugter Raum ohne Spieler darf nicht liegenbleiben.
            if new_channel is not None:
                background(delete_temp_if_empty(new_channel.id, delay=5))
    if before.channel is not None and setting("temp_" + str(before.channel.id)) == "1":
        background(delete_temp_if_empty(before.channel.id, delay=3))


@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild.id == GUILD_ID and setting("temp_" + str(channel.id)) == "1":
        forget_temp_channel(channel.id)

@bot.tree.command(name="einrichtung_vorschau", description="Noch fehlende WoW-Rollen und Kanäle", guild=SERVER)
async def preview(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    missing_roles = sum(role(i.guild, name) is None for name in ROLES)
    missing_categories = sum(discord.utils.get(i.guild.categories, name=name) is None for name in STRUCTURE)
    missing_channels = sum(channel(i.guild, name) is None for items in STRUCTURE.values() for name, kind in items)
    await answer(i, f"Neue Rollen: {missing_roles}\nNeue Kategorien: {missing_categories}\nNeue Kanäle: {missing_channels}\n\nBestehende Objekte werden nicht gelöscht.")

@bot.tree.command(name="einrichtung_start", description="Fehlende WoW-Bereiche anlegen (Admin)", guild=SERVER)
async def setup(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    await i.response.defer(ephemeral=True, thinking=True)
    current = "Start"
    try:
        for name in ROLES:
            current = "Rolle " + name
            if not role(i.guild, name):
                await i.guild.create_role(name=visual_name(name), reason="Corpsegrinder Einrichtung")
        for name, items in STRUCTURE.items():
            current = "Kategorie " + name
            category = discord.utils.get(i.guild.categories, name=name)
            if category is None:
                category = await i.guild.create_category(name, reason="Corpsegrinder Einrichtung")
            for channel_name, kind in items:
                if channel(i.guild, channel_name) is not None:
                    continue
                current = "Kanal " + channel_name
                if kind == "voice":
                    await category.create_voice_channel(channel_name)
                else:
                    await category.create_text_channel(channel_name)
        if not setting("role_post"):
            current = "Rollenmenü"
            await publish_panel(i.guild)
        await i.followup.send("Einrichtung abgeschlossen. Andere Kanäle wurden nicht verändert.", ephemeral=True)
    except discord.HTTPException as exc:
        logging.exception("Einrichtung: %s", current)
        await i.followup.send(f"Fehler bei {current}: Discord-Code {exc.code}. Bitte nicht mehrfach ausführen.", ephemeral=True)

@bot.tree.command(name="rollenmenue_aktualisieren", description="Rollenmenü erneuern (Admin)", guild=SERVER)
async def update_roles(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    await i.response.defer(ephemeral=True, thinking=True)
    try:
        response = await publish_panel(i.guild)
        await i.followup.send(response + " Bestehende Rollen bleiben erhalten.", ephemeral=True)
    except discord.HTTPException:
        logging.exception("Rollenmenü")
        await i.followup.send("Fehler beim Aktualisieren. Bot-Berechtigungen in #rollenwahl prüfen.", ephemeral=True)

@bot.tree.command(name="meine_rollen", description="Deine Rollen anzeigen", guild=SERVER)
async def my_roles(i: discord.Interaction):
    await answer(i, own_roles(i.user))

@bot.tree.command(name="charakter", description="Charakter anlegen oder aktualisieren", guild=SERVER)
@app_commands.describe(name="Charaktername", klasse="Klasse", level="Stufe", beruf1="Beruf 1", beruf2="Beruf 2")
@app_commands.choices(klasse=[app_commands.Choice(name=name, value=name) for name in CLASSES])
async def character(i: discord.Interaction, name: str, klasse: app_commands.Choice[str],
                    level: app_commands.Range[int, 1, 80], beruf1: str = "", beruf2: str = ""):
    if not allowed(i):
        return
    db.execute("INSERT OR REPLACE INTO characters VALUES (?,?,?,?,?,?,?)",
               (GUILD_ID, i.user.id, name[:40], klasse.value, level, beruf1[:50], beruf2[:50]))
    db.commit()
    await answer(i, "Charakter " + name[:40] + " gespeichert.")

@bot.tree.command(name="meine_charaktere", description="Deine Charaktere anzeigen", guild=SERVER)
async def my_characters(i: discord.Interaction):
    rows = db.execute("SELECT name,klass,level,beruf1,beruf2 FROM characters WHERE guild=? AND user=?",
                      (GUILD_ID, i.user.id)).fetchall()
    await answer(i, "\n".join(f"**{n}** · {k} · Stufe {level} · {b1 or '–'} / {b2 or '–'}"
                             for n, k, level, b1, b2 in rows) or "Noch keine Charaktere.")

@bot.tree.command(name="charakter_loeschen", description="Eigenen Charakter löschen", guild=SERVER)
async def delete_character(i: discord.Interaction, name: str):
    cursor = db.execute("DELETE FROM characters WHERE guild=? AND user=? AND name=?",
                        (GUILD_ID, i.user.id, name))
    db.commit()
    await answer(i, "Charakter gelöscht." if cursor.rowcount else "Charakter nicht gefunden.")

@bot.tree.command(name="gruppe_erstellen", description="PvE/PvP-Gruppe erstellen", guild=SERVER)
@app_commands.choices(art=[app_commands.Choice(name=x, value=x) for x in INTERESTS])
async def create_group(i: discord.Interaction, art: app_commands.Choice[str],
                       aktivitaet: str, zeit: str):
    target = channel(i.guild, "pve-gruppensuche" if art.value == "PvE" else "pvp-gruppensuche")
    if not isinstance(target, discord.TextChannel):
        return await answer(i, "Bitte zuerst /einrichtung_start ausführen.")
    cursor = db.execute("INSERT INTO groups(guild,owner,kind,activity,when_text) VALUES (?,?,?,?,?)",
                        (GUILD_ID, i.user.id, art.value, aktivitaet[:100], zeit[:100]))
    group_id = cursor.lastrowid
    db.commit()
    message = await target.send(
        "**" + art.value + "-Gruppe #" + str(group_id) + ": " +
        discord.utils.escape_markdown(aktivitaet[:100]) + "**\nZeit: " +
        discord.utils.escape_markdown(zeit[:100]) + "\nErstellt von " + i.user.mention,
        view=GroupView(group_id),
        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
    db.execute("UPDATE groups SET channel=?,message=? WHERE id=?", (target.id, message.id, group_id))
    db.commit()
    await answer(i, "Gruppe #" + str(group_id) + " erstellt in " + target.mention)

@bot.tree.command(name="gruppe_abmelden", description="Aus Gruppe austragen", guild=SERVER)
async def leave_group(i: discord.Interaction, gruppen_id: int):
    db.execute("DELETE FROM signups WHERE group_id=? AND user=?", (gruppen_id, i.user.id))
    db.commit()
    await answer(i, "Anmeldung entfernt, falls vorhanden.")

@bot.tree.command(name="gruppe_anzeigen", description="Anmeldungen anzeigen", guild=SERVER)
async def show_group(i: discord.Interaction, gruppen_id: int):
    result = db.execute("SELECT user,role FROM signups WHERE group_id=?", (gruppen_id,)).fetchall()
    await answer(i, "\n".join("<@" + str(user) + "> – " + r for user, r in result) or "Noch keine Anmeldungen.")


async def post_version_news_once():
    """Postet wichtige Bot-Neuerungen einmal je Version; kein WoW-Nachrichten-Scraping."""
    key = "news_posted_" + VERSION
    if setting(key):
        return
    guild = bot.get_guild(GUILD_ID)
    target = channel(guild, "ankündigungen") if guild else None
    if not isinstance(target, discord.TextChannel):
        return
    try:
        async for msg in target.history(limit=40):
            if msg.author.id == bot.user.id and any(
                "Bot-Version " + VERSION in (item.footer.text or "") for item in msg.embeds
            ):
                save_setting(key, str(msg.id))
                return
        msg = await target.send(
            embed=update_embed(),
            allowed_mentions=discord.AllowedMentions.none())
        save_setting(key, str(msg.id))
    except discord.HTTPException:
        logging.exception("Automatische Update-Nachricht fehlgeschlagen")


async def publish_info(channel_obj, storage_key, marker, embed):
    """Intro anlegen oder wiederverwenden; mehrfacher Befehl erzeugt keine Textflut."""
    existing = None
    msg_id = setting(storage_key)
    if msg_id:
        try:
            existing = await channel_obj.fetch_message(int(msg_id))
            if existing.author.id != bot.user.id:
                existing = None
        except (discord.NotFound, ValueError):
            existing = None
    if existing is None:
        async for candidate in channel_obj.history(limit=75):
            if candidate.author.id == bot.user.id and any(
                marker in (item.footer.text or "") for item in candidate.embeds
            ):
                existing = candidate
                break
    if existing is None:
        existing = await channel_obj.send(
            embed=embed, allowed_mentions=discord.AllowedMentions.none())
    else:
        await existing.edit(embed=embed)
    save_setting(storage_key, existing.id)
    pin_note = ""
    if not existing.pinned:
        try:
            await existing.pin(reason="Corpsegrinder Startinformation")
        except discord.Forbidden:
            pin_note = " (Anheften erfordert für den Bot 'Nachrichten verwalten'.)"
    return existing, pin_note


@bot.tree.command(name="rollen_design_vorschau", description="Vorschau der bunten Rollen und Icons (Admin)", guild=SERVER)
async def role_design_preview(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    changes = []
    collisions = []
    for plain_name, (styled_name, colour, emoji) in ROLE_STYLE.items():
        old = discord.utils.get(i.guild.roles, name=plain_name)
        styled = discord.utils.get(i.guild.roles, name=styled_name)
        if old and styled:
            collisions.append(plain_name)
        elif old:
            changes.append(plain_name + " → " + styled_name)
    icons = "möglich" if "ROLE_ICONS" in i.guild.features else "nicht freigeschaltet (Server-Boost-Level 2)"
    await answer(i,
        "**Vorschau – keine Änderung**\n"
        + ("\n".join(changes) if changes else "Keine umzubenennenden Rollen.")
        + ("\n**Doppelte Namen bitte prüfen:** " + ", ".join(collisions) if collisions else "")
        + "\n**Discord-Rollen-Icons:** " + icons
        + "\n\nMit /rollen_design_anwenden bestätigst du das Umbenennen und Färben dieser vorhandenen Rollen.")


async def style_all_wow_roles(guild):
    """Gibt bestehenden WoW-Rollen Emoji-Namen und Farben; nie Admin-Rollen anfassen."""
    changed, skipped = [], []
    bot_member = guild.me or guild.get_member(bot.user.id)
    if bot_member is None:
        return changed, ["Bot-Mitglied konnte nicht ermittelt werden"]
    supports_icons = "ROLE_ICONS" in guild.features
    for plain_name, (styled_name, colour, emoji) in ROLE_STYLE.items():
        old = discord.utils.get(guild.roles, name=plain_name)
        styled = discord.utils.get(guild.roles, name=styled_name)
        if old is not None and styled is not None:
            skipped.append(plain_name + " (zwei Rollen mit gleichem Zweck)")
            continue
        target = old or styled
        if target is None:
            # Fehlende WoW-Rollen werden ergänzt, nicht Rollennamen anderer Spiele angetastet.
            try:
                target = await guild.create_role(
                    name=styled_name,
                    colour=discord.Colour(colour),
                    reason="Corpsegrinder 1.0.8: fehlende WoW-Rolle")
            except discord.HTTPException:
                skipped.append(plain_name + " (Rolle fehlt/Erstellen nicht erlaubt)")
                continue
        if target.managed or target >= bot_member.top_role:
            skipped.append(plain_name + " (durch Bot nicht bearbeitbar)")
            continue
        kwargs = {
            "name": styled_name,
            "colour": discord.Colour(colour),
            "reason": "Corpsegrinder 1.0.8: WoW-Rollendesign",
        }
        if supports_icons:
            kwargs["display_icon"] = emoji
        try:
            await target.edit(**kwargs)
            changed.append(styled_name)
        except discord.HTTPException:
            if supports_icons:
                # Discord-Icons sind je nach Boost-Level und Emoji-Unterstützung begrenzt.
                kwargs.pop("display_icon", None)
                try:
                    await target.edit(**kwargs)
                    changed.append(styled_name + " (ohne Rollen-Icon)")
                    continue
                except discord.HTTPException:
                    pass
            skipped.append(plain_name + " (Discord-Berechtigung/Fehler)")
    return changed, skipped


async def apply_all_wow_role_styles_once():
    guild = bot.get_guild(GUILD_ID)
    if guild is None or setting("all_wow_roles_styled_v108") == "1":
        return
    try:
        changed, skipped = await style_all_wow_roles(guild)
        logging.info("WoW-Rollendesign: %s aktualisiert, %s übersprungen: %s",
                     len(changed), len(skipped), skipped)
        if not skipped:
            save_setting("all_wow_roles_styled_v108", "1")
    except Exception:
        logging.exception("Automatisches WoW-Rollendesign gescheitert")


@bot.tree.command(name="rollen_design_anwenden", description="Alle WoW-Rollen einfärben und umbenennen (Admin)", guild=SERVER)
async def role_design_apply(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    await i.response.defer(ephemeral=True, thinking=True)
    changed, skipped = await style_all_wow_roles(i.guild)
    if not skipped:
        save_setting("all_wow_roles_styled_v108", "1")
    await i.followup.send(
        "**WoW-Rollen aktualisiert:** " + str(len(changed)) +
        "\n" + (", ".join(changed) if changed else "Keine Änderung nötig") +
        ("\n**Übersprungen:** " + ", ".join(skipped) if skipped else "") +
        "\nVorhandene Mitglieds-Zuweisungen bleiben erhalten.",
        ephemeral=True)


@bot.tree.command(name="startkanaele_einrichten", description="Willkommen/Ankündigungen mit Infotexten füllen (Admin)", guild=SERVER)
async def start_channels(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    await i.response.defer(ephemeral=True, thinking=True)
    findings = []
    for channel_name, key, marker, embed in (
        ("willkommen", "welcome_post", "corpsegrinder:welcome", welcome_embed()),
        ("ankündigungen", "announcement_intro_post", "corpsegrinder:news-intro",
         announcement_intro_embed()),
    ):
        target = channel(i.guild, channel_name)
        if not isinstance(target, discord.TextChannel):
            findings.append(channel_name + ": Kanal nicht gefunden")
            continue
        try:
            message, note = await publish_info(target, key, marker, embed)
            findings.append("#" + channel_name + ": Nachricht eingerichtet" + note)
        except discord.HTTPException:
            logging.exception("Startkanal einrichten: %s", channel_name)
            findings.append("#" + channel_name + ": Berechtigungsfehler")
    await i.followup.send("\n".join(findings), ephemeral=True)


@bot.tree.command(name="ankuendigung", description="Schöne Nachricht in #ankündigungen veröffentlichen (Admin)", guild=SERVER)
@app_commands.describe(titel="Überschrift", text="Inhalt der Ankündigung")
async def admin_announcement(i: discord.Interaction, titel: str, text: str):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    target = channel(i.guild, "ankündigungen")
    if not isinstance(target, discord.TextChannel):
        return await answer(i, "Kanal #ankündigungen nicht gefunden.")
    try:
        message = await target.send(
            embed=news_embed(titel, text, i.user),
            allowed_mentions=discord.AllowedMentions.none())
        await answer(i, "Ankündigung veröffentlicht: " + message.jump_url)
    except discord.HTTPException:
        logging.exception("Ankündigung fehlgeschlagen")
        await answer(i, "Die Ankündigung konnte nicht veröffentlicht werden.")


@bot.tree.command(name="ankuendigungen_schreibschutz", description="Nur Admins/Bot dürfen dort posten (Admin)", guild=SERVER)
async def announcement_lock(i: discord.Interaction):
    if not admin(i):
        return await answer(i, "Nur Administratoren.")
    target = channel(i.guild, "ankündigungen")
    if not isinstance(target, discord.TextChannel):
        return await answer(i, "Kanal #ankündigungen nicht gefunden.")
    try:
        await target.set_permissions(
            i.guild.default_role, send_messages=False,
            reason="Ankündigungen nur für die Serverleitung")
        await target.set_permissions(
            i.guild.me, view_channel=True, send_messages=True,
            reason="Bot darf weiterhin Mitteilungen veröffentlichen")
        await answer(i, "#ankündigungen ist für normale Mitglieder jetzt schreibgeschützt. Admins und der Bot können weiterhin schreiben.")
    except discord.HTTPException:
        await answer(i, "Kanalberechtigungen konnten nicht geändert werden.")


register_update_commands(bot, SERVER, admin)

bot.run(TOKEN, log_handler=None)
