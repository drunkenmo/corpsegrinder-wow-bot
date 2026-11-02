# Corpsegrinder WoW Forever Bot

Discord-Bot für die **Horde-Community Corpsegrinder** mit PvE/PvP-Gruppensuche, Charakterverwaltung, rollenbasierter Auswahl und Home-Assistant-App.

## Installation / Updates

Home Assistant → **Einstellungen → Apps → App-Store → ⋮ → Repositories**: `https://github.com/drunkenmo/corpsegrinder-wow-bot` eintragen.

Die Version steht in [config.yaml](corpsegrinder_wow_bot/config.yaml). Neue Versionen erscheinen nach Aktualisierung des App-Stores als App-Update; die Einstellungen und die Daten in /data bleiben bei einer Aktualisierung der gleichen App erhalten.

**Keine Secrets auf GitHub speichern.** Der Discord-Bot-Token gehört ausschließlich in das Home-Assistant-Konfigurationsformular.

## Aktueller Stand: 1.0.6

- Updates des Python-Bot-Codes mit /bot_update (Administrator-Bestätigung, SHA-256-Prüfung und Rollback)
- Rollenwahl mit PvE/PvP, Tank/Heiler/DD, Klassen und Benachrichtigungen
- Warcraft-Farben und Emoji-Rollennamen per /rollen_design_vorschau → /rollen_design_anwenden
- Echte Discord-Rollen-Icons bei Boost-Level 2, wenn verfügbar
- Begrüßung bei neuen Mitgliedern
- Willkommen- und Ankündigungs-Infokarten mit /startkanaele_einrichten
- Administrationsankündigungen über /ankuendigung
- Einmalige Meldung über neue Bot-Versionen im Kanal #ankündigungen
- Charakterdaten, Gruppenfinder und temporäre Sprachkanäle

Die vollständige Anleitung steht in [DOCS.md](corpsegrinder_wow_bot/DOCS.md).

**Sicherheit:** Ein Einrichtungs- oder Rollendesign-Befehl wird nur auf expliziten Admin-Aufruf ausgeführt. Vorhandene Gilden- und andere Spielkanäle werden nicht automatisch gelöscht.

### Updateverfahren ab 1.0.6

Die Home-Assistant-App mit dem stabilen Launcher muss **einmal** auf 1.0.6 gebracht werden. Danach genügt für normale Bot-Änderungen in Discord der Befehl `/bot_update`. Die Version und Prüfsummen der aktualisierten Python-Dateien stehen in [bot_releases/latest.json](bot_releases/latest.json). Ein GitHub-Actions-Workflow erstellt dieses Manifest nach Tests automatisch. Für Änderungen am Launcher oder den Systemabhängigkeiten ist weiterhin ein Home-Assistant-App-Update erforderlich.
