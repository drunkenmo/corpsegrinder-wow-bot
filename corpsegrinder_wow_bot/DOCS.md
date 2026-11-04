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

## Ingame-Namen und Hauptcharakter/Twinks (Version 1.0.16)

Der Bot verwendet die **bestehende** `characters`-Tabelle (aus dem Slash-Befehl `/charakter`). Zusätzliche Informationen liegen in `main_characters` und `group_character_choices`, um ältere Charaktere und Gruppenanmeldungen nicht zu beschädigen.

### Dein Charakterprofil
1. Mit `/charakter name:Grumok klasse:Krieger level:35` einen Charakter registrieren oder aktualisieren. Ein zweiter Eintrag, etwa `Zaraku`, ist ein Twink. Bis zu 25 Charaktere können angelegt werden.
2. `/meine_charaktere` zeigt eine **nur für dich sichtbare** Übersicht.
3. `/hauptcharakter name:Grumok` wählt den Hauptcharakter aus. Die Autovervollständigung listet die eigenen Charaktere.
4. `/charakter_loeschen` entfernt einen Eintrag. Bestehende Gruppenanmeldungen bleiben erhalten. Ein zuvor für einen Gruppentermin ausdrücklich gewählter, danach gelöschter Charakter erscheint als Hinweis, bis ein neuer ausgewählt wird.

### Dungeon- und Levelgruppen
- Bei einem einzigen eingetragenen Charakter wird dieser beim Klick auf `Tank`, `Heiler`, `DD` oder `Dabei sein` direkt übernommen.
- Bei mehreren Charakteren öffnet Discord ein privates Dropdown. Der gewählte Charakter wird dauerhaft zu **dieser konkreten Gruppenanmeldung** gespeichert.
- Wer noch keinen Charakter registriert hat, erhält einen Hinweis zu `/charakter` statt eine Anmeldung mit einem unbekannten Ingame-Namen.
- Bei der **Erstellung** einer neuen Dungeon- oder Levelgruppe erscheint in Schritt 2 der Assistenten ebenfalls eine Charakterauswahl. Das erste Profil beziehungsweise der Hauptcharakter wird vorausgewählt. Ohne Profil bleibt die alte Erstellung weiterhin möglich, die Karte weist dann auf den fehlenden Charakter hin.
- Ein Spieler kann über den neuen Button `🎭 Charakter ändern` den Charakter für eine bestehende Anmeldung wechseln, ohne den Gruppenplatz aufzugeben. Die Rolle im Dungeon bleibt dabei gleich.
- Die **Gruppenkarte** zeigt vorrangig `Grumok · Krieger · Stufe 35`, darunter `@Discord-Mitglied` als klickbare Zuordnung. Für ältere Gruppen ohne gespeicherte Charakterauswahl wird der derzeitige Hauptcharakter angezeigt, sofern registriert.
- Änderungen am globalen Hauptcharakter ändern **nicht** die bei einer Gruppenanmeldung ausdrücklich gespeicherte Charakterwahl.
- Erinnerung und Terminbestätigungen nennen den ausgewählten Ingame-Namen. Die bestehenden Gruppen-Erinnerungen, automatische Sprachräume, Ablaufregeln und Gruppengrößen gelten unverändert.
- **Kein Multiboxing-Sonderfall:** Der Bot speichert pro Discord-ID maximal eine Anmeldung je Gruppe, auch wenn das Mitglied mehrere Ingame-Charaktere besitzt.
- **Keine Ingame-Verifizierung:** Die Spieler pflegen ihre Charaktere selbst; der Bot verknüpft sie nur mit der Discord-Mitglieds-ID.

### Freiwilliger Discord-Servernickname
`/ingame_nickname aktiv:true` setzt den Servernickname freiwillig auf `Grumok | Discordname` (mit Discord-Längenbegrenzung). Der vorherige Nickname wird gespeichert. `/ingame_nickname aktiv:false` stellt ihn wieder her, **wenn der aktuelle Name noch dem vom Bot gesetzten entspricht**. Von Mitgliedern später manuell geänderte Servernamen werden nicht überschrieben. Wird ein aktiver Main gewechselt, versucht der Bot den freiwilligen Nickname anzupassen. Erforderlich sind Discord-Bot-Rechte **Nicknames verwalten** und eine ausreichend hohe Rollenposition.

Bei Berechtigungsfehlern bleibt das Profil bestehen und der Bot zeigt eine Fehlermeldung statt die gesamte Anmeldung abzubrechen.

## Charakterregistrierung ohne Level und Onboarding-Buttons (Bot 1.0.17)

**Dies ersetzt die Bedienungsanleitung aus 1.0.16 in Bezug auf Level und die Erstanmeldung.**

### Was ist neu?

Im Kanal **#rollenwahl** veröffentlicht der Bot automatisch eine zusätzliche Karte **„DEIN INGAME-NAME“** direkt im bestehenden Rollenwahlbereich:

- **🎭 Charakter registrieren:** Nur der Spieler sieht die Klassen-Auswahl. Danach öffnet sich ein Discord-Eingabefenster für den **Ingame-Namen**. Keine Level-Eingabe, keine Berufe und keine Bestätigung eines Admins. Über denselben Ablauf lassen sich Twinks hinzufügen oder bestehende Klassen korrigieren.
- **👑 Meine Charaktere:** Privates Profil mit allen Charakteren und Button **Hauptcharakter ändern**. Hauptcharakter wird bei der ersten Registrierung automatisch festgelegt.
- **✏️ Servername an/aus:** Nur auf freiwilligen Klick. Der Bot ändert den Server-Nickname zum Hauptcharakter oder stellt den vorherigen Namen wieder her, wenn die Discord-Berechtigungen es erlauben. Die Anmeldekarten funktionieren auch ohne diese Option.

Der gleiche Ablauf steht mit `/charakter name:<Name> klasse:<Klasse>` weiterhin als Slash-Befehl bereit; die früher verpflichtende Eingabe `level` ist entfernt.

### Neue Mitglieder

- In **#willkommen** weist die Willkommenskarte auf `#rollenwahl` und die neue Charakterregistrierung hin.
- Beim Betreten des Servers informiert die Bot-Begrüßung ebenfalls über die Schritte **Rollen auswählen → Charakter registrieren**.
- Neue Spieler müssen **nichts beantragen und nicht auf eine Freigabe warten**.
- Nach der Anmeldung zeigen Gruppenkarten den Ingame-Namen und die Klasse vor dem verlinkten Discord-Account.

### Technische Kompatibilität

Die SQLite-Tabelle `characters` bleibt unverändert, inklusive der Alt-Spalten `level`, `beruf1`, `beruf2`, um keine bestehenden Daten zu verlieren und die alten DB-Versionen weiterhin öffnen zu können. Neuen Charakteren wird intern ein neutraler Platzhalterwert zugewiesen, der weder im Profil noch auf Gruppenkarten oder in Dropdowns erscheint. Bestehende alte Werte werden beim Bearbeiten nicht überschrieben.

**Gruppen-Levelbereiche** zur Planung von Levelgruppen bleiben erhalten, da sie unabhängig vom Charakterprofil sind.

Das neue Charakterpanel hat einen eindeutigen Discord-Marker `corpsegrinder:character-panel` und ist über `character_panel_message_v117` persistiert. Der Bot lädt die zugehörigen dauerhaften Buttons bei jedem Start und aktualisiert dieselbe Nachricht. Als Administrator kannst du jederzeit `/rollenmenue_erneuern` verwenden; dabei wird auch das Charakterpanel erneuert. Der gewünschte Komfort-Workflow benötigt keine neuen Python-Abhängigkeiten.

Bei Slash-Kommandos kann die Discord-App unmittelbar nach einem Update noch die alte Auswahlliste im Cache zeigen; die App neu öffnen, falls `/charakter` weiterhin ein Level verlangt.

## Charaktere bearbeiten, löschen und im Sprachchat anzeigen (Version 1.0.18)

In **#rollenwahl** auf **Meine Charaktere** klicken. Im privaten Profil stehen jetzt vier Funktionen:

1. **👑 Hauptcharakter ändern:** Wie bisher einen anderen registrierten Charakter als Main wählen.
2. **✏️ Bearbeiten:** Einen eigenen Charakter auswählen und **Ingame-Name und Klasse** in einem Eingabedialog ändern. Der Bot schreibt den Namen auch in gespeicherten Gruppen-Charakterzuordnungen um; Teilnahmen und Rollen bleiben erhalten. Es werden weder Level noch Berufe abgefragt.
3. **🗑️ Löschen:** Einen eigenen Charakter auswählen und die Aktion bestätigen. Es gibt einen separaten Abbrechen-Button. Der Rest der Charaktere und die Gruppenanmeldungen bleiben bestehen. Wird der Main gelöscht, bestimmt der Bot bei vorhandenen Twinks einen verbleibenden Main. Gruppen, die den gelöschten Charakter ausgewählt hatten, verwenden wieder den jeweiligen aktuellen Hauptcharakter.
4. **🔊 Im Sprachchat anzeigen:** Der Bot versucht, den **Discord-Servernickname** freiwillig auf den Hauptcharakternamen zu setzen, **ohne** Discord-Username dahinter. Der Name erscheint damit auch in allen Discord-Sprachkanälen dieses Servers. Erneutes Klicken stellt den vorherigen Nickname wieder her, sofern der Bot ihn noch selbst verwaltet.

Auch das öffentliche Charakter-Panel hat den Button **Sprachchat-Name an/aus**. Die gespeicherten Daten in `character_nickname_preferences` bleiben erhalten. Eine bestehende aktivierte Einstellung wird bei Änderung des Mains aktualisiert, aber nicht, wenn ein Mitglied seinen Nickname inzwischen selbst manuell geändert hat.

**Discord-Berechtigungen:** Der Bot benötigt *Nicknames verwalten* und eine Rolle über dem betreffenden Mitglied. **Der Serverinhaber ist nicht umbenennbar durch Bots**. Falls du Serverinhaber bist, ändere deinen eigenen serverbezogenen Anzeigenamen in Discord selbst auf `Grumok`; der Bot weist bei einem Fehlschlag darauf hin. Diese Einstellung beeinflusst nicht deinen globalen Discord-Benutzernamen.

Im Hauptprofil werden die aktiven Charaktere weiterhin ohne Stufenangabe angezeigt. Vorhandene historische Charakter-Level und Berufe werden weder abgefragt noch beim Bearbeiten gelöscht.

## Neue Mitglieder, Willkommens-Handbuch und Serverstruktur (Bot 1.0.19)

### Gewünschte Kanalreihenfolge

```text
🌋 WOW FOREVER | START
   #willkommen         (erster Kanal, Anleitung)
   #rollenwahl         (Rollen und Charakterregistrierung)
   #allgemein          (Community-Chat)
   #ankündigungen      (Server-News)
   #forever-news       (automatische WoW-Forever-News)
   #addons             (Addon-Empfehlungen/-Updates)

⚔️ WOW FOREVER | PVE
   #pve-gruppensuche
   #dungeons
   #raids-und-termine
   #pve-guides
   PvE – Leveln
   PvE – Dungeon
   PvE – Raid
   ➕ PvE-Gruppe erstellen

🏹 WOW FOREVER | PVP
   #pvp-gruppensuche
   #schlachtfelder
   #welt-pvp
   #pvp-guides
   PvP – Gruppe
   ➕ PvP-Gruppe erstellen

🔨 WOW FOREVER | CHARAKTERE
   #charaktere-und-berufe
   #handel-und-crafting
   #screenshots
```

Bei Botstart wird die Start-Kategorie oben einsortiert und werden die bekannten Kanäle in der logischen Reihenfolge angeordnet, **ohne andere Kanäle zu löschen**. Bereits vorhandene Rollen, Gruppenanmeldungen, Kanalinhalte und Berechtigungen bleiben erhalten. Der Bot benötigt zum Verschieben **Kanäle verwalten**. Unbekannte, eigene Kanäle werden nicht gelöscht.

### Automatisch aktualisierbare Willkommensseite

Die Willkommensseite in `#willkommen` bleibt dieselbe, möglichst **angeheftete** Discord-Nachricht. Im Gegensatz zu einer Flut neuer Nachrichten wird sie bei jedem Bot-Neustart / Funktionsupdate durch `publish_info` bearbeitet. Der Marker `corpsegrinder:welcome` und die gespeicherte ID `welcome_post` schützen vor doppelten Nachrichten. Die Texte für die Funktionsbereiche sind zentral als `WELCOME_FEATURES` in `community_features.py` abgelegt; bei neuen Features kann diese Tabelle mit erweitert werden. Der Fuß zeigt jeweils die aktuelle Bot-Version.

Im Willkommenstext stehen konkrete Schnellstart-Schritte, Kanalverweise und Funktionsbeschreibungen für Charakterregistrierung, Rollenwahl, Dungeon-/Levelgruppen, Sprachräume, Forever-News, Addons, PvP, Raids, Guides und Community.

**Admin-Befehle:**
- `/willkommen_aktualisieren` – dieselbe Willkommenskarte sofort bearbeiten und Kanalordnung prüfen
- `/willkommenshinweis text:<Nachricht>` – individuellen, persistenten Hinweis ergänzen
- `/willkommenshinweis text:aus` – Hinweis entfernen
- `/startkanaele_einrichten` – bestehende Startinformationen erneut erstellen/auffrischen

Neue Mitglieder erhalten ihre persönliche kurze Begrüßung in `#allgemein` mit Verweisen zu `#willkommen` und `#rollenwahl`. Damit bleibt die angeheftete Willkommens-Anleitung übersichtlich.

### Den tatsächlichen Discord-Startbildschirm für neue Mitglieder einrichten

**Der Bot kann keine Discord-App auf einem bestimmten Kanal öffnen und den Community-Onboarding-Server-Leitfaden nicht automatisch für dich konfigurieren.** Die Kategorie-Sortierung allein setzt keinen erzwungenen Startkanal.

Für einen echten ersten Orientierungsschirm sind zusätzliche **manuelle Discord-Einstellungen** nötig, am besten am Desktop:

1. Falls noch nicht geschehen, den Server als **Community** aktivieren.
2. Unter **Servereinstellungen → Onboarding** die **Standardkanäle** festlegen, die alle neuen Mitglieder sofort sehen: mindestens `#willkommen`, `#rollenwahl` und `#allgemein`.
3. Den **Server-Leitfaden** aktivieren und als **Begrüßungsschild** eine kurze Corpsegrinder-Einführung setzen.
4. Drei neue-Mitglieder-Aufgaben einrichten: **#willkommen lesen**, **Rollen und Ingame-Charakter registrieren**, **In #allgemein begrüßen oder Gruppe suchen**.
5. `#willkommen` als normalen, sichtbaren Kanal belassen, wenn er ganz oben in der Kanalliste stehen soll. Optional als Ressourcen-Seite verwenden, wenn Discord die Darstellung als Info-Handbuch stärker hervorheben soll – dabei wird der Kanal allerdings aus der normalen Kanalliste entfernt.

Discord-Hilfedokumentation: https://support.discord.com/hc/de/articles/11074987197975-Community-Onboarding-FAQ-H%C3%A4ufig-gestellte-Fragen und https://support.discord.com/hc/de/articles/13497665141655-FAQ-zum-Server-Leitfaden

Der Server-Leitfaden ist Discord-nativ; für zukünftige neue Funktionskarten erweitert der Bot weiterhin die angeheftete `#willkommen`-Seite.

## Lagerfeuer, Dungeon-Planer und Handelsbörse (1.0.22)

- Der Bot benennt vorhandene `#allgemein` und `#dungeons` beim ersten Start in `#lagerfeuer` und `#dungeon-planer` um. Die Discord-Kanal-IDs bleiben erhalten. Das setzt für die Bot-Rolle **Kanäle verwalten** voraus; bei einem Namenskonflikt wird nichts geändert oder gelöscht.
- `/kanalnamen_aktualisieren` wiederholt den sicheren Umbenennungsversuch.
- In `#handel-und-crafting` erscheint eine angeheftete Händler-Tafel. Nutzer wählen **Suche**, **Biete** oder **Handwerksauftrag** und füllen einen privaten Dialog mit Gegenstand/Dienstleistung, Beschreibung und optionalem Ingame-Preis/Materialien aus.
- Der Bot veröffentlicht eine Karte mit **Kontakt** (private Antwort mit Discord-Kontakt) und **Erledigt** (nur Ersteller/Admin). Die Karte bleibt als abgeschlossener Eintrag stehen; aktive Einträge bleiben auf der angehefteten Händler-Tafel sichtbar.
- **Meine Einträge** zeigt die letzten 12 eigenen Posts als private Links. Maximal sechs gleichzeitig offene Einträge pro Mitglied, um Spam zu reduzieren. Nur Ingame-Handel mit Gold/Gegenständen; kein Echtgeld.
- Bot-Rechte für den Handelskanal: Kanal ansehen, Nachrichten senden, Links einbetten, Nachrichtenverlauf anzeigen und zum Anheften Nachrichten verwalten. `/handel_aktualisieren` aktualisiert die Händler-Tafel.
- Keine zusätzliche HA-App und kein externer Bot erforderlich; die aktuelle SQLite-Datenbank bleibt erhalten.


## Horde-Paladin in WoW Forever (Bot 1.0.23)

Blizzard hat für WoW Forever den **Untoten Paladin (Verlassene)** auf Hordeseite bestätigt. Die Klasse ist in der Characterregistrierung, beim Bearbeiten von Charakterprofilen, als Slash-Choice und im Rollenmenü wählbar. Die passende `🛡️ Paladin`-Rolle wird beim ersten Start erstellt, falls sie fehlt und der Bot `Rollen verwalten` besitzt. Bestehende Rolle und Charaktere bleiben erhalten. Nach `/bot_update` den Bot neu starten und unter `#rollenwahl` die Auswahl prüfen.


## Interaktive Addon-Schmiede 1.0.24

Der bestehende `#addons`-Kanal enthält eine einzelne angeheftete **Addon-Schmiede**. Die vorhandene Nachricht wird über ihre alte ID bzw. den bisherigen Marker erneut verwendet; es wird kein zweites Dashboard angelegt.

- Kategorieauswahl in einem persistenten Dropdown: Quests & Leveln, Interface & Komfort, Karte & Navigation, Auktionshaus, Dungeon-Helfer, Inventar.
- Persönliche Addon-Details erscheinen ephemeral. Der Link-Button führt ausschließlich auf `https://www.curseforge.com/wow/addons/<slug>`.
- **Empfehlungen** listet den kuratierten Katalog, **Neu auf CurseForge** die letzten gespeicherten Forever-Dateien. Die Datei-Version gilt nur als erkannt, nicht als garantiert kompatibel.
- Die automatischen 6-Stunden-CurseForge-Checks und das Newsarchiv bleiben erhalten. Der Bot installiert selbst keine Addons.
- Die Optik verwendet einen goldbraunen Discord-Embed mit bestehender Horde-Grafik; die native Discord-Seitenleiste selbst kann keinen eigenen Skin erhalten. Bestehende Kategorie-Reihenfolge bleibt aus Sicherheitsgründen unangetastet.


## Vereinfachte Addon-Schmiede (1.0.25)

Die angeheftete Nachricht in `#addons` hat **keine Kategorie-Dropdowns oder verschachtelte Menüs** mehr. Stattdessen enthält sie drei eingebettete Discord-Karten in einem Beitrag: Fantasy-Header, Quests/Karten/Komfort und Kampf/Handel/Inventar. Alle acht Addons haben einen direkt klickbaren CurseForge-Link, keine private Zwischenansicht.

Die vorherige gespeicherte Post-ID `addons_intro_post_v114` wird weiterverwendet und der Footer-Marker `corpsegrinder:forever-addon-panel` bleibt stabil. Mit `view=None` werden die bisherigen Menüs beim Editieren entfernt. Die automatische Prüfung und bisherigen Addon-Update-Nachrichten bleiben bestehen.

