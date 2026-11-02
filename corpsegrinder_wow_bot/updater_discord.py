"""Discord admin UI for updates. This module is included in the stable HA app."""
import asyncio
import logging
import os

import discord

from updater_core import (
    UpdateError, BUILTIN_VERSION, check_update, install_update, installed,
)

log = logging.getLogger("corpsegrinder.updater")


class ConfirmUpdate(discord.ui.View):
    def __init__(self, manifest, user_id, admin_predicate):
        super().__init__(timeout=120)
        self.manifest = manifest
        self.user_id = user_id
        self.admin_predicate = admin_predicate

    @discord.ui.button(label="Update installieren", emoji="🔄", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id or not self.admin_predicate(interaction):
            return await interaction.response.send_message(
                "Dieses Update darf nur der Administrator bestätigen, der es geöffnet hat.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            version = await asyncio.to_thread(install_update, self.manifest)
        except (UpdateError, OSError) as exc:
            log.warning("Update abgebrochen: %s", exc)
            return await interaction.followup.send(
                "Update nicht installiert: " + str(exc), ephemeral=True)
        await interaction.followup.send(
            "✅ Bot-Code " + version + " geprüft und installiert. "
            "Der Bot verbindet sich jetzt automatisch neu. Bei einem Startfehler "
            "stellt der Launcher die vorherige Version wieder her.",
            ephemeral=True)
        self.stop()
        asyncio.create_task(self._restart_worker())

    async def _restart_worker(self):
        await asyncio.sleep(2)
        # Only the bot child is restarted. The stable launcher stays running.
        os._exit(42)


def register(bot, server, admin_predicate):
    @bot.tree.command(
        name="bot_update", description="Neue Bot-Version über GitHub prüfen und installieren (Admin)",
        guild=server)
    async def bot_update(i: discord.Interaction):
        if not admin_predicate(i):
            return await i.response.send_message("Nur Server-Administratoren.", ephemeral=True)
        await i.response.defer(ephemeral=True, thinking=True)
        try:
            manifest, newer = await asyncio.to_thread(check_update)
        except (UpdateError, OSError) as exc:
            return await i.followup.send("Update-Prüfung fehlgeschlagen: " + str(exc), ephemeral=True)
        current = os.environ.get("CORPSEGRINDER_WORKER_VERSION", BUILTIN_VERSION)
        if not newer:
            return await i.followup.send(
                "✅ Du verwendest Version **" + current +
                "**. Auf GitHub liegt **" + manifest["version"] + "** – kein neueres Update.",
                ephemeral=True)
        embed = discord.Embed(
            title="🔄 Corpsegrinder Bot-Update verfügbar",
            description="Installiert: **" + current + "**\nNeu: **" + manifest["version"] +
                        "**\n\nDownload ausschließlich aus dem Corpsegrinder-GitHub-Repository. "
                        "Die Dateien werden per SHA-256 geprüft und vor dem Neustart auf "
                        "Python-Syntax getestet.",
            colour=discord.Colour.blue(),
        )
        embed.add_field(
            name="Sicherheit",
            value="Nur Administratoren können bestätigen. "
                  "Die bisherige Version bleibt für einen automatischen Rollback erhalten. "
                  "Deine Charakterdaten und der Token werden nicht ersetzt.",
            inline=False)
        await i.followup.send(
            embed=embed, ephemeral=True,
            view=ConfirmUpdate(manifest, i.user.id, admin_predicate))

    @bot.tree.command(
        name="bot_update_status", description="Aktuellen Stand des Bot-Updaters anzeigen",
        guild=server)
    async def bot_update_status(i: discord.Interaction):
        if not admin_predicate(i):
            return await i.response.send_message("Nur Server-Administratoren.", ephemeral=True)
        active = os.environ.get("CORPSEGRINDER_WORKER_VERSION", BUILTIN_VERSION)
        pending = installed()
        await i.response.send_message(
            "🛠️ **Corpsegrinder Bot**\nAktiv: **" + active +
            "**\nInstalliert für nächsten Start: **" + pending +
            "**\nHome-Assistant-Basis: **1.0.6**\n"
            "Mit /bot_update kannst du nach einer neuen GitHub-Version suchen.",
            ephemeral=True)
