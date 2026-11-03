import discord

VERSION = "1.0.21"

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

# This single guide is updated on each Bot release/restart. New features only
# require one additional entry here; no extra Discord messages are created.
WELCOME_FEATURES = (
    ("🎭 ERSTE SCHRITTE", (
        ("rollenwahl", "Rollen wählen (PvE/PvP, Tank, Heiler, DD, News) und "
         "den **Ingame-Namen + Klasse** registrieren – ohne Level oder Freigabe"),
        ("allgemein", "Mit der Horde chatten, Fragen stellen und Leute kennenlernen"),
    )),
    ("⚔️ MITSPIELER FINDEN", (
        ("dungeons", "Dungeon-Termine planen, mit Tank/Heiler/DD anmelden, "
         "einen Charakter auswählen und Erinnerungen bekommen"),
        ("pve-gruppensuche", "Gemeinsam leveln und Questgruppen erstellen"),
        ("pvp-gruppensuche", "Mitspieler für PvP finden"),
        ("raids-und-termine", "Raid- und Community-Termine im Blick behalten"),
    )),
    ("📰 INFORMATION & GUIDES", (
        ("ankündigungen", "Wichtige Meldungen von der Serverleitung"),
        ("forever-news", "WoW-Forever-News direkt auf Deutsch lesen"),
        ("addons", "Addon-Empfehlungen und neue Forever-Versionen finden"),
        ("pve-guides", "Tipps und Hilfen für PvE entdecken"),
    )),
    ("🎮 MEHR AUS DER COMMUNITY", (
        ("charaktere-und-berufe", "Über Charaktere und Berufe sprechen"),
        ("handel-und-crafting", "Handel, Herstellung und Materialien"),
        ("screenshots", "Eure WoW-Momente teilen"),
    )),
)


def welcome_embed(guild=None, extra_tip=""):
    """Maintain one comprehensive #willkommen guide across all Bot versions."""
    def channel_link(name):
        if guild is None:
            return "#" + name
        target = next(
            (c for c in getattr(guild, "text_channels", ())
             if c.name == name), None)
        return target.mention if target is not None else "#" + name

    embed = discord.Embed(
        title="🌋 CORPSEGRINDER · WILLKOMMEN BEI DER HORDE!",
        description=(
            "**Alte Säcke. Kaltes Bier. Seit 2004.** 🍻\n\n"
            "Schön, dass du dabei bist! Hier treffen sich alte Weggefährten "
            "und neue WoW-Forever-Spieler. Du brauchst keine "
            "Gildenmitgliedschaft und keine Ingame-Verifizierung.\n\n"
            "**Dein Einstieg in 3 Schritten:**\n"
            f"**1.** In {channel_link('rollenwahl')} deine Rollen auswählen.\n"
            "**2.** Dort **Charakter registrieren** anklicken und "
            "**Ingame-Namen + Klasse** eintragen (Hauptcharakter und Twinks möglich).\n"
            f"**3.** In {channel_link('allgemein')} Hallo sagen oder "
            f"in {channel_link('dungeons')} direkt Mitspieler suchen.\n\n"
            "📌 **Diese Übersicht bleibt aktuell**, wenn wir neue Bot-Funktionen "
            "hinzufügen. Du musst nicht nach neuen Anleitungen suchen."
        ),
        colour=discord.Colour.from_rgb(153,46,29))
    embed.set_image(
        url="https://raw.githubusercontent.com/drunkenmo/corpsegrinder-wow-bot/main/assets/welcome.png")
    for heading, entries in WELCOME_FEATURES:
        lines = [
            f"• {channel_link(name)} – {description}"
            for name, description in entries
        ]
        embed.add_field(name=heading, value="\n".join(lines), inline=False)
    embed.add_field(
        name="🔊 SPRACHCHAT & SPIELERNAMEN",
        value=(
            "Unter **⚔️ WOW FOREVER | PVE** und **🏹 WOW FOREVER | PVP** "
            "findest du feste Sprachkanäle und Möglichkeiten, "
            "temporäre Gruppenräume zu öffnen.\n"
            "Der Bot kann deinen **Hauptcharakter als Discord-Servernickname** "
            "anzeigen. Das aktivierst du freiwillig in "
            f"{channel_link('rollenwahl')} unter **Meine Charaktere**. "
            "Dann steht der Ingame-Name auch im Sprachchat."
        ), inline=False)
    if extra_tip:
        embed.add_field(
            name="📣 AKTUELLER HINWEIS DER SERVERLEITUNG",
            value=discord.utils.escape_markdown(extra_tip[:650]),
            inline=False)
    embed.set_footer(
        text="Corpsegrinder • Version " + VERSION +
             " • corpsegrinder:welcome")
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
        title="🌋 Corpsegrinder Bot – Update " + VERSION,
        description=(
            "🇩🇪 **Blizzard-Klassenänderungen endlich direkt auf Deutsch!**\n\n"
            "🔵 Im Kanal **#forever-news** stehen bei offiziellen "
            "Entwicklungsnotizen nun direkt die wichtigsten erkannten "
            "Buffs, Nerfs und Zahlen, sortiert nach Klassen.\n"
            "✅ Die Werte stammen aus Blizzards Originalbeiträgen. "
            "Bei unklaren Formulierungen wird nichts erfunden.\n"
            "♻️ Bereits veröffentlichte Bluepost-Karten werden mit "
            "der neuen deutschen Übersicht aktualisiert.\n\n"
            "Die ausführlichen englischen Notizen bleiben als Quelle "
            "verlinkt; es handelt sich um eine geprüfte Auswahl, "
            "nicht um eine vollständige Übersetzung."
        ),
        colour=discord.Colour.gold())
    embed.set_footer(text="Corpsegrinder • Bot-Version " + VERSION)
    return embed
