# Changelog

## 1.0.6 – Discord-Updater (einmaliges Home-Assistant-App-Update)
- Neuer Slash-Befehl /bot_update mit Admin-Bestätigung.
- Bot-Code wird aus festgelegtem GitHub-Repository geladen; der Release-Commit ist festgepinnt und die Python-Dateien werden per SHA-256 geprüft.
- Nur der Bot-Prozess wird nach dem Update neu gestartet. Bei einem Startfehler greift der Launcher auf die letzte funktionierende Version zurück.
- /bot_update_status zeigt aktive Version und ggf. installierte Version an.
- GitHub-Actions-Workflow publiziert nach Offline-Tests den Release für künftige Versionen.
- Datenbank, Tokens und Home-Assistant-Einstellungen bleiben in /data bestehen.

## 1.0.5
- Warcraft-Rollenfarben und sichtbare Emoji-Rollennamen mit sicherer Admin-Vorschau.
- Native Rollen-Icons, falls Server-Boost-Level 2 vorhanden ist.
- Automatische einmalige Bot-Update-Mitteilung in #ankündigungen.
- Begrüßung neuer Mitglieder und Startkarten für #willkommen / #ankündigungen.
- Admin-Ankündigungen und optionaler Schreibschutz für #ankündigungen.

## 1.0.4
- Neue Rollenwahl mit getrennten PvE/PvP-, Tank/Heiler/DD-, Klassen- und Benachrichtigungsoptionen.
- Befehl /rollenmenue_aktualisieren.
- Keine neue private Gilden-Kategorie mehr bei der Einrichtung.
- Umstellung auf GitHub-basiertes Home-Assistant-App-Repository.

## 1.0.3
- Verbesserte Fehlermeldungen bei Discord-Berechtigungsproblemen.
