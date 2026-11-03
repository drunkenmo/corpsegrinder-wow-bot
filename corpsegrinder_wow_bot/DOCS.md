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

## Das große Horde-Update 1.0.12

### Neues Design
- Das angepinnte Panel in `#willkommen` zeigt ein selbst gestaltetes Lagerfeuer-Banner (Ork, Tauren und Troll), Humor und Links zu den anderen Bereichen. Die bestehende Geschichte der Gilde seit 2004 wird bewusst nicht überschrieben oder gelöscht.
- `#rollenwahl` bekommt eine rot-goldene Karte mit den Sektionen Spielbereiche, Gruppenaufgaben, Klassen und News/Erinnerungen sowie eine hübsche private Meine-Auswahl-Anzeige.
- Das Dungeon-Panel in `#dungeons` und das Level-Panel in `#pve-gruppensuche` zeigen automatisch die **nächsten drei Gruppen** samt Restplätzen. Bilder werden als öffentliche PNG-Assets aus dem Github-Repository geladen. Der GitHub-Actions-Workflow rendert die zugrunde liegenden SVG-Illustrationen zu PNG.

### Persönliche Benachrichtigungen
- Standardmäßig aktiv. `/erinnerungen aktiv:false` deaktiviert sowohl die Erinnerungs-DMs als auch Vollmeldungen. `/erinnerungen aktiv:true` schaltet wieder ein.
- Alternativ: Schalter **Erinnerungen an/aus** direkt in `#rollenwahl`; **Meine Auswahl** zeigt die aktuelle Einstellung.
- 15 Minuten vor einem geplanten Termin werden die angemeldeten Spieler per Direktnachricht informiert, mit Link zur Gruppenkarte. Pro Teilnehmer und Gruppentermin gibt es keine doppelte Erinnerung (selbst nach Neustarts).
- Wenn ein Dungeon erstmals **1 Tank / 1 Heiler / 3 DD** erreicht, werden alle fünf Spieler einmal benachrichtigt. Wird die Gruppe später durch Abmeldung wieder unvollständig und erneut vollständig, darf es eine neue Vollmeldung geben.
- Falls Discord-Direktnachrichten blockiert werden, protokolliert der Bot dies und läuft weiter, ohne die Gruppe zu stören.

### Automatisch geplante Sprachkanäle
- Für **Dungeon- und Levelgruppen mit fünf angemeldeten Spielern** legt der Bot 15 Minuten vor Start einen fünf Plätze großen Sprachraum in der PvE-Kategorie an.
- Erreicht eine Gruppe erst nach diesem Zeitpunkt die volle Besetzung, öffnet der Bot den Raum noch vor der Startzeit.
- Der Raumname enthält die Instanz bzw. das Levelgebiet, bei Levelgruppen den Levelbereich und die Uhrzeit.
- Der direkte Link erscheint in der Gruppenkarte und gegebenenfalls in der Erinnerung.
- Solange ein Sprachraum noch nie benutzt wurde, hat er mindestens eine Stunde Schonfrist. Danach entfernt der Bot ungenutzte Räume; sobald ein besuchter Raum wieder leer wird, löscht der Bot ihn automatisch. **Die automatische Kartenlöschung trennt keine Spieler aus einem Sprachchat.**
- Voraussetzung: Der Bot benötigt **Kanäle verwalten** in der PvE-Kategorie und Berechtigung, den Sprachkanal zu erstellen.

### Termine und automatisches Aufräumen
- Beim Start einer Gruppe ist die Karte aktiv. **Eine Stunde nach dem Start** erscheint **⌛ Abgelaufen**, fünf Minuten später wird die Discord-Nachricht gelöscht.
- Die SQLite-Datensätze werden als internes Archiv behalten, die Karten verschwinden aus den aktiven Übersichten.
- Der neue Button **✅ Abschließen** ermöglicht Organisator oder Admin, eine Gruppe vorzeitig zu beenden (fünf Minuten bis zur Kartenlöschung).
- Auch abgesagte Termine werden nach einer kurzen Frist aufgeräumt.

### Entfernen des alten Gildenbereichs
- Der frühere Bereich `🔒 WOW FOREVER | GILDE` ist nicht mehr erforderlich.
- Der Bot sucht beim ersten Start nur nach Kategorien, deren Name auf `WOW FOREVER | GILDE` endet, und löscht dort ausschließlich `gildenchat`, `gilden-raids` und `offiziers-chat`, anschließend die Kategorie.
- **Achtung: Discord-Kanallöschungen entfernen den Chatverlauf unwiderruflich.** Hat der Bereich weitere oder anders benannte Kanäle, wird zur Sicherheit nichts gelöscht und der Fall im Log vermerkt.
- Außerhalb dieser Kategorie werden keine anderen Kanäle verändert oder gelöscht.

### Update
1. In Discord mit `/bot_update` die Version 1.0.12 installieren.
2. Nach dem automatischen Neustart mit `/bot_update_status` die neue Version prüfen.
3. Falls die Illustration noch nicht sofort zu sehen ist, prüfen, ob GitHub Actions bereits `assets/*.png` veröffentlicht hat; Discord kann Bilder kurzzeitig cachen.
4. Gruppensuche und Voice mit zwei Testaccounts ausprobieren.

## Forever News – offizieller Blizzard-Feed (Bot-Code 1.0.13)

Der Bot erstellt nach dem Discord-Update automatisch den Textkanal `#forever-news` **direkt unter `#ankündigungen`, über `#rollenwahl`** in der bestehenden Start-Kategorie und fügt eine angepinnte Info-Karte hinzu. Der Kanal ist als News-Kanal mit Schreibrecht für den Bot vorgesehen.

**Quelle:** Primär nutzt der Bot Blizzards eigenen nach dem Produkt `world-of-warcraft-forever` gefilterten News-Endpunkt unter `https://news.blizzard.com/de-de/api/news/blizzard?feedCxpProductIds%5B%5D=world-of-warcraft-forever`. Weil dieser Endpunkt nicht als stabile öffentliche Programmierschnittstelle garantiert ist, dienen die offizielle deutsche News-Übersicht unter `https://worldofwarcraft.blizzard.com/de-de/news` und die offizielle `news.blizzard.com`-Übersicht als Fallback. Es werden nur Artikel-URLs der offiziellen Domains und eindeutig Forever-bezogene Artikelüberschriften berücksichtigt. Gemischte Sammelbeiträge über andere WoW-Versionen werden weggelassen. Der Bot schaut **alle 30 Minuten** nach neuen Einträgen, ohne Push-Spam und ohne Doppelpostings.

**Erstbefüllung:** Beim ersten erfolgreichen Abruf werden ausschließlich passende Blizzard-Artikel aus den vorherigen **48 Stunden** veröffentlicht. Das Datum stammt aus offiziellen Artikelmetadaten; Veröffentlichungen ohne eindeutig auslesbare Datumsangabe werden aus Vorsicht nicht gepostet. Wenn es in dieser Zeit keine Forever-News gibt, bleibt der Kanal zunächst nur mit der Info-Karte sichtbar – es werden keine älteren Meldungen als angeblich neue veröffentlicht. Vorübergehende Fehler beim Abruf sind im Home-Assistant-Bot-Log zu sehen.

**Kommandos:** `/forever_news_status` zeigt die Anzahl gespeicherter Meldungen und den letzten Abruf. Mit `/forever_news_pruefen` kann ein Administrator sofort einen erneuten Abruf anstoßen. Der Bot archiviert bereits gepostete Artikel-IDs in `/data/corpsegrinder.sqlite` und postet sie nach Neustarts nicht erneut.

**Berechtigungen:** Der Bot braucht in seiner Start-Kategorie mindestens `Kanäle verwalten`, `Kanal anzeigen`, `Nachrichten senden`, `Links einbetten` und `Nachrichtenverlauf lesen`. Fürs Anpinnen kommt `Nachrichten verwalten` hinzu.

Nur die normalen per `/bot_update` verwalteten Python-Code-Dateien wurden verändert. Es wird keine zusätzliche Python-Abhängigkeit oder Home-Assistant-App-Aktualisierung benötigt.

## Forever-News und Addons ab Bot-Version 1.0.14

### #forever-news: Blizzard + zusätzliche Forever-Quellen

Die seltenen **offiziellen Blizzard-Meldungen** bleiben erhalten und werden weiterhin ausdrücklich als solche gekennzeichnet. Die weiteren Quellen sind:
- **Wowhead – Forever News:** `https://www.wowhead.com/forever/news`. Artikel aus der eigenen Forever-Rubrik, in Discord als `Community-News · Wowhead` bezeichnet. Nur aktuelle, anhand von Metadaten datierbare Forever-Themen werden gepostet.
- **WoW Forever GG:** `https://wow-forever.gg/rss.xml` sowie `https://wow-forever.gg/official.xml`. Ein unabhängiges Forever-Community-Portal mit RSS. Beiträge werden als Community-Quelle gekennzeichnet, auch wenn sie auf einen Blizzard-Beitrag verweisen.

Der Bot prüft weiterhin alle 30 Minuten. Community-Artikel aus den letzten sieben Tagen kommen nur dann dazu, wenn Titel, gültige Quell-URL und Veröffentlichungsdatum überprüfbar sind (maximal fünf neue Beiträge je Prüfung). URLs bleiben in SQLite, damit nach Neustarts keine wiederholten Meldungen entstehen. Die drei im Code hinterlegten Wowhead-Lesetipps sind als **Startauswahl**, nicht als neue Blizzard-Mitteilungen ausgewiesen.

Wichtig: Automatisches Lesen von Webseiten funktioniert nur, sofern die jeweiligen Anbieter den Abruf durch den Bot erlauben. Wowhead kann Scraping blockieren; alle solchen Fehler erscheinen im Home-Assistant-Log und sind kein Grund, Meldungen zu erfinden. Bei technischen Problemen bleibt wenigstens die echte Startauswahl erhalten.

### #addons: nur Forever-Dateien, keine Retail-Downloads

Neuer eigener Textkanal **#addons** direkt unter **#forever-news**, vor **#rollenwahl**. Die angepinnte Empfehlungsliste verweist auf die Projektseiten bei CurseForge:
- Questie (Questhilfe)
- Leatrix Plus und Leatrix Maps (Komfort/Karte)
- Auctionator (Auktionshaus)
- Baganator (Taschen)
- TomTom (Wegpunkte)
- Deadly Boss Mods (Bosswarnungen, Inhalte gesondert prüfen)
- QuestForever (Questhilfe speziell für Forever)

**Automatische Prüfung alle sechs Stunden:** Der Bot liest die CurseForge-Projektseiten und sucht gezielt die **WoW Forever**-Datei, unterstützt durch die explizite Spielversion **1.60.1**. Er veröffentlicht Änderungen für bekannte Projekte und kann über die CurseForge-Suche neue Forever-Dateien finden. Neue Projekte erhalten die Warnung `Neu gefunden – keine Qualitätsempfehlung`, und bei der Erstbefüllung wird die Zahl der Meldungen gedrosselt. Ohne eindeutigen Forever-Nachweis wird nichts als updatefähig angekündigt. Projektseiten werden verlinkt; der Bot lädt keine Dateien herunter und installiert sie nicht. Die tatsächliche Funktionstüchtigkeit der Addons ist nicht durch den Bot garantiert.

**Befehle:** `/addons_status` für den aktuellen Stand und `/addons_pruefen` (Admin) für einen sofortigen Lauf. `/forever_news_status` zeigt jetzt sowohl Blizzard- als auch Community-Beiträge; `/forever_news_pruefen` sucht beide Arten.

Die neue Bot-Code-Version wird per `/bot_update` installiert. Die bestehende SQLite-Datei mit Charakteren und Gruppen bleibt erhalten.

## Nachrichten direkt in Discord – Version 1.0.15

Ab 1.0.15 sind die Artikelkarten in `#forever-news` selbst aussagekräftiger: Sie enthalten deutschsprachige Überschriften und direkt darunter aufgelistete belegbare Fakten. Es gibt ausdrücklich **keinen „Ausführlicher lesen“-Button** und keine zusätzliche private Discord-Ansicht. Der verlinkte Originalartikel dient nur als Quellenangabe.

Der Bot verwendet eine regelbasierte Darstellung ohne externen Übersetzungsdienst. Bei Build-/Changelog-Meldungen werden insbesondere **Buildnummern**, **neu hinzugefügte, entfernte und geänderte Zauber und Gegenstände** sowie Klassen- und Talentinformationen herausgearbeitet. Andere Arten von Meldungen erhalten einen kurzen deutschen Kontext. Wenn die Originalquelle keine zuverlässigen Angaben liefert, erfindet der Bot keine Übersetzung und behauptet nicht, den vollständigen Originalartikel wiederzugeben. Vollständige geschützte Artikeltexte werden nicht kopiert.

Zurückliegende Community-Meldungen, die noch über die Feeds/Artikel erreichbar sind, werden anhand ihrer Discord-Nachrichten-ID *in-place* bearbeitet. Die Tabelle `forever_news_card_versions` verhindert doppelte Änderungen und zusätzliche Nachrichtenspam. Sobald neue Feed-Inhalte verfügbar werden, werden bislang nicht umformatierte ältere Posts bei einer späteren Prüfung erneut berücksichtigt.

Die automatisch gespeicherte SQLite-Datenbank und sämtliche bereits erstellten Kanäle und Rollen bleiben unverändert.
