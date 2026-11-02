import asyncio
import calendar
from datetime import datetime, timedelta, timezone
from collections import defaultdict
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
db.execute("CREATE TABLE IF NOT EXISTS level_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, guild INTEGER NOT NULL, owner INTEGER NOT NULL, area TEXT NOT NULL, min_level INTEGER NOT NULL, max_level INTEGER NOT NULL, start_utc INTEGER NOT NULL, display_time TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', channel INTEGER, message INTEGER, status TEXT NOT NULL DEFAULT 'open')")
db.execute("CREATE TABLE IF NOT EXISTS level_signups (group_id INTEGER NOT NULL, user INTEGER NOT NULL, PRIMARY KEY(group_id,user))")
# Die Planer-Datenbanken behalten auch nach der Löschung der Discord-Karten ihr Archiv.
db.execute("CREATE TABLE IF NOT EXISTS event_meta (kind TEXT NOT NULL, group_id INTEGER NOT NULL, reminder_sent INTEGER NOT NULL DEFAULT 0, full_prev INTEGER NOT NULL DEFAULT 0, voice_id INTEGER, voice_seen INTEGER NOT NULL DEFAULT 0, voice_created INTEGER NOT NULL DEFAULT 0, expired_at INTEGER, archived_at INTEGER, PRIMARY KEY(kind,group_id))")
db.execute("CREATE TABLE IF NOT EXISTS notification_preferences (user_id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1)")
db.execute("CREATE TABLE IF NOT EXISTS event_reminder_deliveries (kind TEXT NOT NULL, group_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY(kind,group_id,user_id))")
db.commit()
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
        title="⚔️ CORPSEGRINDER · DIE HORDE RUFT!",
        description=(
            "**Alte Säcke. Kaltes Bier. Für die Horde!** 🍻\n\n"
            "Wähle deine Rollen für die Community. Alles ist freiwillig und "
            "du kannst deine Auswahl jederzeit ändern.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"),
        colour=discord.Colour.from_rgb(143, 35, 27))
    embed.add_field(
        name="⚔️ SPIELBEREICHE",
        value="**PvE** · Dungeons, Quests und Raids\n"
              "**PvP** · Schlachtfelder und Welt-PvP",
        inline=False)
    embed.add_field(
        name="🛡️ DEINE AUFGABEN",
        value="**Tank** · **Heiler** · **DD**\nMehrfachauswahl ist erlaubt.",
        inline=False)
    embed.add_field(
        name="🧙 DEINE KLASSEN",
        value="Wähle eine oder mehrere Klassen im Auswahlmenü.",
        inline=False)
    embed.add_field(
        name="🔔 DEINE NACHRICHTEN",
        value="News-Rollen im Menü auswählen. Erinnerungen und "
              "Gruppenmeldungen kannst du separat ein- oder ausschalten.",
        inline=False)
    embed.set_footer(
        text="Erneut klicken = abwählen • Meine Auswahl = private Übersicht")
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
                await i.response.send_message(
                    embed=my_roles_embed(i.user), ephemeral=True)
        button.callback = overview
        self.add_item(button)
        reminder = discord.ui.Button(
            label="Erinnerungen an/aus", emoji="🔔",
            style=discord.ButtonStyle.secondary, row=4,
            custom_id="corpse_alert_toggle_v112")
        async def toggle_alerts(i):
            if not allowed(i):
                return await answer(i, "Nur auf Corpsegrinder.")
            enabled = not notifications_enabled(i.user.id)
            db.execute(
                "INSERT OR REPLACE INTO notification_preferences(user_id,enabled) VALUES (?,?)",
                (i.user.id, int(enabled)))
            db.commit()
            await answer(i, "🔔 Persönliche Erinnerungen und Gruppenmeldungen: "
                         + ("**EIN**" if enabled else "**AUS**"))
        reminder.callback = toggle_alerts
        self.add_item(reminder)

def notifications_enabled(user_id):
    result = db.execute(
        "SELECT enabled FROM notification_preferences WHERE user_id=?",
        (user_id,)).fetchone()
    return bool(result[0]) if result else True


def my_roles_embed(member):
    embed = discord.Embed(
        title="📜 Deine Corpsegrinder-Rollen",
        description=own_roles(member),
        colour=discord.Colour.from_rgb(178, 90, 34))
    embed.add_field(
        name="🔔 Persönliche Gruppenmeldungen",
        value=("✅ Aktiv · 15-Minuten-Erinnerungen & volle Gruppen"
               if notifications_enabled(member.id)
               else "🔕 Deaktiviert"),
        inline=False)
    embed.set_footer(text="Änderungen jederzeit über #rollenwahl")
    return embed


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
    bot.add_view(PlannerDashboardView())
    bot.add_view(LevelDashboardView())
    for (group_id, message_id) in db.execute(
            "SELECT id,message FROM level_groups WHERE guild=? AND status='open' "
            "AND start_utc>? AND message IS NOT NULL",
            (GUILD_ID, int(datetime.now(timezone.utc).timestamp())-3600)).fetchall():
        bot.add_view(level_group_view(group_id), message_id=message_id)
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
    initialize_scheduler_meta()
    background(apply_all_wow_role_styles_once())
    background(ensure_planner_dashboard_on_start())
    background(ensure_level_dashboard_on_start())
    background(remove_old_guild_category_once())
    background(refresh_community_panels_on_start())
    if not getattr(bot, "event_scheduler_started", False):
        bot.event_scheduler_started = True
        background(event_scheduler_loop())
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
    scheduled = scheduled_voice_details(channel_id)
    if target.members:
        if scheduled:
            db.execute("UPDATE event_meta SET voice_seen=1 WHERE voice_id=?",
                       (channel_id,))
            db.commit()
        return
    # Geplante Treffpunkte dürfen nach Erstellung nicht sofort wieder verschwinden:
    # nie besucht = mindestens eine Stunde zum Eintreffen lassen.
    if scheduled and not scheduled[2]:
        if int(datetime.now(timezone.utc).timestamp()) < scheduled[3] + VOICE_UNUSED_TTL:
            return
    try:
        await target.delete(reason="Corpsegrinder: temporärer Sprachkanal ist leer")
        forget_temp_channel(channel_id)
        if scheduled:
            db.execute("UPDATE event_meta SET voice_id=NULL WHERE voice_id=?", (channel_id,))
            db.commit()
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
    creation_names = ("➕ PvE-Gruppe erstellen", "➕ PvP-Gruppe erstellen")
    if (after.channel is not None and after.channel != before.channel
            and after.channel.name in creation_names):
        kind = "PvE" if "PvE" in after.channel.name else "PvP"
        source = after.channel
        parent = source.category
        bot_member = member.guild.me or member.guild.get_member(bot.user.id)
        if parent is None or bot_member is None:
            logging.warning("Temporäre Gruppe: Kategorie oder Bot-Mitglied nicht gefunden")
            return
        # Ohne 'Mitglieder verschieben' darf Discord den Ersteller nicht bewegen.
        # Dann gar keinen verwaisten Raum erzeugen.
        perms = source.permissions_for(bot_member)
        if not perms.manage_channels or not perms.move_members:
            logging.error(
                "Corpsegrinder: Bot benötigt in %s die Rechte 'Kanäle verwalten' "
                "und 'Mitglieder verschieben' für das automatische Beitreten.",
                source.name)
            try:
                await member.send(
                    "⚠️ Deine " + kind + "-Gruppe wurde noch nicht erstellt: "
                    "Dem WoW Forever Bot fehlen im Discord-Server die Berechtigungen "
                    "**Kanäle verwalten** oder **Mitglieder verschieben**. "
                    "Bitte einen Administrator bitten, sie der Bot-Rolle zu geben.")
            except discord.HTTPException:
                pass
            return
        new_channel = None
        try:
            new_channel = await parent.create_voice_channel(
                (kind + " | " + member.display_name)[:90],
                user_limit=5 if kind == "PvE" else 10,
                reason="Corpsegrinder: temporäre " + kind + "-Gruppe")
            save_setting("temp_" + str(new_channel.id), "1")
            # Sichtbarkeit und Verbindung des Erstellers sind Voraussetzung
            # für den sofortigen automatischen Wechsel.
            user_perms = new_channel.permissions_for(member)
            if not (user_perms.view_channel and user_perms.connect):
                await new_channel.set_permissions(
                    member, view_channel=True, connect=True,
                    reason="Ersteller kann seinen temporären Gruppenraum betreten")
            target_perms = new_channel.permissions_for(bot_member)
            if not target_perms.move_members:
                logging.error("Bot darf im neuen Raum %s keine Mitglieder verschieben", new_channel.id)
                background(delete_temp_if_empty(new_channel.id, delay=7))
                try:
                    await member.send(
                        "⚠️ Der neue Gruppenkanal erlaubt dem Bot kein **Mitglieder verschieben**. "
                        "Bitte einen Administrator um Freigabe bitten.")
                except discord.HTTPException:
                    pass
                return
            # Voice-State und API-Update können kurz zeitversetzt eintreffen.
            for attempt in range(2):
                try:
                    await member.move_to(
                        new_channel, reason="Ersteller automatisch in " + kind + "-Gruppe")
                    break
                except discord.Forbidden:
                    raise
                except (discord.HTTPException, discord.ClientException):
                    if attempt:
                        raise
                    await asyncio.sleep(0.6)
            logging.info("Ersteller %s in neue Gruppe %s verschoben", member.id, new_channel.id)
        except (discord.HTTPException, discord.ClientException):
            logging.exception(
                "Automatisches Erstellen/Beitreten fehlgeschlagen. "
                "Bot benötigt 'Mitglieder verschieben', 'Kanäle verwalten' "
                "und Zugang zur PvE-/PvP-Kategorie.")
            if new_channel is not None:
                background(delete_temp_if_empty(new_channel.id, delay=7))
            try:
                await member.send(
                    "⚠️ Die " + kind + "-Gruppe konnte nicht automatisch betreten werden. "
                    "Bitte prüfe mit einem Admin die Bot-Berechtigung "
                    "**Mitglieder verschieben** im Server und im Voice-Kanal.")
            except discord.HTTPException:
                pass
    if after.channel is not None and scheduled_voice_details(after.channel.id):
        db.execute(
            "UPDATE event_meta SET voice_seen=1 WHERE voice_id=?",
            (after.channel.id,))
        db.commit()
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


# --- Terminplaner für Instanzgruppen ---------------------------------------
# 5er-Dungeon: ein Tank, ein Heiler, drei Schadensklassen.
# Separate SQLite-Tabellen erhalten die bisherigen Gruppenfinder-Daten.
PLAN_ROLES = ("Tank", "Heiler", "DD")
PLAN_LIMITS = {"Tank": 1, "Heiler": 1, "DD": 3}
_PLAN_LOCKS = {}


def plan_lock(group_id):
    if group_id not in _PLAN_LOCKS:
        _PLAN_LOCKS[group_id] = asyncio.Lock()
    return _PLAN_LOCKS[group_id]


def last_sunday(year, month):
    day = calendar.monthrange(year, month)[1]
    while datetime(year, month, day).weekday() != 6:
        day -= 1
    return day


def berlin_now():
    utc = datetime.now(timezone.utc)
    try:
        return utc.astimezone(ZoneInfo("Europe/Berlin"))
    except ZoneInfoNotFoundError:
        y = utc.year
        start = datetime(y, 3, last_sunday(y, 3), 1, tzinfo=timezone.utc)
        end = datetime(y, 10, last_sunday(y, 10), 1, tzinfo=timezone.utc)
        hours = 2 if start <= utc < end else 1
        return utc.astimezone(timezone(timedelta(hours=hours)))


def parse_plan_time(day_text, clock_text):
    label = day_text.strip().casefold()
    today = berlin_now().date()
    if label == "heute":
        chosen = today
    elif label == "morgen":
        chosen = today + timedelta(days=1)
    elif label in ("übermorgen", "uebermorgen"):
        chosen = today + timedelta(days=2)
    else:
        chosen = None
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                chosen = datetime.strptime(day_text.strip(), fmt).date()
                break
            except ValueError:
                pass
        if chosen is None:
            raise ValueError("Datum bitte als heute, morgen, übermorgen oder TT.MM.JJJJ eingeben.")
    if not re.fullmatch(r"[0-2]?\d:[0-5]\d", clock_text.strip()):
        raise ValueError("Uhrzeit bitte als HH:MM eingeben, zum Beispiel 20:00.")
    try:
        hour, minute = map(int, clock_text.strip().split(":"))
        naive = datetime(chosen.year, chosen.month, chosen.day, hour, minute)
    except ValueError as exc:
        raise ValueError("Ungültige Uhrzeit.") from exc
    try:
        zone = ZoneInfo("Europe/Berlin")
        local = naive.replace(tzinfo=zone)
        alternative = naive.replace(tzinfo=zone, fold=1)
        if local.utcoffset() != alternative.utcoffset():
            raise ValueError("Am Tag der Zeitumstellung bitte nicht 02:00–02:59 verwenden.")
        if local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != naive:
            raise ValueError("Uhrzeit existiert wegen der Zeitumstellung nicht.")
    except ZoneInfoNotFoundError:
        march = datetime(chosen.year, 3, last_sunday(chosen.year, 3)).date()
        october = datetime(chosen.year, 10, last_sunday(chosen.year, 10)).date()
        if chosen in (march, october) and hour == 2:
            raise ValueError("Am Tag der Zeitumstellung bitte nicht 02:00–02:59 verwenden.")
        summer = (march < chosen < october) or (
            chosen == march and hour >= 3) or (chosen == october and hour < 2)
        local = naive.replace(tzinfo=timezone(timedelta(hours=2 if summer else 1)))
    when = int(local.astimezone(timezone.utc).timestamp())
    now = int(datetime.now(timezone.utc).timestamp())
    if when < now + 300:
        raise ValueError("Der Termin muss mindestens fünf Minuten in der Zukunft liegen.")
    if when > now + 120 * 86400:
        raise ValueError("Termine höchstens 120 Tage im Voraus planen.")
    display = naive.strftime("%d.%m.%Y · %H:%M") + (
        " MESZ" if local.utcoffset() == timedelta(hours=2) else " MEZ")
    return when, display


def load_plan(group_id):
    return db.execute(
        "SELECT id,guild,owner,instance,start_utc,display_time,note,channel,message,status "
        "FROM planned_groups WHERE id=? AND guild=?",
        (group_id, GUILD_ID)).fetchone()


def plan_members(group_id):
    return db.execute(
        "SELECT user,role FROM planned_signups WHERE group_id=? ORDER BY role,user",
        (group_id,)).fetchall()


def plan_counts(group_id):
    members = plan_members(group_id)
    return {role: sum(item_role == role for _, item_role in members)
            for role in PLAN_ROLES}


def plan_open(plan):
    return (plan is not None and plan[9] == "open" and
            plan[4] > int(datetime.now(timezone.utc).timestamp()) - 3600)


def planned_embed(plan):
    group_id, _, owner, instance, when, display, note, _, _, status = plan
    members = plan_members(group_id)
    counts = plan_counts(group_id)
    full = all(counts[r] == PLAN_LIMITS[r] for r in PLAN_ROLES)
    now = int(datetime.now(timezone.utc).timestamp())
    if status == "cancelled":
        caption, color = "❌ ABGESAGT", discord.Colour.red()
    elif status == "completed":
        caption, color = "✅ ABGESCHLOSSEN", discord.Colour.green()
    elif status in ("expired", "archived") or now >= when + 3600:
        caption, color = "⌛ ABGELAUFEN", discord.Colour.dark_grey()
    elif now >= when:
        caption, color = "⚔️ DUNGEON LÄUFT", discord.Colour.orange()
    elif full:
        caption, color = "🎉 GRUPPE VOLLSTÄNDIG", discord.Colour.gold()
    else:
        caption, color = "🔎 MITSTREITER GESUCHT", discord.Colour.from_rgb(145, 37, 28)
    safe_instance = discord.utils.escape_markdown(instance[:90])
    embed = discord.Embed(
        title="⚔️ " + safe_instance.upper(),
        description=(
            f"**{caption}**  ·  Dungeon **#{group_id}**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 **{display}**\n"
            f"⏳ <t:{when}:R> · 🔔 Erinnerung 15 Min. vorher\n"
            f"👑 Organisiert von <@{owner}>\n"
            + (f"📜 {discord.utils.escape_markdown(note[:160])}\n" if note else "")
        ),
        colour=color)
    filled = len(members)
    embed.add_field(
        name=f"⚔️ SCHLACHTGRUPPE · {filled}/5",
        value=("🟥" * filled + "⬛" * (5-filled)),
        inline=False)
    for role, emoji in (("Tank", "🛡️"), ("Heiler", "💚"), ("DD", "💥")):
        players = [f"<@{user}>" for user, task in members if task == role]
        embed.add_field(
            name=f"{emoji} {role} · {len(players)}/{PLAN_LIMITS[role]}",
            value="\n".join(players) if players else "*Noch frei*",
            inline=True)
    meta = event_meta("dungeon", group_id, create=False)
    if meta and meta[4]:
        embed.add_field(
            name="🔊 Euer Sprach-Treffpunkt",
            value=f"<#{meta[4]}> · **5 Plätze** · ab 15 Min. vor Termin",
            inline=False)
    embed.set_footer(
        text="Für die Horde! • Rolle anklicken = anmelden/wechseln • Abmelden • Organisator: Abschließen")
    return embed


class PlannedView(discord.ui.View):
    def __init__(self, group_id):
        super().__init__(timeout=None)
        for task, emoji in (("Tank", "🛡️"), ("Heiler", "💚"), ("DD", "💥")):
            button = discord.ui.Button(
                label=task, emoji=emoji,
                custom_id=f"corpse_plan_{group_id}_{task}",
                style=discord.ButtonStyle.primary)
            async def choose(interaction, selected=task):
                await plan_signup(interaction, group_id, selected)
            button.callback = choose
            self.add_item(button)
        button = discord.ui.Button(
            label="Abmelden", emoji="❌", style=discord.ButtonStyle.secondary,
            custom_id=f"corpse_plan_{group_id}_leave")
        async def leave(interaction):
            await plan_signup(interaction, group_id, None)
        button.callback = leave
        self.add_item(button)
        finish = discord.ui.Button(
            label="Abschließen", emoji="✅",
            style=discord.ButtonStyle.secondary, row=1,
            custom_id=f"corpse_plan_{group_id}_finish")
        async def completed(interaction):
            await finish_scheduled_group(interaction, "dungeon", group_id)
        finish.callback = completed
        self.add_item(finish)


async def refresh_planned_message(plan):
    target = bot.get_channel(plan[7])
    if not isinstance(target, discord.TextChannel):
        target = await bot.fetch_channel(plan[7])
    message = await target.fetch_message(plan[8])
    await message.edit(
        embed=planned_embed(plan),
        view=PlannedView(plan[0]) if plan_open(plan) else None,
        allowed_mentions=discord.AllowedMentions.none())


async def plan_signup(interaction, group_id, task):
    if not allowed(interaction):
        return await answer(interaction, "Dieser Termin gehört zu Corpsegrinder.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    async with plan_lock(group_id):
        plan = load_plan(group_id)
        if not plan_open(plan):
            return await interaction.followup.send(
                "Der Termin ist nicht mehr offen.", ephemeral=True)
        current = dict(plan_members(group_id)).get(interaction.user.id)
        if task is None:
            if current is None:
                return await interaction.followup.send(
                    "Du bist noch nicht angemeldet.", ephemeral=True)
            db.execute(
                "DELETE FROM planned_signups WHERE group_id=? AND user=?",
                (group_id, interaction.user.id))
            result = "Du bist abgemeldet."
        else:
            if task == current:
                return await interaction.followup.send(
                    "Du bist bereits als " + task + " angemeldet.", ephemeral=True)
            if plan_counts(group_id)[task] >= PLAN_LIMITS[task]:
                return await interaction.followup.send(
                    "Dieser Platz ist bereits belegt. Wähle eine andere Rolle.",
                    ephemeral=True)
            db.execute(
                "INSERT OR REPLACE INTO planned_signups(group_id,user,role) VALUES (?,?,?)",
                (group_id, interaction.user.id, task))
            result = "Du bist jetzt als " + task + " angemeldet."
        db.commit()
        try:
            await refresh_planned_message(plan)
            result += " Die Übersicht wurde aktualisiert."
        except discord.HTTPException:
            logging.exception("Termin #%s gespeichert, Embed nicht aktualisiert", group_id)
            result += " Gespeichert, aber Discord konnte die Anzeige nicht aktualisieren."
        await interaction.followup.send(result, ephemeral=True)




COMMON_DUNGEONS = (
    "Flammenschlund", "Höhlen des Wehklagens", "Die Todesminen",
    "Burg Schattenfang", "Tiefschwarze Grotte", "Gnomeregan",
    "Kral der Klingenhauer", "Scharlachrotes Kloster", "Uldaman",
    "Zul'Farrak", "Maraudon", "Versunkener Tempel", "Schwarzfelstiefen",
    "Stratholme", "Scholomance", "Düsterbruch", "Untere Schwarzfelsspitze",
    "Obere Schwarzfelsspitze"
)


async def suggest_dungeons(i, current):
    matching = [name for name in COMMON_DUNGEONS
                if current.casefold() in name.casefold()]
    return [app_commands.Choice(name=name, value=name) for name in matching[:20]]


@bot.tree.command(
    name="gruppe_planen",
    description="Instanztermin mit 1 Tank, 1 Heiler und 3 DD erstellen",
    guild=SERVER)
@app_commands.describe(
    instanz="Welche Instanz? Beispiel: Flammenschlund",
    tag="heute, morgen, übermorgen oder TT.MM.JJJJ",
    uhrzeit="Deutsche Uhrzeit, zum Beispiel 20:00",
    rolle="Mit welcher Rolle spielst du mit?",
    notiz="Optional: Level, Treffpunkt, Hinweise")
@app_commands.choices(rolle=[app_commands.Choice(name=r, value=r)
                              for r in PLAN_ROLES])
@app_commands.autocomplete(instanz=suggest_dungeons)
async def create_planned_group(
        i: discord.Interaction, instanz: str, tag: str, uhrzeit: str,
        rolle: app_commands.Choice[str], notiz: str = ""):
    if not allowed(i):
        return await answer(i, "Nur auf Corpsegrinder verfügbar.")
    target = channel(i.guild, "dungeons")
    if not isinstance(target, discord.TextChannel):
        return await answer(i, "Kanal #dungeons ist nicht vorhanden.")
    instanz = instanz.strip()
    if not 2 <= len(instanz) <= 90:
        return await answer(i, "Instanzname: 2 bis 90 Zeichen.")
    if len(notiz) > 160:
        return await answer(i, "Notiz: höchstens 160 Zeichen.")
    try:
        when, display = parse_plan_time(tag, uhrzeit)
    except ValueError as exc:
        return await answer(i, str(exc))
    await i.response.defer(ephemeral=True, thinking=True)
    try:
        message, group_id = await create_plan_record_and_post(
            i.guild, i.user.id, instanz, when, display, rolle.value, notiz.strip())
    except (discord.HTTPException, ValueError):
        logging.exception("Konnte neue Gruppensuche nicht veröffentlichen")
        return await i.followup.send(
            "Der Termin konnte nicht veröffentlicht werden. "
            "Bitte Bot-Berechtigungen in #dungeons prüfen.",
            ephemeral=True)
    await i.followup.send(
        f"✅ Termin **#{group_id}** für **{discord.utils.escape_markdown(instanz)}** "
        f"am {display} erstellt. Du bist als **{rolle.value}** angemeldet.\n"
        + message.jump_url, ephemeral=True)


@bot.tree.command(name="termine",
                  description="Nächste geplante Dungeon-Gruppen anzeigen",
                  guild=SERVER)
async def upcoming_plans(i: discord.Interaction):
    if not allowed(i):
        return await answer(i, "Nur auf Corpsegrinder verfügbar.")
    rows = db.execute(
        "SELECT id,instance,start_utc,channel,message FROM planned_groups "
        "WHERE guild=? AND status='open' AND start_utc>? "
        "ORDER BY start_utc LIMIT 8",
        (GUILD_ID, int(datetime.now(timezone.utc).timestamp()) - 3600)).fetchall()
    if not rows:
        return await answer(i, "Noch keine Termine geplant. Erstelle einen mit /gruppe_planen.")
    parts = []
    for group_id, instance, when, channel_id, message_id in rows:
        counts = plan_counts(group_id)
        slots = f"🛡️ {counts['Tank']}/1 · 💚 {counts['Heiler']}/1 · 💥 {counts['DD']}/3"
        link = (f"https://discord.com/channels/{GUILD_ID}/{channel_id}/{message_id}"
                if channel_id and message_id else "")
        part = f"**#{group_id} {discord.utils.escape_markdown(instance[:65])}** · <t:{when}:f>\n{slots}"
        parts.append(part + (f"\n[Zur Anmeldung]({link})" if link else ""))
    await answer(i, "\n\n".join(parts))


@bot.tree.command(name="termin_absagen",
                  description="Eigenen Dungeon-Termin absagen (oder als Admin)",
                  guild=SERVER)
async def cancel_planned_group(i: discord.Interaction, termin_id: int):
    if not allowed(i):
        return await answer(i, "Nur auf Corpsegrinder verfügbar.")
    await i.response.defer(ephemeral=True, thinking=True)
    async with plan_lock(termin_id):
        plan = load_plan(termin_id)
        if not plan:
            return await i.followup.send("Termin nicht gefunden.", ephemeral=True)
        if i.user.id != plan[2] and not admin(i):
            return await i.followup.send(
                "Nur der Organisator oder ein Administrator kann diesen Termin absagen.",
                ephemeral=True)
        if plan[9] == "cancelled":
            return await i.followup.send("Termin bereits abgesagt.", ephemeral=True)
        db.execute("UPDATE planned_groups SET status='cancelled' WHERE id=?", (termin_id,))
        db.commit()
        try:
            await refresh_planned_message(load_plan(termin_id))
            result = "Der Termin wurde als abgesagt markiert."
        except discord.HTTPException:
            logging.exception("Terminabsage gespeichert, Anzeige konnte nicht aktualisiert werden")
            result = "Termin abgesagt, aber Discord konnte die Nachricht nicht aktualisieren."
        await i.followup.send(result, ephemeral=True)


@bot.tree.command(name="termin_verschieben",
                  description="Deinen Dungeon-Termin auf eine andere Uhrzeit verschieben",
                  guild=SERVER)
@app_commands.describe(
    termin_id="Termin-Nummer aus der Gruppenkarte",
    tag="morgen, übermorgen oder TT.MM.JJJJ",
    uhrzeit="Neue deutsche Uhrzeit, z. B. 19:30")
async def reschedule_planned_group(
        i: discord.Interaction, termin_id: int, tag: str, uhrzeit: str):
    if not allowed(i):
        return await answer(i, "Nur auf Corpsegrinder verfügbar.")
    await i.response.defer(ephemeral=True, thinking=True)
    async with plan_lock(termin_id):
        plan = load_plan(termin_id)
        if not plan or plan[9] == "cancelled":
            return await i.followup.send("Termin nicht vorhanden oder abgesagt.", ephemeral=True)
        if i.user.id != plan[2] and not admin(i):
            return await i.followup.send(
                "Nur Organisator oder Administrator können diesen Termin verschieben.",
                ephemeral=True)
        try:
            when, display = parse_plan_time(tag, uhrzeit)
        except ValueError as exc:
            return await i.followup.send(str(exc), ephemeral=True)
        db.execute("UPDATE planned_groups SET start_utc=?,display_time=? WHERE id=?",
                   (when, display, termin_id))
        db.commit()
        try:
            await refresh_planned_message(load_plan(termin_id))
            result = "Termin verschoben auf " + display + ". Alle bisherigen Anmeldungen bleiben erhalten."
        except discord.HTTPException:
            result = "Termin verschoben, aber Discord konnte die Karte noch nicht aktualisieren."
        await i.followup.send(result, ephemeral=True)





async def create_plan_record_and_post(guild, user_id, instance, when, display, role, note=""):
    """Gemeinsamer Veröffentlichungsweg für Slash-Befehl und Dropdown-Assistent."""
    target = channel(guild, "dungeons")
    if not isinstance(target, discord.TextChannel):
        raise ValueError("Kanal #dungeons fehlt.")
    if role not in PLAN_ROLES or not 2 <= len(instance) <= 90 or len(note) > 160:
        raise ValueError("Instanz-/Rollen-Auswahl ungültig.")
    if when < int(datetime.now(timezone.utc).timestamp()) + 30:
        raise ValueError("Der Termin liegt in der Vergangenheit.")
    db.execute(
        "INSERT INTO planned_groups (guild,owner,instance,start_utc,display_time,note) "
        "VALUES (?,?,?,?,?,?)",
        (GUILD_ID, user_id, instance.strip(), when, display, note.strip()))
    group_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute(
        "INSERT INTO planned_signups(group_id,user,role) VALUES (?,?,?)",
        (group_id, user_id, role))
    db.commit()
    plan = load_plan(group_id)
    try:
        message = await target.send(
            embed=planned_embed(plan),
            view=PlannedView(group_id),
            allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        db.execute("DELETE FROM planned_signups WHERE group_id=?", (group_id,))
        db.execute("DELETE FROM planned_groups WHERE id=?", (group_id,))
        db.commit()
        raise
    db.execute("UPDATE planned_groups SET channel=?,message=? WHERE id=?",
               (target.id, message.id, group_id))
    db.commit()
    bot.add_view(PlannedView(group_id), message_id=message.id)
    return message, group_id


# --- Interaktiver Dungeon-Planer (1.0.10) ---------------------------------
# Die Dungeon-Steuerzentrale ist eine dauerhafte Nachricht im #dungeons-Kanal.
# Der zwei-stufige Assistent ist privat und gilt nur für die auslösende Person.

PLANNER_MARKER = "corpsegrinder:planner-dashboard"
PLANNER_STORAGE_KEY = "planner_dashboard_message_v110"
WEEKDAY_DE = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


def planner_dashboard_embed():
    embed = discord.Embed(
        title="🏰 CORPSEGRINDER · DUNGEON-PLANER",
        description=(
            "**Für die Horde!** Plane Instanzbesuche ohne umständliche Befehle. "
            "Wähle über die Buttons eine Instanz, deine Aufgabe und den gewünschten Termin. "
            "Der Assistent ist **nur für dich sichtbar**, bis du die Gruppe veröffentlichst."
        ),
        colour=discord.Colour.dark_red()
    )
    embed.add_field(
        name="⚔️ 1. Dungeon planen",
        value="Instanz & Rolle auswählen → Datum & Uhrzeit einstellen → veröffentlichen.",
        inline=False)
    embed.add_field(
        name="🛡️ 2. Spieler finden",
        value="**1 Tank · 1 Heiler · 3 DD** – alle tragen sich direkt auf der Gruppenkarte ein.",
        inline=False)
    embed.add_field(
        name="📅 3. Überblick behalten",
        value="Nächste Termine ansehen oder deine eigenen Termine aufrufen. "
              "Gruppen können vom Organisator verschoben und abgesagt werden.",
        inline=False)
    embed.set_footer(text="Corpsegrinder • Dungeonplaner • " + PLANNER_MARKER)
    return embed


def wizard_state(user_id):
    return {
        "owner": user_id,
        "instance": None,
        "role": None,
        "day": None,
        "hour": "20",
        "minute": "00",
        "note": "",
        "published": False,
        "message_url": None,
    }


def wizard_embed(state, step=1, notice=None):
    embed = discord.Embed(
        title=("🏰 Terminplanung · 1/2" if step == 1
               else "📅 Terminplanung · 2/2"),
        description=(
            "**Wähle Instanz und Aufgabe** und klicke dann auf **Weiter**."
            if step == 1 else
            "**Datum und Uhrzeit auswählen.** Danach kannst du die Gruppe "
            "im PvE-Kanal veröffentlichen."
        ),
        colour=discord.Colour.gold()
    )
    embed.add_field(name="🏰 Instanz", value=state["instance"] or "Noch nicht gewählt", inline=False)
    embed.add_field(
        name="🎭 Deine Rolle",
        value={"Tank": "🛡️ Tank", "Heiler": "💚 Heiler", "DD": "💥 DD"}
        .get(state["role"], "Noch nicht gewählt"),
        inline=True)
    day = state["day"]
    try:
        if day:
            pretty = datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m.%Y")
        else:
            pretty = "Noch nicht gewählt"
    except ValueError:
        pretty = "Noch nicht gewählt"
    embed.add_field(name="🗓️ Tag", value=pretty, inline=True)
    embed.add_field(
        name="🕗 Uhrzeit", value=state["hour"] + ":" + state["minute"] + " Uhr",
        inline=True)
    if state.get("note"):
        embed.add_field(name="📝 Hinweis", value=state["note"][:160], inline=False)
    if notice:
        embed.add_field(name="Hinweis", value=notice[:700], inline=False)
    embed.set_footer(text="Private Auswahl • Nach 10 Minuten erneut starten")
    return embed


class WizardSelect(discord.ui.Select):
    def __init__(self, state, field, placeholder, options, row):
        super().__init__(
            placeholder=placeholder, min_values=1, max_values=1,
            options=options, row=row)
        self.state = state
        self.field = field

    async def callback(self, interaction):
        self.state[self.field] = self.values[0]
        step = 1 if self.field in ("instance", "role") else 2
        await interaction.response.edit_message(
            embed=wizard_embed(self.state, step),
            view=(WizardStepOne(self.state) if step == 1
                  else WizardStepTwo(self.state)))


class PrivateWizard(discord.ui.View):
    def __init__(self, state):
        super().__init__(timeout=600)
        self.state = state

    async def interaction_check(self, interaction):
        if interaction.user.id == self.state["owner"]:
            return True
        await interaction.response.send_message(
            "Dieser Termin-Assistent gehört einer anderen Person. "
            "Benutze die öffentliche Steuerzentrale für deine eigene Gruppe.",
            ephemeral=True)
        return False


class CustomInstanceModal(discord.ui.Modal, title="Eigene Instanz auswählen"):
    instance = discord.ui.TextInput(
        label="Instanzname", placeholder="Zum Beispiel eine besondere Instanz",
        min_length=2, max_length=90, required=True)
    note = discord.ui.TextInput(
        label="Optionaler Hinweis", placeholder="Zum Beispiel Mindestlevel",
        style=discord.TextStyle.paragraph, max_length=160, required=False)

    def __init__(self, state):
        super().__init__()
        self.state = state

    async def on_submit(self, interaction):
        if interaction.user.id != self.state["owner"]:
            return await interaction.response.send_message(
                "Diese Auswahl gehört nicht dir.", ephemeral=True)
        self.state["instance"] = str(self.instance.value).strip()
        self.state["note"] = str(self.note.value or "").strip()
        # Modal-Antwort als neue private Nachricht: der Hauptkanal bleibt sauber.
        await interaction.response.send_message(
            embed=wizard_embed(self.state, 1),
            view=WizardStepOne(self.state), ephemeral=True)


class WizardStepOne(PrivateWizard):
    def __init__(self, state):
        super().__init__(state)
        self.add_item(WizardSelect(
            state, "instance", "🏰 Instanz auswählen",
            [discord.SelectOption(
                label=name, value=name,
                default=(state["instance"] == name))
                for name in COMMON_DUNGEONS[:25]],
            row=0))
        self.add_item(WizardSelect(
            state, "role", "🛡️ Deine Rolle auswählen",
            [discord.SelectOption(
                label=r, value=r,
                emoji={"Tank": "🛡️", "Heiler": "💚", "DD": "💥"}[r],
                default=(state["role"] == r))
                for r in PLAN_ROLES],
            row=1))

    @discord.ui.button(label="Andere Instanz", emoji="✏️",
                       style=discord.ButtonStyle.secondary, row=2)
    async def custom(self, interaction, button):
        await interaction.response.send_modal(CustomInstanceModal(self.state))

    @discord.ui.button(label="Weiter zum Termin", emoji="➡️",
                       style=discord.ButtonStyle.success, row=2)
    async def forward(self, interaction, button):
        if not self.state["instance"] or not self.state["role"]:
            return await interaction.response.send_message(
                "Bitte zuerst eine Instanz und deine Rolle auswählen.", ephemeral=True)
        await interaction.response.edit_message(
            embed=wizard_embed(self.state, 2),
            view=WizardStepTwo(self.state))


class WizardStepTwo(PrivateWizard):
    def __init__(self, state):
        super().__init__(state)
        today = berlin_now().date()
        options = []
        for index in range(21):
            day = today + timedelta(days=index)
            prefix = ("Heute" if index == 0
                      else "Morgen" if index == 1
                      else "Übermorgen" if index == 2 else WEEKDAY_DE[day.weekday()])
            options.append(discord.SelectOption(
                label=f"{prefix} · {day:%d.%m.%Y}",
                value=day.isoformat(),
                default=(state["day"] == day.isoformat())))
        self.add_item(WizardSelect(
            state, "day", "📅 Tag auswählen (nächste 21 Tage)",
            options, row=0))
        self.add_item(WizardSelect(
            state, "hour", "🕗 Stunde auswählen",
            [discord.SelectOption(
                label=f"{n:02d}:00 Uhr", value=f"{n:02d}",
                default=(state["hour"] == f"{n:02d}"))
                for n in range(24)],
            row=1))
        self.add_item(WizardSelect(
            state, "minute", "⏱️ Minuten auswählen",
            [discord.SelectOption(
                label=f"{n:02d} Minuten", value=f"{n:02d}",
                default=(state["minute"] == f"{n:02d}"))
                for n in (0, 15, 30, 45)],
            row=2))

    @discord.ui.button(label="Zurück", emoji="⬅️",
                       style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            embed=wizard_embed(self.state, 1),
            view=WizardStepOne(self.state))

    @discord.ui.button(label="Termin veröffentlichen", emoji="✅",
                       style=discord.ButtonStyle.success, row=3)
    async def publish(self, interaction, button):
        state = self.state
        if state["published"]:
            return await interaction.response.send_message(
                "Dein Termin wurde bereits veröffentlicht: " +
                (state["message_url"] or ""), ephemeral=True)
        if not all(state[k] for k in ("instance", "role", "day")):
            return await interaction.response.send_message(
                "Bitte zuerst Instanz, Rolle und Datum auswählen.", ephemeral=True)
        try:
            when, display = parse_plan_time(
                state["day"], state["hour"] + ":" + state["minute"])
        except ValueError as exc:
            return await interaction.response.send_message(
                str(exc), ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        async with plan_lock(-interaction.user.id):
            if state["published"]:
                return await interaction.followup.send(
                    "Dieser Termin wurde bereits erstellt: " +
                    (state["message_url"] or ""), ephemeral=True)
            try:
                message, group_id = await create_plan_record_and_post(
                    interaction.guild, interaction.user.id, state["instance"],
                    when, display, state["role"], state["note"])
            except (discord.HTTPException, ValueError) as exc:
                logging.exception("Konnte Dungeon-Termin über Assistent nicht erstellen")
                return await interaction.followup.send(
                    "Der Termin konnte nicht veröffentlicht werden. "
                    "Bitte Discord-Kanalberechtigungen prüfen.",
                    ephemeral=True)
            state["published"] = True
            state["message_url"] = message.jump_url
        await interaction.followup.send(
            f"✅ **Gruppe #{group_id} erstellt!**\n"
            f"🏰 **{discord.utils.escape_markdown(state['instance'])}** · {display}\n"
            f"Du bist als **{state['role']}** eingetragen.\n"
            f"[Zur Gruppenkarte]({message.jump_url})",
            ephemeral=True)


class PlannerDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Dungeon planen", emoji="🏰",
                       style=discord.ButtonStyle.success,
                       custom_id="corpse_planner_new_v110")
    async def start(self, interaction, button):
        if not allowed(interaction):
            return await interaction.response.send_message(
                "Nur in Corpsegrinder verfügbar.", ephemeral=True)
        state = wizard_state(interaction.user.id)
        await interaction.response.send_message(
            embed=wizard_embed(state),
            view=WizardStepOne(state), ephemeral=True)

    @discord.ui.button(label="Nächste Termine", emoji="📅",
                       style=discord.ButtonStyle.primary,
                       custom_id="corpse_planner_upcoming_v110")
    async def upcoming(self, interaction, button):
        if not allowed(interaction):
            return await interaction.response.send_message(
                "Nur in Corpsegrinder verfügbar.", ephemeral=True)
        await interaction.response.send_message(
            embed=planner_list_embed(), ephemeral=True)

    @discord.ui.button(label="Meine Termine", emoji="📋",
                       style=discord.ButtonStyle.secondary,
                       custom_id="corpse_planner_mine_v110")
    async def mine(self, interaction, button):
        if not allowed(interaction):
            return await interaction.response.send_message(
                "Nur in Corpsegrinder verfügbar.", ephemeral=True)
        await interaction.response.send_message(
            embed=planner_list_embed(user_id=interaction.user.id), ephemeral=True)


def planner_list_embed(user_id=None):
    cutoff = int(datetime.now(timezone.utc).timestamp()) - 3600
    if user_id is None:
        rows = db.execute(
            "SELECT id,instance,start_utc,channel,message FROM planned_groups "
            "WHERE guild=? AND status='open' AND start_utc>? "
            "ORDER BY start_utc LIMIT 8", (GUILD_ID, cutoff)).fetchall()
    else:
        rows = db.execute(
            "SELECT g.id,g.instance,g.start_utc,g.channel,g.message "
            "FROM planned_groups g WHERE g.guild=? AND g.status='open' "
            "AND g.start_utc>? AND "
            "(g.owner=? OR EXISTS (SELECT 1 FROM planned_signups s "
            "WHERE s.group_id=g.id AND s.user=?)) "
            "ORDER BY g.start_utc LIMIT 8",
            (GUILD_ID, cutoff, user_id, user_id)).fetchall()
    embed = discord.Embed(
        title="📅 " + ("Meine Dungeon-Termine" if user_id else "Nächste Dungeon-Termine"),
        colour=discord.Colour.blue())
    if not rows:
        embed.description = "Noch keine passenden Termine. "
        embed.description += "Erstelle einen über **🏰 Dungeon planen**!"
        return embed
    for group_id, instance, when, channel_id, message_id in rows:
        counts = plan_counts(group_id)
        slots = (f"🛡️ {counts['Tank']}/1 · 💚 {counts['Heiler']}/1 · "
                 f"💥 {counts['DD']}/3")
        link = (f"https://discord.com/channels/{GUILD_ID}/{channel_id}/{message_id}"
                if channel_id and message_id else None)
        embed.add_field(
            name=f"🏰 #{group_id} · {discord.utils.escape_markdown(instance[:65])}",
            value=(f"🗓️ <t:{when}:f>\n{slots}\n"
                   + (f"[Zur Gruppenkarte]({link})" if link else "")),
            inline=False)
    embed.set_footer(text="In der Gruppenkarte auf deine Rolle klicken, um dich anzumelden.")
    return embed


async def ensure_planner_dashboard(guild):
    target = channel(guild, "dungeons")
    if not isinstance(target, discord.TextChannel):
        logging.warning("Dungeon-Planer: #dungeons fehlt")
        return None, False
    existing = None
    old_post_id = setting(PLANNER_STORAGE_KEY)
    post_id = old_post_id
    if post_id:
        try:
            candidate = await target.fetch_message(int(post_id))
            if candidate.author.id == bot.user.id:
                existing = candidate
        except (discord.HTTPException, ValueError):
            pass
    if existing is None:
        try:
            async for candidate in target.history(limit=80):
                if candidate.author.id == bot.user.id and any(
                        PLANNER_MARKER in (emb.footer.text or "")
                        for emb in candidate.embeds):
                    existing = candidate
                    break
        except discord.HTTPException:
            logging.warning("Dungeon-Planer: bisherige Nachrichten nicht lesbar")
    if existing is None:
        existing = await target.send(
            embed=planner_dashboard_embed(),
            view=PlannerDashboardView(),
            allowed_mentions=discord.AllowedMentions.none())
    else:
        await existing.edit(embed=planner_dashboard_embed(),
                            view=PlannerDashboardView())
    save_setting(PLANNER_STORAGE_KEY, existing.id)
    # Nur den alten, eigenen Dungeon-Panelpost aus #pve-gruppensuche entfernen.
    # Bereits erstellte Gruppentermine und fremde Nachrichten bleiben bestehen.
    if old_post_id and str(old_post_id) != str(existing.id):
        old_channel = channel(guild, "pve-gruppensuche")
        if isinstance(old_channel, discord.TextChannel):
            try:
                previous = await old_channel.fetch_message(int(old_post_id))
                if previous.author.id == bot.user.id and any(
                        PLANNER_MARKER in (embed.footer.text or "")
                        for embed in previous.embeds):
                    await previous.delete()
                    logging.info("Altes Dungeon-Panel aus PvE-Gruppensuche entfernt")
            except (discord.HTTPException, ValueError):
                logging.warning("Altes Dungeon-Panel konnte nicht gelöscht werden")
    # Zusätzlich ohne fremde Kanal-Themen zu überschreiben einen Link anbieten.
    if not target.topic:
        try:
            await target.edit(
                topic="🏰 Dungeon planen und Termine finden: " + existing.jump_url,
                reason="Corpsegrinder Dungeon-Steuerzentrale")
        except discord.HTTPException:
            logging.warning("Kanalthema konnte nicht gesetzt werden")
    pinned = existing.pinned
    if not pinned:
        try:
            await existing.pin(reason="Corpsegrinder: Dungeon-Planer")
            pinned = True
        except discord.Forbidden:
            logging.warning(
                "Dungeon-Planer veröffentlicht, aber nicht angepinnt. "
                "Bot benötigt Nachrichten verwalten; alternativ selbst anpinnen.")
        except discord.HTTPException:
            logging.exception("Dungeon-Planer konnte nicht angepinnt werden")
    return existing, pinned



async def ensure_planner_dashboard_on_start():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    try:
        await ensure_planner_dashboard(guild)
    except discord.HTTPException:
        logging.exception("Konnte Dungeon-Steuerzentrale beim Start nicht einrichten")



@bot.tree.command(
    name="gruppenpanel",
    description="Angeheftete PvE-Dungeon-Steuerzentrale einrichten (Admin)",
    guild=SERVER)
async def set_planner_dashboard(interaction: discord.Interaction):
    if not admin(interaction):
        return await answer(interaction, "Nur Administratoren.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        message, pinned = await ensure_planner_dashboard(interaction.guild)
    except discord.HTTPException:
        logging.exception("Dungeon-Steuerzentrale")
        return await interaction.followup.send(
            "Konnte die Steuerzentrale nicht erstellen. "
            "Bitte die Schreib- und Leserechte des Bots prüfen.", ephemeral=True)
    if message is None:
        return await interaction.followup.send(
            "#dungeons nicht gefunden.", ephemeral=True)
    note = "✅ Angepinnt" if pinned else "⚠️ Nicht angepinnt: Bitte Nachricht selbst anpinnen."
    await interaction.followup.send(
        f"🏰 Dungeon-Steuerzentrale: {message.jump_url}\n{note}",
        ephemeral=True)




# ---------------------------------------------------------------------------
# Levelgruppen-Planer: separates Fünfer-Questteam statt Dungeon-Rollenpflicht.
# Alles bleibt in den erlaubten Bot-Dateien, damit /bot_update weiter funktioniert.
# ---------------------------------------------------------------------------
LEVEL_AREAS = (
    "Durotar", "Mulgore", "Tirisfal", "Brachland", "Silberwald",
    "Steinkrallengebirge", "Vorgebirge des Hügellands", "Eschental",
    "Tausend Nadeln", "Desolace", "Schlingendorntal", "Arathihochland",
    "Düstermarschen", "Sümpfe des Elends", "Tanaris", "Feralas",
    "Hinterland", "Sengende Schlucht", "Un'Goro-Krater", "Teufelswald",
    "Westliche Pestländer", "Östliche Pestländer", "Brennende Steppe",
    "Winterquell",
)
LEVEL_RANGES = (
    (1, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 35),
    (35, 40), (40, 45), (45, 50), (50, 55), (55, 60), (1, 60),
)
LEVEL_PANEL_MARKER = "corpsegrinder:level-dashboard"
LEVEL_PANEL_SETTING = "level_dashboard_v111"
_LEVEL_LOCKS = {}


def level_lock(group_id):
    if group_id not in _LEVEL_LOCKS:
        _LEVEL_LOCKS[group_id] = asyncio.Lock()
    return _LEVEL_LOCKS[group_id]


def level_record(group_id):
    return db.execute(
        "SELECT id,guild,owner,area,min_level,max_level,start_utc,display_time,"
        "note,channel,message,status FROM level_groups WHERE id=? AND guild=?",
        (group_id, GUILD_ID)).fetchone()


def level_players(group_id):
    return [row[0] for row in db.execute(
        "SELECT user FROM level_signups WHERE group_id=? ORDER BY rowid",
        (group_id,)).fetchall()]


def level_open(record):
    return (record is not None and record[11] == "open"
            and record[6] >= int(datetime.now(timezone.utc).timestamp()) - 3600)


def level_card(record):
    group_id, _, owner, area, low, high, when, display, note, _, _, status = record
    members = level_players(group_id)
    now = int(datetime.now(timezone.utc).timestamp())
    if status == "cancelled":
        label, color = "❌ ABGESAGT", discord.Colour.red()
    elif status == "completed":
        label, color = "✅ ABGESCHLOSSEN", discord.Colour.green()
    elif status in ("expired", "archived") or now >= when + 3600:
        label, color = "⌛ ABGELAUFEN", discord.Colour.dark_grey()
    elif now >= when:
        label, color = "🌿 QUESTGRUPPE LÄUFT", discord.Colour.orange()
    elif len(members) == 5:
        label, color = "🎉 GRUPPE VOLLSTÄNDIG", discord.Colour.gold()
    else:
        label, color = "🌿 MITSTREITER GESUCHT", discord.Colour.from_rgb(46, 142, 83)
    embed = discord.Embed(
        title="🌿 " + discord.utils.escape_markdown(area[:90]).upper(),
        description=(
            f"**{label}**  ·  Levelgruppe **#{group_id}**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 **{display}**  ·  <t:{when}:R>\n"
            f"🎚️ **Level {low}–{high}**  ·  🔔 Erinnerung 15 Min. vorher\n"
            f"👑 Organisiert von <@{owner}>\n"
            + (f"📝 {discord.utils.escape_markdown(note[:160])}\n" if note else "")
        ),
        colour=color)
    embed.add_field(
        name=f"👥 QUELLEN-TRUPP · {len(members)}/5",
        value=("🟩" * len(members) + "⬛" * (5-len(members))),
        inline=False)
    embed.add_field(
        name="🍃 DIE ABENTEURER",
        value=("\n".join(f"• <@{user}>" for user in members)
               if members else "*Noch keine Anmeldung*"),
        inline=False)
    if level_open(record) and len(members) < 5:
        embed.add_field(
            name="Noch Platz am Lagerfeuer",
            value=f"✨ **{5-len(members)}** freie Plätze",
            inline=False)
    meta = event_meta("level", group_id, create=False)
    if meta and meta[4]:
        embed.add_field(
            name="🔊 Euer Treffpunkt",
            value=f"<#{meta[4]}> · max. 5 Mitspieler",
            inline=False)
    embed.set_footer(
        text="Corpsegrinder • Dabei sein / Abmelden • Organisator: Abschließen")
    return embed


class LevelGroupView(discord.ui.View):
    def __init__(self, group_id):
        super().__init__(timeout=None)
        self.group_id = group_id

    @discord.ui.button(label="Dabei sein", emoji="✅",
                       custom_id="corpse_level_join_placeholder",
                       style=discord.ButtonStyle.success)
    async def join(self, interaction, button):
        await join_level_group(interaction, self.group_id, True)

    @discord.ui.button(label="Abmelden", emoji="❌",
                       custom_id="corpse_level_leave_placeholder",
                       style=discord.ButtonStyle.secondary)
    async def leave(self, interaction, button):
        await join_level_group(interaction, self.group_id, False)

    @discord.ui.button(label="Abschließen", emoji="✅",
                       custom_id="corpse_level_finish_placeholder",
                       style=discord.ButtonStyle.secondary)
    async def finish(self, interaction, button):
        await finish_scheduled_group(interaction, "level", self.group_id)


def level_group_view(group_id):
    view = LevelGroupView(group_id)
    for item in view.children:
        if isinstance(item, discord.ui.Button):
            prefix = ("join" if item.label == "Dabei sein"
                      else "finish" if item.label == "Abschließen" else "leave")
            item.custom_id = f"corpse_level_{group_id}_{prefix}"
    return view


async def refresh_level_card(record):
    target = bot.get_channel(record[9])
    if not isinstance(target, discord.TextChannel):
        target = await bot.fetch_channel(record[9])
    post = await target.fetch_message(record[10])
    await post.edit(
        embed=level_card(record),
        view=(level_group_view(record[0]) if level_open(record) else None),
        allowed_mentions=discord.AllowedMentions.none())


async def join_level_group(interaction, group_id, joining):
    if not allowed(interaction):
        return await answer(interaction, "Dieser Termin gehört nicht zu Corpsegrinder.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    async with level_lock(group_id):
        group = level_record(group_id)
        if not level_open(group):
            return await interaction.followup.send(
                "Diese Levelgruppe ist nicht mehr offen.", ephemeral=True)
        players = level_players(group_id)
        me = interaction.user.id
        if joining and me in players:
            return await interaction.followup.send(
                "Du bist bereits angemeldet.", ephemeral=True)
        if not joining and me not in players:
            return await interaction.followup.send(
                "Du bist nicht angemeldet.", ephemeral=True)
        if joining:
            if len(players) >= 5:
                return await interaction.followup.send(
                    "Die Gruppe ist voll (5/5).", ephemeral=True)
            db.execute("INSERT OR IGNORE INTO level_signups(group_id,user) VALUES (?,?)",
                       (group_id, me))
            response = "✅ Du bist jetzt für diese Levelgruppe angemeldet!"
        else:
            db.execute("DELETE FROM level_signups WHERE group_id=? AND user=?",
                       (group_id, me))
            response = "❌ Du bist aus der Levelgruppe ausgetragen."
        db.commit()
        try:
            await refresh_level_card(group)
        except discord.HTTPException:
            logging.exception("Levelgruppe #%s gespeichert, Nachricht nicht aktualisiert", group_id)
            response += " Die Übersicht konnte gerade nicht aktualisiert werden."
        await interaction.followup.send(response, ephemeral=True)


async def publish_level_group(guild, user_id, area, low, high, when, display, note=""):
    dest = channel(guild, "pve-gruppensuche")
    if not isinstance(dest, discord.TextChannel):
        raise ValueError("Kanal #pve-gruppensuche fehlt.")
    if not 2 <= len(area) <= 90 or not 1 <= low <= high <= 60 or len(note) > 160:
        raise ValueError("Ungültige Gebiets- oder Levelangabe.")
    if when < int(datetime.now(timezone.utc).timestamp()) + 30:
        raise ValueError("Dieser Termin liegt schon in der Vergangenheit.")
    cursor = db.execute(
        "INSERT INTO level_groups(guild,owner,area,min_level,max_level,start_utc,display_time,note) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (GUILD_ID, user_id, area, low, high, when, display, note))
    group_id = cursor.lastrowid
    db.execute("INSERT INTO level_signups(group_id,user) VALUES (?,?)",
               (group_id, user_id))
    db.commit()
    group = level_record(group_id)
    try:
        message = await dest.send(
            embed=level_card(group),
            view=level_group_view(group_id),
            allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        db.execute("DELETE FROM level_signups WHERE group_id=?", (group_id,))
        db.execute("DELETE FROM level_groups WHERE id=?", (group_id,))
        db.commit()
        raise
    db.execute("UPDATE level_groups SET channel=?,message=? WHERE id=?",
               (dest.id, message.id, group_id))
    db.commit()
    bot.add_view(level_group_view(group_id), message_id=message.id)
    return message, group_id



# ---------------------------------------------------------------------------
# Interaktive Level-Planung, mit eigener Steuerzentrale in #pve-gruppensuche
# ---------------------------------------------------------------------------

def level_wizard_state(user_id):
    return {
        "owner": user_id, "area": None, "range": None,
        "day": None, "hour": "20", "minute": "00", "note": "",
        "published": False, "message_url": None,
    }


def level_wizard_embed(state, step=1, notice=None):
    if step == 1:
        explanation = (
            "Such dir dein **Levelgebiet** und einen passenden **Levelbereich** aus. "
            "Bei Bedarf kannst du ein eigenes Gebiet oder eine Notiz eintragen."
        )
    else:
        explanation = (
            "Wähle den **Tag**, die **Stunde** und die **Minuten**. "
            "Erst mit **Levelgruppe veröffentlichen** wird dein Termin für alle sichtbar."
        )
    embed = discord.Embed(
        title=f"🌿 Levelgruppe planen · Schritt {step}/2",
        description=explanation,
        colour=discord.Colour.green())
    embed.add_field(
        name="🌍 Levelgebiet",
        value=state["area"] or "*Bitte auswählen*",
        inline=False)
    current_range = state["range"]
    embed.add_field(
        name="🎚️ Levelbereich",
        value=(current_range.replace(":", "–") if current_range else "*Bitte auswählen*"),
        inline=True)
    day = state["day"]
    formatted = (datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m.%Y")
                 if day else "*Bitte auswählen*")
    embed.add_field(name="📅 Tag", value=formatted, inline=True)
    embed.add_field(
        name="🕗 Uhrzeit", value=state["hour"] + ":" + state["minute"] + " Uhr",
        inline=True)
    if state["note"]:
        embed.add_field(name="📝 Notiz", value=state["note"][:160], inline=False)
    if notice:
        embed.add_field(name="Hinweis", value=notice[:600], inline=False)
    embed.set_footer(text="Privater Assistent • Levelgruppengröße: 5 Spieler")
    return embed


class LevelWizardSelect(discord.ui.Select):
    def __init__(self, state, field, options, placeholder, row):
        super().__init__(
            placeholder=placeholder,
            options=options,
            min_values=1, max_values=1, row=row)
        self.state = state
        self.field = field

    async def callback(self, interaction):
        self.state[self.field] = self.values[0]
        step = 1 if self.field in ("area", "range") else 2
        await interaction.response.edit_message(
            embed=level_wizard_embed(self.state, step),
            view=LevelWizardOne(self.state) if step == 1 else LevelWizardTwo(self.state))


class LevelPrivateWizard(discord.ui.View):
    def __init__(self, state):
        super().__init__(timeout=600)
        self.state = state

    async def interaction_check(self, interaction):
        if interaction.user.id == self.state["owner"]:
            return True
        await interaction.response.send_message(
            "Diese Auswahl gehört jemand anderem. Bitte öffne deinen eigenen Level-Planer.",
            ephemeral=True)
        return False


class LevelCustomZoneModal(discord.ui.Modal, title="Eigenes Levelgebiet & Hinweis"):
    area = discord.ui.TextInput(
        label="Gebiet / Treffpunkt", min_length=2, max_length=90,
        placeholder="Zum Beispiel eine Questreihe im Brachland")
    note = discord.ui.TextInput(
        label="Zusätzlicher Hinweis (optional)", required=False,
        max_length=160, style=discord.TextStyle.paragraph,
        placeholder="Gemeinsam Questen, Elitequest, Treffpunkt ...")

    def __init__(self, state):
        super().__init__()
        self.state = state

    async def on_submit(self, interaction):
        if interaction.user.id != self.state["owner"]:
            return await interaction.response.send_message(
                "Diese Levelgruppe gehört dir nicht.", ephemeral=True)
        self.state["area"] = str(self.area.value).strip()
        self.state["note"] = str(self.note.value or "").strip()
        await interaction.response.send_message(
            embed=level_wizard_embed(self.state, 1),
            view=LevelWizardOne(self.state),
            ephemeral=True)


class LevelWizardOne(LevelPrivateWizard):
    def __init__(self, state):
        super().__init__(state)
        self.add_item(LevelWizardSelect(
            state, "area",
            [discord.SelectOption(
                label=name, value=name,
                default=(state["area"] == name))
                for name in LEVEL_AREAS],
            "🌍 Levelgebiet wählen", row=0))
        self.add_item(LevelWizardSelect(
            state, "range",
            [discord.SelectOption(
                label=("Alle Level" if (low, high) == (1, 60)
                       else f"Level {low}–{high}"),
                value=f"{low}:{high}",
                default=(state["range"] == f"{low}:{high}"))
                for low, high in LEVEL_RANGES],
            "🎚️ Levelbereich wählen", row=1))

    @discord.ui.button(label="Eigenes Gebiet / Notiz", emoji="✏️",
                       style=discord.ButtonStyle.secondary, row=2)
    async def custom(self, interaction, button):
        await interaction.response.send_modal(LevelCustomZoneModal(self.state))

    @discord.ui.button(label="Weiter zum Termin", emoji="➡️",
                       style=discord.ButtonStyle.success, row=2)
    async def next(self, interaction, button):
        if not self.state["area"] or not self.state["range"]:
            return await interaction.response.send_message(
                "Bitte zuerst Levelgebiet und Levelbereich auswählen.",
                ephemeral=True)
        await interaction.response.edit_message(
            embed=level_wizard_embed(self.state, 2),
            view=LevelWizardTwo(self.state))


class LevelWizardTwo(LevelPrivateWizard):
    def __init__(self, state):
        super().__init__(state)
        today = berlin_now().date()
        self.add_item(LevelWizardSelect(
            state, "day",
            [discord.SelectOption(
                label=(("Heute" if ix == 0 else
                        "Morgen" if ix == 1 else
                        "Übermorgen" if ix == 2 else
                        WEEKDAY_DE[(today + timedelta(days=ix)).weekday()])
                       + f" · {(today + timedelta(days=ix)):%d.%m.%Y}"),
                value=(today + timedelta(days=ix)).isoformat(),
                default=(state["day"] == (today + timedelta(days=ix)).isoformat()))
                for ix in range(21)],
            "📅 Datum auswählen", row=0))
        self.add_item(LevelWizardSelect(
            state, "hour",
            [discord.SelectOption(
                label=f"{h:02d}:00 Uhr", value=f"{h:02d}",
                default=(state["hour"] == f"{h:02d}"))
                for h in range(24)],
            "🕗 Stunde", row=1))
        self.add_item(LevelWizardSelect(
            state, "minute",
            [discord.SelectOption(
                label=f"{m:02d} Minuten", value=f"{m:02d}",
                default=(state["minute"] == f"{m:02d}"))
                for m in (0, 15, 30, 45)],
            "⏱️ Minuten", row=2))

    @discord.ui.button(label="Zurück", emoji="⬅️",
                       style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            embed=level_wizard_embed(self.state, 1),
            view=LevelWizardOne(self.state))

    @discord.ui.button(label="Levelgruppe veröffentlichen", emoji="✅",
                       style=discord.ButtonStyle.success, row=3)
    async def publish(self, interaction, button):
        state = self.state
        if state["published"]:
            return await interaction.response.send_message(
                "Bereits veröffentlicht: " + (state["message_url"] or ""),
                ephemeral=True)
        if not all(state.get(item) for item in ("area", "range", "day")):
            return await interaction.response.send_message(
                "Bitte Gebiet, Levelbereich und Tag auswählen.", ephemeral=True)
        try:
            low, high = map(int, state["range"].split(":"))
            when, display = parse_plan_time(
                state["day"], state["hour"] + ":" + state["minute"])
        except (ValueError, TypeError) as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        async with level_lock(-interaction.user.id):
            if state["published"]:
                return await interaction.followup.send(
                    "Bereits veröffentlicht: " + (state["message_url"] or ""),
                    ephemeral=True)
            try:
                message, group_id = await publish_level_group(
                    interaction.guild, interaction.user.id,
                    state["area"], low, high, when, display, state["note"])
            except (discord.HTTPException, ValueError):
                logging.exception("Levelgruppe konnte nicht gepostet werden")
                return await interaction.followup.send(
                    "Levelgruppe konnte nicht veröffentlicht werden. "
                    "Bitte Bot-Berechtigungen im Kanal #pve-gruppensuche prüfen.",
                    ephemeral=True)
            state["published"] = True
            state["message_url"] = message.jump_url
        await interaction.followup.send(
            f"✅ **Levelgruppe #{group_id} veröffentlicht!**\n"
            f"🌍 {discord.utils.escape_markdown(state['area'])} · "
            f"Level {low}–{high}\n📅 {display}\n"
            f"[Zur Anmeldung]({message.jump_url})",
            ephemeral=True)




# ---------------------------------------------------------------------------
# Levelgruppen-Dashboard: nach einem Neustart automatisch wieder verfügbar.
# ---------------------------------------------------------------------------

def level_dashboard_embed():
    embed = discord.Embed(
        title="🌿 CORPSEGRINDER · LEVELGRUPPEN",
        description=(
            "**Gemeinsam leveln macht mehr Spaß!**\n\n"
            "Plane deine nächsten Quests, Elitequests oder einen ganzen Levelabend. "
            "Du wählst Gebiet, Levelbereich und Uhrzeit; Mitspieler melden sich "
            "mit einem Klick an. Auch Besucher unserer Horde-Community sind willkommen!"
        ),
        colour=discord.Colour.green())
    embed.add_field(
        name="🌍 Gebiet & Level",
        value="Durotar, Brachland, Schlingendorntal und viele weitere Gebiete "
              "– oder ein eigenes Ziel mit Hinweis auswählen.",
        inline=False)
    embed.add_field(
        name="📅 Dein Termin",
        value="Datum und Uhrzeit komfortabel über Dropdowns auswählen.",
        inline=False)
    embed.add_field(
        name="👥 Bis zu 5 Spieler",
        value="Einfach **Dabei sein** oder **Abmelden** anklicken. "
              "Keine feste Tank-/Heiler-/DD-Aufteilung notwendig.",
        inline=False)
    embed.set_footer(text="Corpsegrinder • Levelgruppen • " + LEVEL_PANEL_MARKER)
    return embed


def list_level_groups_embed(user_id=None):
    cutoff = int(datetime.now(timezone.utc).timestamp()) - 3600
    if user_id is None:
        entries = db.execute(
            "SELECT id,area,min_level,max_level,start_utc,channel,message "
            "FROM level_groups WHERE guild=? AND status='open' AND start_utc > ? "
            "ORDER BY start_utc LIMIT 8",
            (GUILD_ID, cutoff)).fetchall()
    else:
        entries = db.execute(
            "SELECT g.id,g.area,g.min_level,g.max_level,g.start_utc,g.channel,g.message "
            "FROM level_groups g WHERE g.guild=? AND g.status='open' AND g.start_utc > ? "
            "AND (g.owner=? OR EXISTS (SELECT 1 FROM level_signups l "
            "WHERE l.group_id=g.id AND l.user=?)) ORDER BY g.start_utc LIMIT 8",
            (GUILD_ID, cutoff, user_id, user_id)).fetchall()
    embed = discord.Embed(
        title="🌿 Meine Levelgruppen" if user_id else "🌿 Nächste Levelgruppen",
        colour=discord.Colour.green())
    if not entries:
        embed.description = (
            "Hier gibt es noch keine anstehenden Levelgruppen. "
            "Starte die erste mit **🌿 Levelgruppe planen**!")
        return embed
    for group_id, area, low, high, start, chan, msg in entries:
        roster = len(level_players(group_id))
        jump_url = (f"https://discord.com/channels/{GUILD_ID}/{chan}/{msg}"
                    if chan and msg else None)
        content = f"🎚️ Level {low}–{high} · 👥 {roster}/5\n🗓️ <t:{start}:f>"
        if jump_url:
            content += f"\n[Zur Gruppenkarte]({jump_url})"
        embed.add_field(
            name=f"🌍 #{group_id} · {discord.utils.escape_markdown(area[:65])}",
            value=content, inline=False)
    embed.set_footer(text="Öffne eine Karte und melde dich an.")
    return embed


class LevelDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Levelgruppe planen", emoji="🌿",
                       style=discord.ButtonStyle.success,
                       custom_id="corpse_level_dashboard_new_v111")
    async def new_level_group(self, interaction, button):
        if not allowed(interaction):
            return await interaction.response.send_message(
                "Nur auf Corpsegrinder verfügbar.", ephemeral=True)
        state = level_wizard_state(interaction.user.id)
        await interaction.response.send_message(
            embed=level_wizard_embed(state, 1),
            view=LevelWizardOne(state), ephemeral=True)

    @discord.ui.button(label="Leveltermine", emoji="📅",
                       style=discord.ButtonStyle.primary,
                       custom_id="corpse_level_dashboard_upcoming_v111")
    async def level_dates(self, interaction, button):
        if not allowed(interaction):
            return await interaction.response.send_message(
                "Nur auf Corpsegrinder verfügbar.", ephemeral=True)
        await interaction.response.send_message(
            embed=list_level_groups_embed(), ephemeral=True)

    @discord.ui.button(label="Meine Levelgruppen", emoji="📋",
                       style=discord.ButtonStyle.secondary,
                       custom_id="corpse_level_dashboard_mine_v111")
    async def mine(self, interaction, button):
        if not allowed(interaction):
            return await interaction.response.send_message(
                "Nur auf Corpsegrinder verfügbar.", ephemeral=True)
        await interaction.response.send_message(
            embed=list_level_groups_embed(interaction.user.id), ephemeral=True)


async def ensure_level_dashboard(guild):
    target = channel(guild, "pve-gruppensuche")
    if not isinstance(target, discord.TextChannel):
        logging.warning("Levelgruppen-Dashboard: #pve-gruppensuche fehlt")
        return None, False
    post = None
    old_id = setting(LEVEL_PANEL_SETTING)
    if old_id:
        try:
            existing = await target.fetch_message(int(old_id))
            if existing.author.id == bot.user.id and any(
                    LEVEL_PANEL_MARKER in (item.footer.text or "")
                    for item in existing.embeds):
                post = existing
        except (discord.HTTPException, ValueError):
            pass
    if post is None:
        try:
            async for existing in target.history(limit=80):
                if existing.author.id == bot.user.id and any(
                        LEVEL_PANEL_MARKER in (item.footer.text or "")
                        for item in existing.embeds):
                    post = existing
                    break
        except discord.HTTPException:
            logging.warning("Levelgruppen-Dashboard: Kanalhistorie nicht lesbar")
    if post is None:
        post = await target.send(
            embed=level_dashboard_embed(), view=LevelDashboardView(),
            allowed_mentions=discord.AllowedMentions.none())
    else:
        await post.edit(
            embed=level_dashboard_embed(), view=LevelDashboardView())
    save_setting(LEVEL_PANEL_SETTING, post.id)
    if (not target.topic or target.topic.startswith(
            "🏰 Dungeon planen und Termine finden: ")):
        try:
            await target.edit(
                topic="🌿 Levelgruppen planen und Mitspieler finden: " + post.jump_url,
                reason="Corpsegrinder Levelgruppen-Dashboard")
        except discord.HTTPException:
            logging.warning("Kanalthema für Levelgruppen konnte nicht angepasst werden")
    pinned = post.pinned
    if not pinned:
        try:
            await post.pin(reason="Corpsegrinder Levelgruppen-Steuerzentrale")
            pinned = True
        except discord.Forbidden:
            logging.warning(
                "Levelgruppen-Bedienfeld gepostet, aber nicht angeheftet. "
                "Recht 'Nachrichten verwalten' fehlt.")
        except discord.HTTPException:
            logging.exception("Levelgruppen-Bedienfeld konnte nicht angeheftet werden")
    return post, pinned


async def ensure_level_dashboard_on_start():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    try:
        await ensure_level_dashboard(guild)
    except discord.HTTPException:
        logging.exception("Automatisches Levelgruppen-Dashboard fehlgeschlagen")


@bot.tree.command(name="levelpanel",
                  description="Levelgruppen-Steuerzentrale aktualisieren (Admin)",
                  guild=SERVER)
async def install_level_dashboard(interaction: discord.Interaction):
    if not admin(interaction):
        return await answer(interaction, "Nur Administratoren.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        post, pinned = await ensure_level_dashboard(interaction.guild)
    except discord.HTTPException:
        logging.exception("Levelgruppen-Dashboard")
        return await interaction.followup.send(
            "Das Panel konnte nicht erstellt werden. "
            "Bitte Bot-Rechte in #pve-gruppensuche prüfen.", ephemeral=True)
    if post is None:
        return await interaction.followup.send(
            "Der Textkanal #pve-gruppensuche wurde nicht gefunden.", ephemeral=True)
    await interaction.followup.send(
        f"🌿 **Levelgruppen-Panel**: {post.jump_url}\n"
        + ("✅ Angepinnt" if pinned else "⚠️ Noch nicht angepinnt – bitte selbst anpinnen."),
        ephemeral=True)


@bot.tree.command(name="leveltermin_absagen",
                  description="Eigene Levelgruppe absagen (oder als Administrator)",
                  guild=SERVER)
async def cancel_level_group(interaction: discord.Interaction, termin_id: int):
    if not allowed(interaction):
        return await answer(interaction, "Nur auf Corpsegrinder verfügbar.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    async with level_lock(termin_id):
        group = level_record(termin_id)
        if not group:
            return await interaction.followup.send(
                "Leveltermin nicht gefunden.", ephemeral=True)
        if group[2] != interaction.user.id and not admin(interaction):
            return await interaction.followup.send(
                "Nur Organisator oder Administrator kann die Levelgruppe absagen.",
                ephemeral=True)
        if group[11] == "cancelled":
            return await interaction.followup.send(
                "Termin ist bereits abgesagt.", ephemeral=True)
        db.execute("UPDATE level_groups SET status='cancelled' WHERE id=?", (termin_id,))
        db.commit()
        try:
            await refresh_level_card(level_record(termin_id))
            result = f"❌ Levelgruppe #{termin_id} abgesagt."
        except discord.HTTPException:
            logging.exception("Abgesagte Levelgruppe konnte nicht aktualisiert werden")
            result = "Leveltermin abgesagt; die Gruppenkarte wurde noch nicht aktualisiert."
        await interaction.followup.send(result, ephemeral=True)


@bot.tree.command(name="leveltermin_verschieben",
                  description="Datum/Uhrzeit einer eigenen Levelgruppe ändern",
                  guild=SERVER)
@app_commands.describe(
    termin_id="Nummer der Levelgruppenkarte",
    tag="morgen, übermorgen oder TT.MM.JJJJ",
    uhrzeit="Neue Uhrzeit, z. B. 20:30")
async def reschedule_level_group(
        interaction: discord.Interaction, termin_id: int, tag: str, uhrzeit: str):
    if not allowed(interaction):
        return await answer(interaction, "Nur auf Corpsegrinder verfügbar.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    async with level_lock(termin_id):
        group = level_record(termin_id)
        if not group or group[11] == "cancelled":
            return await interaction.followup.send(
                "Leveltermin ist nicht vorhanden oder abgesagt.", ephemeral=True)
        if group[2] != interaction.user.id and not admin(interaction):
            return await interaction.followup.send(
                "Nur Organisator oder Administrator kann verschieben.", ephemeral=True)
        try:
            when, display = parse_plan_time(tag, uhrzeit)
        except ValueError as exc:
            return await interaction.followup.send(str(exc), ephemeral=True)
        db.execute(
            "UPDATE level_groups SET start_utc=?,display_time=? WHERE id=?",
            (when, display, termin_id))
        db.commit()
        try:
            await refresh_level_card(level_record(termin_id))
            result = "✅ Leveltermin verschoben auf " + display + ". Mitglieder bleiben angemeldet."
        except discord.HTTPException:
            result = "Termin geändert, aber die Gruppenkarte konnte nicht aktualisiert werden."
        await interaction.followup.send(result, ephemeral=True)




# --- Corpsegrinder 1.0.12: zeitgesteuerte Abenteuer --------------------------
# Der Prozess läuft im vorhandenen Discord-Worker (kein neuer Supervisor nötig).
# Zeitstempel bleiben in UTC; die Darstellung erfolgt lokal in Deutschland.

EVENT_KINDS = ("dungeon", "level")
EVENT_RETIRE_SECONDS = 3600    # +1 Stunde: Karte als abgelaufen kennzeichnen.
EVENT_DELETE_DELAY = 300      # +5 Minuten: Karten-Nachricht endgültig entfernen.
EVENT_REMIND_SECONDS = 900    # -15 Minuten: private Erinnerung/Voice.
VOICE_UNUSED_TTL = 3600      # Leerer, nie benutzter Raum: 1h Schonfrist.
_event_scheduler_task = None
_event_panel_locks = {}


def event_meta(kind, group_id, create=True):
    if kind not in EVENT_KINDS:
        raise ValueError("Unbekannte Gruppenart")
    if create:
        db.execute(
            "INSERT OR IGNORE INTO event_meta(kind,group_id) VALUES (?,?)",
            (kind, group_id))
        db.commit()
    return db.execute(
        "SELECT kind,group_id,reminder_sent,full_prev,voice_id,voice_seen,"
        "voice_created,expired_at,archived_at FROM event_meta "
        "WHERE kind=? AND group_id=?", (kind, group_id)).fetchone()


def event_record(kind, group_id):
    return load_plan(group_id) if kind == "dungeon" else level_record(group_id)


def event_start(kind, group):
    return group[4] if kind == "dungeon" else group[6]


def event_status(kind, group):
    return group[9] if kind == "dungeon" else group[11]


def event_owner(group):
    return group[2]


def event_participants(kind, group_id):
    return ([user_id for user_id, _ in plan_members(group_id)]
            if kind == "dungeon" else level_players(group_id))


def event_is_full(kind, group_id):
    if kind == "dungeon":
        counts = plan_counts(group_id)
        return all(counts.get(r, 0) == PLAN_LIMITS[r] for r in PLAN_ROLES)
    return len(level_players(group_id)) == 5


def event_title(kind, group):
    return group[3]


def event_channel_id(kind, group):
    return group[7] if kind == "dungeon" else group[9]


def event_message_id(kind, group):
    return group[8] if kind == "dungeon" else group[10]


def event_link(kind, group):
    c, m = event_channel_id(kind, group), event_message_id(kind, group)
    if c and m:
        return f"https://discord.com/channels/{GUILD_ID}/{c}/{m}"
    return None


async def refresh_event_card(kind, group):
    if not event_message_id(kind, group):
        return
    if kind == "dungeon":
        await refresh_planned_message(group)
    else:
        await refresh_level_card(group)


async def refresh_event_dashboard(kind):
    lock = _event_panel_locks.setdefault(kind, asyncio.Lock())
    async with lock:
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            return
        try:
            if kind == "dungeon":
                await ensure_planner_dashboard(guild)
            else:
                await ensure_level_dashboard(guild)
        except discord.HTTPException:
            logging.exception("Dynamisches %s-Panel konnte nicht aktualisiert werden", kind)


async def event_dm(user_id, title, body, kind, group, voice_id=None):
    if not notifications_enabled(user_id):
        return
    try:
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)
        embed = discord.Embed(
            title=title,
            description=body,
            colour=(discord.Colour.dark_red() if kind == "dungeon"
                    else discord.Colour.green()))
        embed.add_field(
            name="🗓️ Gruppenstart",
            value=f"<t:{event_start(kind, group)}:F>",
            inline=False)
        url = event_link(kind, group)
        if url:
            embed.add_field(name="📜 Zur Anmeldung", value=f"[Gruppenkarte öffnen]({url})", inline=False)
        if voice_id:
            embed.add_field(
                name="🔊 Sprachkanal",
                value=f"[Zum Treffpunkt](https://discord.com/channels/{GUILD_ID}/{voice_id})",
                inline=False)
        await user.send(embed=embed)
    except (discord.Forbidden, discord.NotFound):
        logging.info("DM an %s nicht möglich (Privatsphäre)", user_id)
    except discord.HTTPException:
        logging.exception("Discord-DM an %s fehlgeschlagen", user_id)


async def event_changed(kind, group_id):
    group = event_record(kind, group_id)
    if not group:
        return
    metadata = event_meta(kind, group_id)
    is_full = event_is_full(kind, group_id)
    was_full = bool(metadata[3])
    db.execute(
        "UPDATE event_meta SET full_prev=? WHERE kind=? AND group_id=?",
        (int(is_full), kind, group_id))
    db.commit()
    if (kind == "dungeon" and is_full and not was_full
            and event_status(kind, group) == "open"):
        for user_id in event_participants(kind, group_id):
            background(event_dm(
                user_id, "🎉 Eure Dungeon-Gruppe ist vollständig!",
                f"**{discord.utils.escape_markdown(event_title(kind, group))}** "
                "ist mit **1 Tank, 1 Heiler und 3 DD** vollständig. "
                "15 Minuten vor dem Termin folgt eure Erinnerung.",
                kind, group, metadata[4]))
    await refresh_event_dashboard(kind)
    # Falls eine Gruppe erst kurz vor Start voll wird, direkt den Treffpunkt öffnen.
    when = event_start(kind, group)
    now = int(datetime.now(timezone.utc).timestamp())
    if is_full and when-900 <= now < when:
        background(process_scheduled_event(kind, group_id))


async def finish_scheduled_group(interaction, kind, group_id):
    if not allowed(interaction):
        return await answer(interaction, "Nur auf Corpsegrinder verfügbar.")
    await interaction.response.defer(ephemeral=True, thinking=True)
    lock = plan_lock(group_id) if kind == "dungeon" else level_lock(group_id)
    async with lock:
        group = event_record(kind, group_id)
        if not group or event_status(kind, group) != "open":
            return await interaction.followup.send(
                "Die Gruppe ist nicht mehr aktiv.", ephemeral=True)
        if (interaction.user.id != event_owner(group) and not admin(interaction)):
            return await interaction.followup.send(
                "Nur der Organisator oder ein Administrator darf abschließen.",
                ephemeral=True)
        table = "planned_groups" if kind == "dungeon" else "level_groups"
        db.execute(f"UPDATE {table} SET status='completed' WHERE id=? AND guild=?",
                   (group_id, GUILD_ID))
        event_meta(kind, group_id)
        db.execute(
            "UPDATE event_meta SET expired_at=? WHERE kind=? AND group_id=?",
            (int(datetime.now(timezone.utc).timestamp()), kind, group_id))
        db.commit()
        try:
            await refresh_event_card(kind, event_record(kind, group_id))
        except discord.HTTPException:
            logging.exception("Abgeschlossene %s-Gruppe konnte nicht aktualisiert werden",kind)
        await refresh_event_dashboard(kind)
        await interaction.followup.send(
            "✅ Gruppe abgeschlossen und aus den aktiven Übersichten entfernt. "
            "Die Karte wird in fünf Minuten gelöscht; euer Sprachkanal bleibt "
            "bestehen, solange jemand darin ist.",
            ephemeral=True)


async def create_scheduled_voice(kind, group):
    group_id = group[0]
    metadata = event_meta(kind, group_id)
    if metadata[4]:
        active = bot.get_channel(metadata[4])
        if isinstance(active, discord.VoiceChannel):
            return active.id
    guild = bot.get_guild(GUILD_ID)
    source = channel(guild, "dungeons" if kind == "dungeon" else "pve-gruppensuche") if guild else None
    category = source.category if source else None
    if category is None:
        logging.warning("%s-Gruppe #%s: keine PvE-Kategorie für Sprachkanal",kind,group_id)
        return None
    name = event_title(kind, group)
    short_time = datetime.fromtimestamp(
        event_start(kind, group), timezone.utc).astimezone(berlin_now().tzinfo).strftime("%H:%M")
    if kind == "dungeon":
        voice_name = f"🏰 {name} · {short_time}"
    else:
        voice_name = f"🌿 {name} {group[4]}–{group[5]} · {short_time}"
    voice = await category.create_voice_channel(
        voice_name[:100], user_limit=5,
        reason=f"Corpsegrinder Termin #{group_id}: automatischer Treffpunkt")
    db.execute(
        "UPDATE event_meta SET voice_id=?,voice_seen=0,voice_created=? "
        "WHERE kind=? AND group_id=?",
        (voice.id, int(datetime.now(timezone.utc).timestamp()), kind,group_id))
    db.commit()
    save_setting("temp_"+str(voice.id),"1")
    try:
        await refresh_event_card(kind, event_record(kind, group_id))
    except discord.HTTPException:
        logging.warning("Sprachkanal in Gruppenkarte noch nicht angezeigt")
    return voice.id


def scheduled_voice_details(channel_id):
    return db.execute(
        "SELECT kind,group_id,voice_seen,voice_created FROM event_meta "
        "WHERE voice_id=?", (channel_id,)).fetchone()


async def process_scheduled_event(kind, group_id):
    group = event_record(kind,group_id)
    if not group:
        return
    status = event_status(kind, group)
    now = int(datetime.now(timezone.utc).timestamp())
    start = event_start(kind, group)
    metadata = event_meta(kind, group_id)
    if status == "open":
        if now >= start + EVENT_RETIRE_SECONDS:
            table = "planned_groups" if kind == "dungeon" else "level_groups"
            db.execute(
                f"UPDATE {table} SET status='expired' WHERE id=? AND guild=?",
                (group_id, GUILD_ID))
            db.execute(
                "UPDATE event_meta SET expired_at=? WHERE kind=? AND group_id=?",
                (now, kind, group_id))
            db.commit()
            try:
                await refresh_event_card(kind, event_record(kind,group_id))
            except (discord.HTTPException, ValueError):
                logging.warning("Abgelaufene Gruppenkarte %s/%s konnte nicht markiert werden",kind,group_id)
            await refresh_event_dashboard(kind)
            return
        if now >= start-EVENT_REMIND_SECONDS and now < start:
            voice_id = metadata[4]
            if event_is_full(kind,group_id):
                if not voice_id or not isinstance(bot.get_channel(voice_id),discord.VoiceChannel):
                    voice_id = await create_scheduled_voice(kind,group)
            for user_id in event_participants(kind,group_id):
                # Pro Spieler nur eine Erinnerung (auch nach Neustart).
                cursor = db.execute(
                    "INSERT OR IGNORE INTO event_reminder_deliveries(kind,group_id,user_id) "
                    "VALUES (?,?,?)", (kind,group_id,user_id))
                db.commit()
                if cursor.rowcount:
                    background(event_dm(
                        user_id, "🔔 Dein Abenteuer startet in Kürze!",
                        f"**{discord.utils.escape_markdown(event_title(kind,group))}** "
                        "beginnt um **<t:"+str(start)+":t>**. "
                        "Dein Corpsegrinder-Treffpunkt ist bereit!",
                        kind, group, voice_id))
        elif now >= start:
            # Nie nach dem Start eine verspätete Erinnerung senden.
            db.execute(
                "UPDATE event_meta SET reminder_sent=1 WHERE kind=? AND group_id=?",
                (kind,group_id))
            db.commit()
    elif status in ("expired","completed","cancelled"):
        done_at = metadata[7]
        if done_at is None:
            db.execute(
                "UPDATE event_meta SET expired_at=? WHERE kind=? AND group_id=?",
                (now,kind,group_id))
            db.commit()
            done_at=now
        if now < done_at+EVENT_DELETE_DELAY:
            return
        channel_id = event_channel_id(kind,group)
        message_id = event_message_id(kind,group)
        if channel_id and message_id:
            try:
                target = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
                post = await target.fetch_message(message_id)
                if post.author.id == bot.user.id:
                    await post.delete(reason="Corpsegrinder Gruppenkarte abgelaufen")
            except discord.NotFound:
                pass
            except discord.HTTPException:
                logging.exception("Kann abgelaufene Karte %s/%s nicht löschen",kind,group_id)
                return
        table = "planned_groups" if kind == "dungeon" else "level_groups"
        db.execute(f"UPDATE {table} SET status='archived' WHERE id=? AND guild=?",
                   (group_id,GUILD_ID))
        db.execute(
            "UPDATE event_meta SET archived_at=? WHERE kind=? AND group_id=?",
            (now,kind,group_id))
        db.commit()
        await refresh_event_dashboard(kind)


async def event_scheduler_loop():
    # Neustart-sicher: Ereigniszustand, Erinnerung und Kanal werden in SQLite gespeichert.
    while not bot.is_closed():
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            for kind,table in (("dungeon","planned_groups"),("level","level_groups")):
                time_col = "start_utc"
                rows = db.execute(
                    f"SELECT id FROM {table} WHERE guild=? "
                    "AND status IN ('open','expired','cancelled','completed') "
                    f"AND ({time_col}<=? OR status!='open') ORDER BY id",
                    (GUILD_ID,now+EVENT_REMIND_SECONDS)).fetchall()
                for (group_id,) in rows:
                    try:
                        await process_scheduled_event(kind, group_id)
                    except (discord.HTTPException, ValueError):
                        logging.exception("Event-Timer %s/%s gescheitert",kind,group_id)
            # Erst genutzte Sprachräume sofort nach Leerwerden löschen;
            # bis dahin noch ungenutzte Räume erst nach Schonfrist.
            rows = db.execute(
                "SELECT voice_id FROM event_meta WHERE voice_id IS NOT NULL").fetchall()
            for (voice_id,) in rows:
                target = bot.get_channel(voice_id)
                if target is None:
                    forget_temp_channel(voice_id)
                    db.execute("UPDATE event_meta SET voice_id=NULL WHERE voice_id=?", (voice_id,))
                    db.commit()
                elif target.members:
                    db.execute("UPDATE event_meta SET voice_seen=1 WHERE voice_id=?",
                               (voice_id,))
                    db.commit()
                else:
                    background(delete_temp_if_empty(voice_id, delay=0))
        except Exception:
            logging.exception("Corpsegrinder Zeitsteuerung: unerwarteter Fehler")
        await asyncio.sleep(30)


def initialize_scheduler_meta():
    for kind,table in (("dungeon","planned_groups"),("level","level_groups")):
        rows = db.execute(
            f"SELECT id FROM {table} WHERE guild=? AND status='open'",
            (GUILD_ID,)).fetchall()
        for (group_id,) in rows:
            if event_meta(kind,group_id,create=False) is None:
                # Frühere, schon volle Gruppen beim Neustart nicht als neu 'voll' melden.
                db.execute(
                    "INSERT OR IGNORE INTO event_meta(kind,group_id,full_prev) "
                    "VALUES (?,?,?)",
                    (kind,group_id,int(event_is_full(kind,group_id))))
    db.commit()


async def remove_old_guild_category_once():
    """Löscht NUR die explizit abgewählte alte WoW-Gilden-Kategorie."""
    if setting("guild_area_removed_112") == "1":
        return
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    matching = [cat for cat in guild.categories
                if cat.name.upper().strip().endswith("WOW FOREVER | GILDE")]
    if not matching:
        save_setting("guild_area_removed_112","1")
        return
    allowed_names = {"gildenchat","gilden-raids","offiziers-chat"}
    for category in matching:
        present = {x.name.casefold() for x in category.channels}
        if not present.issubset(allowed_names):
            logging.warning(
                "Gilden-Kategorie %s enthält fremde Kanäle: %s – keine Löschung",
                category.name, present-allowed_names)
            return
        # Vorhandene Chatnachrichten werden durch Discord-Kanallöschung unwiederbringlich entfernt.
        try:
            for ch in list(category.channels):
                await ch.delete(reason="Corpsegrinder: alter Gildenbereich auf Nutzerwunsch entfernt")
            await category.delete(reason="Corpsegrinder: gemeinsamer Server ohne Gildentrennung")
        except discord.HTTPException:
            logging.exception("Alte Gildenkategorie konnte nicht vollständig entfernt werden")
            return
    save_setting("guild_area_removed_112","1")


@bot.tree.command(name="erinnerungen",
                  description="Private Gruppen-Erinnerungen und Vollmeldungen ein-/ausschalten",
                  guild=SERVER)
async def toggle_personal_reminders(interaction: discord.Interaction, aktiv: bool):
    if not allowed(interaction):
        return await answer(interaction, "Nur auf Corpsegrinder.")
    db.execute(
        "INSERT OR REPLACE INTO notification_preferences(user_id,enabled) VALUES (?,?)",
        (interaction.user.id,int(aktiv)))
    db.commit()
    await answer(interaction,
                 "🔔 Deine Gruppen-Erinnerungen und Vollmeldungen sind jetzt "
                 + ("**aktiviert**." if aktiv else "**deaktiviert**."))



bot.run(TOKEN, log_handler=None)
