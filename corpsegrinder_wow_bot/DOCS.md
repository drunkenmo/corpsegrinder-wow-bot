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
- Die v1.0.5 erzeugt keine neue private Gildenkategorie. Vorhandene WOW FOREVER | GILDE-Kanäle werden aus Sicherheitsgründen nicht automatisch gelöscht.
- Keine automatische Löschung anderer Discord-Kanäle/Rollen.
- Die App wird auf dem Home-Assistant-Rechner gebaut. Beim ersten Installieren ist Internetzugriff für Python-Pakete notwendig.
- Versionsupdates: Nach Änderung der App-Dateien muss version in config.yaml erhöht werden. Im App-Store nach Updates suchen und Aktualisieren wählen.

## Befehle

/einrichtung_vorschau, /einrichtung_start, /rollenmenue_aktualisieren, /meine_rollen, /charakter, /meine_charaktere, /charakter_loeschen, /gruppe_erstellen, /gruppe_anzeigen, /gruppe_abmelden.

## Neue Befehle ab 1.0.5

- /rollen_design_vorschau zeigt vorab genau an, welche Rollen umbenannt werden.
- /rollen_design_anwenden benennt bestehende Rollen mit Emojis um und setzt Farben; Rollenzuweisungen bleiben erhalten.
- /startkanaele_einrichten erzeugt eine Begrüßung in #willkommen und eine Info in #ankündigungen; der Bot versucht diese anzuheften (benötigt Nachrichten verwalten).
- /ankuendigung titel:<Text> text:<Text> erstellt eine formatierte Mitteilung ohne Massen-Pings (Admins).
- /ankuendigungen_schreibschutz macht #ankündigungen für normale Mitglieder schreibgeschützt (Admins).
- Beim Start einer neuen Version wird einmal eine Bot-Update-Meldung nach #ankündigungen gepostet. Bei neuen Mitgliedern erfolgt automatisch eine Begrüßung in #willkommen.

Achtung: Unicode-Emojis im Rollennamen erscheinen im Rollenprofil; ein echtes Icon direkt neben dem Chatnamen benötigt Discords Rollen-Icons (Boost-Level 2). Es wird nur das Icon der höchstpriorisierten passenden Rolle angezeigt. Der Bot verändert keine Nicknames automatisch.

## Bot-Updates direkt in Discord (ab Home-Assistant-App-Version 1.0.6)

- Die Home-Assistant-App auf **1.0.6** aktualisieren (letztes notwendiges App-Update für normale Bot-Codeänderungen).
- In Discord als Server-Administrator `/bot_update` eingeben. Bei einer neueren Version auf `🔄 Update installieren` klicken.
- Nach erfolgreicher SHA-256-/Syntaxprüfung verbindet sich der Bot automatisch neu. Der App-Container bleibt dabei aktiv. Ein abgebrochenes Update ändert den laufenden Code nicht.
- `/bot_update_status` zeigt die aktive Bot-Version. Bei fehlerhaftem Start setzt der Launcher automatisch auf die zuletzt funktionierende Version zurück.
- Die Bot-Datenbank und `/data/options.json` werden **nicht** mit GitHub überschrieben. Es wird **kein** Home-Assistant-Supervisor-API-Administratorzugriff benötigt.
- **Sicherheit:** Das Verfahren führt Python-Code aus dem festgelegten GitHub-Repository aus. Schütze deshalb dein GitHub-Konto mit Zwei-Faktor-Authentifizierung und lasse nur vertrauenswürdige Personen dort Änderungen vornehmen. Keine Updates aus fremden Quellen.
- **Grenze:** Änderungen am festen Launcher, Python-Abhängigkeiten oder Home-Assistant-App-Einstellungen benötigen weiterhin ein reguläres Home-Assistant-App-Update. Normale Änderungen an `bot.py` und `community_features.py` nicht mehr.

### Neue Bot-Version veröffentlichen

1. Ändere `bot.py` / `community_features.py` und erhöhe `VERSION` in `community_features.py` (z. B. 1.0.7).
2. GitHub Actions führt Python-Syntax- und Offline-Updater-Tests aus und veröffentlicht bei Erfolg das Release-Manifest `bot_releases/latest.json` mit einem festen Commit und SHA-256-Prüfsummen.
3. In Discord mit `/bot_update` prüfen und installieren. **Keine ZIP-Datei und kein `ha store reload` nötig.**

Es gibt **keine automatische Selbstaktualisierung ohne Admin-Bestätigung**. Die vorherige Version bleibt im persistierenden App-Speicher für einen Rückfall erhalten.
