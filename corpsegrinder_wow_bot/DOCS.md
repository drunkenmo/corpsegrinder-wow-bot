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

## Geplante Instanzgruppen (ab Bot-Version 1.0.9)

**Neue Slash-Befehle:**

- `/gruppe_planen instanz:Flammenschlund tag:übermorgen uhrzeit:20:00 rolle:Tank` erstellt eine öffentliche Gruppe in `#pve-gruppensuche`.
- `/termine` zeigt die nächsten geplanten Gruppen mit direktem Link.
- `/termin_verschieben` ändert Datum/Uhrzeit ohne die vorhandenen Spieler auszutragen.
- `/termin_absagen` sagt einen Termin ab (nur Ersteller oder Server-Admin).

Der Organisator ist bereits mit der gewählten Rolle angemeldet. Der Button-Terminplaner bietet **1 Tank, 1 Heiler und 3 DD**. Jeder Teilnehmer kann mit einem Klick dazukommen, die Rolle wechseln oder sich abmelden. Der Bot aktualisiert die übersichtliche Gruppenkarte sofort und verhindert Doppelanmeldungen sowie zu viele Spieler pro Rolle. Andere Spielkanäle bleiben unberührt.

Das Feld **tag** akzeptiert **heute**, **morgen**, **übermorgen** oder **TT.MM.JJJJ**. Uhrzeit ist deutsche Ortszeit (MEZ/MESZ). Alle Daten bleiben in der Home-Assistant-App-Datenbank `/data/corpsegrinder.sqlite` und werden auch bei Bot-Updates beibehalten. Die bisherigen spontanen Gruppenfinder-Befehle bleiben verfügbar.


## Dungeon-Steuerzentrale – Buttons und Dropdowns (ab 1.0.10)

Nach dem Bot-Update wird in `#pve-gruppensuche` eine Steuerzentrale veröffentlicht. Ihre Buttons bleiben auch nach einem Bot-Neustart funktionsfähig.

**🏰 Dungeon planen** öffnet eine **private** 2-Schritt-Auswahl:

1. Instanz aus einer Classic-Liste und Tank/Heiler/DD auswählen. Für andere Instanzen gibt es `Andere Instanz` mit optionalem Hinweis.
2. Einen Tag aus den **nächsten 21 Tagen**, eine Stunde zwischen 00 und 23 Uhr und Minuten `00 / 15 / 30 / 45` wählen.
3. Erst durch `Termin veröffentlichen` wird die vollständige Fünfergruppe in `#pve-gruppensuche` für alle sichtbar, inklusive Anmeldebuttons.

Die weiteren Tasten **📅 Nächste Termine** und **📋 Meine Termine** zeigen eine private Terminübersicht mit direkten Links.

**Admins:** `/gruppenpanel` kann die Steuerzentrale erneut erstellen oder aktualisieren, ohne Duplikate zu erzeugen. Der Bot versucht die Nachricht anzupinnen; fehlt ihm die Berechtigung `Nachrichten verwalten`, muss ein Administrator sie manuell über das Nachrichtenmenü anpinnen. Anpinnen erzeugt **keine dauerhaft feststehende Chat-Kopfzeile** – die Nachricht wird über das Pin-Symbol oben rechts aufgerufen. Wo möglich, wird bei leerem Kanalthema außerdem ein Link zur Steuerzentrale ergänzt. Vorhandene Kanalthemen werden nicht verändert.

Das alte `/gruppe_planen` bleibt für längere Vorlaufzeiten (mehr als 21 Tage) und freie Eingaben erhalten. Bei Updates werden bestehende Gruppen, Spielerregistrierungen, Rollen und andere Serverkanäle nicht gelöscht.

## Neue Levelgruppen und Dungeon-Umzug (ab Bot-Code 1.0.11)

### Dungeon-Planer
Die öffentliche Dungeon-Steuerzentrale und alle **neu angelegten Dungeon-Gruppentermine** stehen ab dieser Version im Textkanal **#dungeons**. Das vorhandene Dungeon-Panel in `#pve-gruppensuche` wird vom Bot nur dann entfernt, wenn es eindeutig als **eigene** Panel-Nachricht identifiziert wurde. Alte, bereits gebuchte Dungeon-Karten bleiben aus Datensicherheitsgründen an ihrer bisherigen Stelle und funktionieren weiterhin.

### Level-Planer
Im Textkanal **#pve-gruppensuche** erscheint eine eigene grüne Levelgruppen-Steuerzentrale mit den Buttons:
- **🌿 Levelgruppe planen**: Privater Assistent mit Auswahl der Region, des Levelbereichs, Datum und Uhrzeit sowie optionaler Notiz (über "Eigenes Gebiet / Notiz").
- **📅 Leveltermine**: kommende Levelgruppen mit Links zur Anmeldung.
- **📋 Meine Levelgruppen**: eigens erstellte und beigetretene Gruppen.

Gebiete umfassen Horde-Zonen wie Durotar, Mulgore, Brachland, Schlingendorntal und Winterquell. Levelbereiche sind in 5-Stufen-Schritten (plus 1–10 und "alle") auswählbar; maximal fünf Spieler je Gruppe. Der Organisator ist beim Erstellen direkt angemeldet. Mit **Dabei sein** und **Abmelden** kann man jederzeit kommen oder gehen. Die Anmeldungen stehen dauerhaft in SQLite. Organisator oder Administrator können mit `/leveltermin_verschieben` und `/leveltermin_absagen` Änderungen vornehmen.

Wenn das Panel nicht automatisch erscheint, hilft dem Admin `/levelpanel`. Fürs automatische Anpinnen benötigt der Bot **Nachrichten verwalten**; sonst kann ein Administrator manuell über das Discord-Nachrichtenmenü anpinnen. Anpinnen bedeutet Zugang über das Pin-Symbol, nicht dauerhaft oben im laufenden Chat.

### Automatische Voice-Gruppe: Ersteller sofort mitnehmen
Wer die Sprachkanäle **➕ PvE-Gruppe erstellen** oder **➕ PvP-Gruppe erstellen** betritt, soll direkt in den neu erzeugten Voice-Kanal verschoben werden. Dafür muss der **WoW Forever Bot** die Discord-Rollenberechtigungen **Kanäle verwalten**, **Kanäle ansehen** und insbesondere **Mitglieder verschieben** besitzen. Die Rechte dürfen in den PvE-/PvP-Kategorien nicht blockiert werden. Fehlt "Mitglieder verschieben", lässt Discord die automatische Verschiebung nicht zu; der Bot meldet dies und legt keine leeren Kanalreste an.

Alle Änderungen an normalen Botfunktionen kommen weiterhin mit `/bot_update` und benötigen keine neue Home-Assistant-App.
