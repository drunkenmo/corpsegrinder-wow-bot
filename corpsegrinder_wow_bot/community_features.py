import discord

VERSION = "1.0.13"

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
        title="🍻 CORPSEGRINDER · FÜR DIE HORDE!",
        description=(
            "**ALTE SÄCKE. KALTES BIER. SEIT 2004.** 🔥\n\n"
            "Es war einmal im Classic-Release-Jahr 2004: mittelmäßiges DSL, "
            "ordentlich Bier und erschreckend wenig Ahnung. "
            "Ein paar Orks, Tauren und Trolle zogen los – und sind irgendwie "
            "immer noch gemeinsam unterwegs.\n\n"
            "Willkommen am Lagerfeuer! Hier spielen alte Gildenfreunde und neue "
            "Horde-Mitstreiter zusammen. Eine Gildenmitgliedschaft brauchst du nicht."
        ),
        colour=discord.Colour.from_rgb(153, 46, 29))
    embed.set_image(
        url="https://raw.githubusercontent.com/drunkenmo/corpsegrinder-wow-bot/main/assets/welcome.png")
    embed.add_field(
        name="🎭 DEINE ROLLEN",
        value="PvE/PvP, Tank, Heiler, DD, Klassen und Benachrichtigungen wählen.",
        inline=False)
    embed.add_field(
        name="⚔️ DEIN NÄCHSTES ABENTEUER",
        value="In **#dungeons** Instanzgruppe planen oder in "
              "**#pve-gruppensuche** Mitspieler zum Leveln treffen.",
        inline=False)
    embed.add_field(
        name="📖 UNSERE STORY",
        value="Die echte Geschichte der alten Säcke steht hier im Willkommen-Kanal. "
              "Lest sie ruhig – sie ist fast so alt wie unser Internetanschluss.",
        inline=False)
    embed.set_footer(
        text="Corpsegrinder • Willkommen • corpsegrinder:welcome")
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
        title="📰 Corpsegrinder Bot – Update " + VERSION,
        description=(
            "**NEU: #forever-news – Offizielle Blizzard-Nachrichten!**\n\n"
            "Direkt unter **#ankündigungen** und über **#rollenwahl** "
            "erscheint ein neuer Textkanal nur für **World of Warcraft: Forever**.\n\n"
            "🔎 Der Bot prüft alle **30 Minuten** die offiziellen deutschen "
            "Blizzard-Neuigkeiten und veröffentlicht nur eindeutig Forever-bezogene "
            "Artikel mit geprüftem Veröffentlichungsdatum.\n\n"
            "📅 Beim ersten Start werden passende Artikel der letzten "
            "**48 Stunden** nachgetragen, sofern es welche gibt. "
            "Jeder Artikel wird nur einmal gepostet.\n\n"
            "Admin: **/forever_news_pruefen** · Status: **/forever_news_status**"
        ),
        colour=discord.Colour.dark_red())
    embed.set_footer(text="Corpsegrinder • Bot-Version " + VERSION)
    return embed
