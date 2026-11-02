# Corpsegrinder WoW Forever Bot

Horde-only Discord-Community-Bot für PvE/PvP.

## Einrichtung

1. In Home Assistant unter Einstellungen > Apps > App-Store > Repositories dieses Repository hinzufügen.
2. App Corpsegrinder WoW Forever Bot installieren.
3. Im Bereich Konfiguration den Discord-Bot-Token (discord_token) und die Discord-Server-ID (guild_id) eintragen.
4. Nur eine Instanz mit demselben Discord-Token gleichzeitig starten: alte lokale App vorher stoppen.
5. App starten und das Protokoll prüfen. Der Bot meldet „Angemeldet als …“.
6. In Discord als Administrator zunächst /einrichtung_vorschau ausführen. Vorhandene Kanäle bleiben erhalten.
7. /rollenmenue_aktualisieren stellt das neue Rollenmenü bereit. /einrichtung_start ist nur erforderlich, falls Kanäle fehlen.

## Wichtige Hinweise

- Discord-Token niemals in GitHub veröffentlichen. Token wird nur im Home-Assistant-Konfigurationsdialog eingetragen.
- Lokale und Repository-Installation gelten als zwei verschiedene Apps. Daten aus /data/corpsegrinder.sqlite werden nicht automatisch übertragen. Die alte App nicht löschen, bevor Daten und Rollenmenü geprüft wurden.
- Die v1.0.4 erzeugt keine neue private Gildenkategorie. Vorhandene WOW FOREVER | GILDE-Kanäle werden aus Sicherheitsgründen nicht automatisch gelöscht.
- Keine automatische Löschung anderer Discord-Kanäle/Rollen.
- Die App wird auf dem Home-Assistant-Rechner gebaut. Beim ersten Installieren ist Internetzugriff für Python-Pakete notwendig.
- Versionsupdates: Nach Änderung der App-Dateien muss version in config.yaml erhöht werden. Im App-Store nach Updates suchen und Aktualisieren wählen.

## Befehle

/einrichtung_vorschau, /einrichtung_start, /rollenmenue_aktualisieren, /meine_rollen, /charakter, /meine_charaktere, /charakter_loeschen, /gruppe_erstellen, /gruppe_anzeigen, /gruppe_abmelden.
