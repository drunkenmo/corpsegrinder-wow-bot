import discord

VERSION = "1.0.11"

# Schlüssel bleiben ohne Emoji, damit die gespeicherten Rollen und Bot-Befehle stabil bleiben.
ROLE_STYLE = {
    "Community": ("🌋 Community", 0x000000, "🌋"),
    "Dungeon-News": ("🏰 Dungeon-News", 0x000000, "🏰"),
    "Raid-News": ("🐉 Raid-News", 0x000000, "🐉"),
    "PvP-News": ("📣 PvP-News", 0x000000, "📣"),
    "Tank": ("🛡️ Tank", 0x3274B5, "🛡️"),
    "Heiler": ("💚 Heiler", 0x32B875, "💚"),
    "DD": ("💥 DD", 0xD85742, "💥"),
    "Krieger": ("⚔️ Krieger", 0xC79C6E, "⚔️"),
    "Schamane": ("🌩️ Schamane", 0x0070DE, "🌩️"),
    "Druide": ("🌿 Druide", 0xFF7D0A, "🌿"),
    "Jäger": ("🏹 Jäger", 0xABD473, "🏹"),
    "Schurke": ("🗡️ Schurke", 0xFFF569, "🗡️"),
    "Magier": ("✨ Magier", 0x69CCF0, "✨"),
    "Priester": ("🌟 Priester", 0xE9E9E9, "🌟"),
    "Hexenmeister": ("🔥 Hexenmeister", 0x9482C9, "🔥"),
    "PvE": ("⚔️ PvE", 0x8795A1, "⚔️"),
    "PvP": ("🏹 PvP", 0xA64A4A, "🏹"),
}

def visual_name(name):
    return ROLE_STYLE[name][0] if name in ROLE_STYLE else name

def welcome_embed():
    embed = discord.Embed(
        title="⚔️ Willkommen bei CORPSEGRINDER!",
        description=(
            "**LOK'TAR OGAR – FÜR DIE HORDE!**\n\n"
            "Ob Gildenmitglied oder Community-Gast: Hier spielen wir gemeinsam **WoW Forever**. "
            "Du bist auch ohne Gildenmitgliedschaft willkommen."
        ),
        colour=discord.Colour.dark_red())
    embed.add_field(name="🎭 1. Rollen wählen",
                    value="Gehe zu **#rollenwahl**. Wähle PvE/PvP, Tank/Heiler/DD und deine Klassen.", inline=False)
    embed.add_field(name="🛡️ 2. Mitspieler finden",
                    value="Nutze **#pve-gruppensuche** oder **#pvp-gruppensuche**.", inline=False)
    embed.add_field(name="🍻 3. Gemeinsam Spaß haben",
                    value="Bleib respektvoll, vermeide Spam und hilf anderen Horde-Spielern.", inline=False)
    embed.set_footer(text="Corpsegrinder • Willkommen • corpsegrinder:welcome")
    return embed

def announcement_intro_embed():
    embed = discord.Embed(
        title="📢 Neues aus Corpsegrinder",
        description="Hier findest du wichtige Informationen rund um unsere Horde-Community.",
        colour=discord.Colour.orange())
    embed.add_field(
        name="Was erscheint hier?",
        value="🐉 Raid- und Eventhinweise\n🏹 Organisierte PvP-Aktionen\n🛠️ Wichtige Bot-Änderungen\n📜 Mitteilungen der Serverleitung",
        inline=False)
    embed.add_field(name="Für Neuigkeiten anmelden",
                    value="Im Kanal **#rollenwahl** kannst du Raid-News, Dungeon-News und PvP-News auswählen.",
                    inline=False)
    embed.set_footer(text="Corpsegrinder • Ankündigungen • corpsegrinder:news-intro")
    return embed

def news_embed(title, description, author=None):
    embed = discord.Embed(
        title="📢 " + title[:200],
        description=description[:3500],
        colour=discord.Colour.orange())
    if author is not None:
        embed.set_footer(text="Corpsegrinder • Mitteilung von " + author.display_name[:120])
    return embed

def update_embed():
    embed = discord.Embed(
        title="🛠️ Corpsegrinder Bot – Update " + VERSION,
        description=(
            "**Neue Levelgruppen und Dungeon-Planer am richtigen Platz!**\n\n"
            "🏰 Der Dungeon-Planer erscheint jetzt in **#dungeons**; neue "
            "Dungeon-Termine werden ebenfalls dort veröffentlicht.\n\n"
            "🌿 In **#pve-gruppensuche** gibt es einen eigenen Levelgruppen-Planer "
            "mit Gebiet, Levelbereich, Datum und Uhrzeit. Mitspieler können sich "
            "mit einem Klick für bis zu fünf Plätze anmelden.\n\n"
            "🔊 Der Ersteller eines temporären PvE-/PvP-Sprachkanals wird automatisch "
            "in seinen Raum verschoben, sofern der Bot **Mitglieder verschieben** darf."
        ),
        colour=discord.Colour.green())
    embed.set_footer(text="Corpsegrinder • Bot-Version " + VERSION)
    return embed
