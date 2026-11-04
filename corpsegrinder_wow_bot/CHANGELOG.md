# Changelog

## 1.0.24 – Warcraft-Fantasy Addon-Schmiede

- Der bestehende, angeheftete **#addons**-Einführungsbeitrag wird als **Addon-Schmiede** mit bronzegoldener Fantasy-Farbgebung, Horde-Grafik, kurzer Einleitung und sechs Kategorien überarbeitet. Die alte Nachrichten-ID und der gespeicherte Marker bleiben erhalten, damit keine doppelte Hauptkarte entsteht.
- **Interaktive, dauerhafte Discord-Auswahl:** Quests & Leveln, Interface & Komfort, Karte & Navigation, Auktionshaus, Dungeon-Helfer und Inventar. Ein zweites Dropdown öffnet private Detailkarten zu den kuratierten Addons; die Downloadseite ist über einen sicheren CurseForge-Link-Button erreichbar.
- Buttons **Empfehlungen** und **Neu auf CurseForge** zeigen private Übersichten, ohne den Kanal zu fluten. Ein fehlender Forever-Dateinachweis wird ausdrücklich als *nicht bestätigt* angezeigt.
- Bereits bestehende, automatisch veröffentlichte Forever-Dateimeldungen bleiben bestehen. Neue Update-Karten erhalten eine besser lesbare Fantasy-Optik. CurseForge-Abfrage weiterhin alle sechs Stunden, keine zusätzlichen API-Schlüssel.
- Discord-Einschränkung: Die native linke Kanalseitenleiste kann nicht mit eigenen Fantasy-Texturen oder Rahmen versehen werden. Die vorhandene Kanalstruktur und Emoji-Kategorien bleiben erhalten; nur die Darstellung **innerhalb von #addons** wird über Discord-Embeds, Bild und native Menüs umgestaltet.
- Die vorhandenen Rollen, Kanäle, Nachrichten, Datenbank und übrigen Bot-Funktionen werden nicht gelöscht oder verändert.


## 1.0.23 – Paladin der Verlassenen für WoW Forever

- **Paladin** als neunte Klasse für die Horde ergänzt, wie von Blizzard für untote Charaktere bestätigt.
- Paladin ist jetzt bei der privaten Charakterregistrierung, der Bearbeitung von Charakterprofilen, bei `/charakter` und in der Klassen-Rollenwahl verfügbar.
- Neue Rollenfarbe und 🛡️-Symbol. Falls auf dem Server noch keine Paladin-Rolle vorhanden ist, legt der Bot diese beim Start an (Berechtigung **Rollen verwalten** erforderlich); vorhandene Rollen werden wiederverwendet.
- Bestehende Charaktere, Gruppenanmeldungen, Kanalnachrichten, Namen und Berechtigungen bleiben unverändert. Für bestehende Panels genügt das reguläre Bot-Update mit Neustart.
- Offline-Regressionstests decken die neun Klassen, die Paladinregistrierung und die sichere Rollenerstellung ab.


## 1.0.22 – Lagerfeuer, Dungeon-Planer und Horde-Handelsbörse

- **Bestehende Kanäle umbenennen:** `#allgemein` → `#lagerfeuer`, `#dungeons` → `#dungeon-planer`. Der Bot verwendet die vorhandenen Discord-Kanäle und IDs; Nachrichten, Pins, Rollen, Einstellungen, Termine und Sprachkanäle bleiben erhalten. Bei vorhandenen Namenskonflikten wird nichts gelöscht oder zusammengeführt.
- Alle Verweise in Willkommensanleitung, Buttons, Beitrittsbegrüßung, Dungeonplaner und Termin-Sprachkanälen sind aktualisiert. Eine Rückwärtskompatibilität für die alten Kanalnamen greift, wenn die Discord-Rechte zum Umbenennen fehlen.
- Der Bot richtet im bestehenden `#handel-und-crafting` eine **angeheftete Händler-Tafel** mit den Buttons **Suche**, **Biete**, **Handwerksauftrag** und **Meine Einträge** ein.
- Einträge werden mit Titel, Details und optionalem Ingame-Preis/Materialien veröffentlicht und erhalten die Schaltflächen **Kontakt** und **Erledigt**. Abschließen kann nur der Ersteller oder ein Admin.
- Aktive Angebote stehen in einer aktualisierten Übersicht; jeder Nutzer kann bis zu 6 gleichzeitig offene Einträge veröffentlichen. Daten und Buttons überleben einen Neustart. **Keine Echtgeldgeschäfte**, externe API oder zusätzlichen Kanäle nötig.
- Admin-Kommandos: `/kanalnamen_aktualisieren` und `/handel_aktualisieren`. Neue und bestehende Bereiche werden bei Botstart aktualisiert, ohne alte Nachrichten zu entfernen.
- Offline-Tests für Migration, gesicherte Daten, persistente Handelsbuttons und Kanallinks.


## 1.0.21 – Deutsche Blizzard-Klassenänderungen direkt im News-Kanal

- Offizielle englische Blizzard-Blueposts werden zusätzlich auf klar erkennbare konkrete Werteänderungen untersucht (beispielsweise Schaden, Bedrohung, Abklingzeit und Dauer).
- Der Bot zeigt im bestehenden Discord-News-Embed eine begrenzte **deutschsprachige Auswahl** der Buffs/Nerfs mit Originalzahlen, nach Klassen sortiert. Unzuverlässig übersetzbare Sätze werden nicht als vermeintliche Fakten ausgegeben.
- Erster Teil bekannter Fähigkeiten erhält deutsche Namen; bei nicht sicher zugeordneten Bezeichnungen wird der Originalname beibehalten.
- Bestehende Bluepost-Karten von 1.0.20 werden einmalig ohne Doppelpostings auf das neue Format gebracht. Die SQLite-Datenbank und alle übrigen Bot-Funktionen bleiben erhalten.
- Kein Cloud-Übersetzungsdienst und kein API-Schlüssel nötig. Die verlinkten Originalnotizen enthalten weiterhin alle Details; die Discord-Karte ist ausdrücklich keine vollständige Übersetzung.


## 1.0.20 – Offizielle Blizzard-Blueposts und Entwicklernotizen

- Der Bot überwacht neben Blizzard-News, Wowhead und Community-Feeds jetzt auch die öffentliche WoW-Forever-Entwicklungskategorie im offiziellen Blizzard-Forum sowie den bekannten Beta-Entwicklungsnotizen-Thread.
- Nur bestätigte Blizzard-Mitarbeiterbeiträge werden berücksichtigt; normale Nutzerantworten bleiben außen vor.
- Neue oder innerhalb von 7 Tagen bearbeitete Entwicklerbeiträge landen mit deutschen Hinweisen, betroffenen Klassen und offiziellem Quelllink in `#forever-news`.
- Wird ein bereits veröffentlichter Beitrag bearbeitet, aktualisiert der Bot die vorhandene Discord-Karte statt eine zweite Meldung zu posten.
- `/forever_news_status` zeigt jetzt auch die Zahl der Blueposts; Quellenfehler werden getrennt im Status angezeigt. Alle bisherigen Nachrichtenquellen und Daten bleiben bestehen.
- Für das Update genügt wie gewohnt `/bot_update` und anschließend der normale Bot-Neustart; keine neue Home-Assistant-App nötig.


## 1.0.19 – Willkommensseite, Server-Einstieg und klare Kanalreihenfolge

- Die Start-Kategorie **🌋 WOW FOREVER | START** steht jetzt ganz oben. Darin ordnet der Bot seine bestehenden Kanäle als **#willkommen → #rollenwahl → #allgemein → #ankündigungen → #forever-news → #addons** an.
- Die Kategorien **PvE**, **PvP** und **Charaktere** folgen in dieser Reihenfolge; vorhandene zugehörige Text- und Sprachkanäle werden ebenfalls geordnet. Unbekannte/fremde Kanäle bleiben bestehen. Es wird nichts gelöscht und keine vorhandene Kanalberechtigung absichtlich synchronisiert oder überschrieben.
- Die automatisch erstellten News- und Addon-Kanäle räumen nur bei ihrer **Erstellung** die Startreihenfolge auf; die 30-Minuten-News- und 6-Stunden-Addon-Prüfungen verschieben die Kanäle nicht mehr.
- Die bestehende, angeheftete **#willkommen**-Karte ist nun ein umfassender Einstieg mit klaren Schritten (Rollen → Ingame-Name/Klasse → Community/Gruppen), einem **Kanal-Kompass** mit anklickbaren Verweisen zu Gruppenfindern, News, Addons, Guides, Handel und Charakteren sowie einer kurzen Erklärung zum Voice-Chat. Die Grafik und bisherigen Nachrichten bleiben erhalten.
- Willkommens-Informationen sind **versioniert und aus einer zentralen Funktionsliste** in `community_features.py` aufgebaut. Nach künftigen Feature-Updates wird bei jedem Botstart die **bestehende** Willkommensnachricht bearbeitet, ohne Duplikate zu posten. Das Marker-/ID-Verfahren wird beibehalten.
- `/willkommen_aktualisieren` (Admin) aktualisiert Anleitung und Kanalreihenfolge. `/willkommenshinweis text:...` (Admin) fügt einen individuellen, dauerhaft gespeicherten Hinweis hinzu; `text:aus` entfernt ihn.
- Im **#willkommen**-Kanal wird das Handbuch nicht mehr durch Begrüßungen neuer Mitglieder nach unten gedrückt: Neue Mitglieder werden in `#allgemein` begrüßt und direkt auf `#willkommen` und `#rollenwahl` verwiesen.
- Die Schnellzugriffe unter der Willkommensseite verlinken Rollenwahl, Allgemein, Dungeons, Levelgruppen und Forever-News.
- **Discord-Einschränkung:** Ein Bot kann nicht garantiert steuern, welche Seite die Discord-App beim ersten Betreten öffnet. Dafür sollte der Serverinhaber unter **Servereinstellungen → Onboarding** die Standardkanäle `#willkommen`, `#rollenwahl`, `#allgemein` auswählen und den **Server-Leitfaden** konfigurieren. Diese Discord-native Einstellung erfordert den Desktop und wird vom Bot nicht ohne Wissen des Administrators geändert.
- Offline-Tests für Kanalstruktur, Willkommen-Funktionsliste, automatische Aktualisierung und Admin-Hinweise.

## 1.0.18 – Charakterprofil bearbeiten/löschen und Hauptcharakter im Sprachchat

- Über **#rollenwahl → Meine Charaktere** stehen zusätzliche Buttons **Bearbeiten**, **Löschen** und **Im Sprachchat anzeigen** bereit. Die vorhandene Hauptcharakter-Auswahl bleibt.
- Bearbeiten: den eigenen Charakter auswählen und **Ingame-Namen sowie Klasse** in einem privaten Discord-Dialog ändern. Bereits gespeicherte Level/Berufe bleiben intern erhalten, erscheinen aber nicht im UI. Bereits gewählte Charaktere in Dungeon-/Levelgruppen werden auf den neuen Namen aktualisiert, ohne vorhandene Gruppenplätze anzutasten.
- Löschen: zuerst einen der eigenen Charaktere wählen, dann mit **Ja, endgültig löschen** bestätigen oder abbrechen. Wird der Hauptcharakter gelöscht, wird bei vorhandenen Twinks automatisch ein verbleibender Charakter als Main verwendet. Ohne Charakter bleibt kein Main gespeichert. Gruppenanmeldungen bleiben erhalten und verweisen gegebenenfalls auf den neuen Hauptcharakter.
- Sprachchat: Der freiwillige Servernickname ist jetzt **genau der Ingame-Name** (z. B. `Grumok`), ohne Discord-Namen hinter dem Trennzeichen. Discord verwendet diesen Servernickname auch in Sprachkanälen; die Änderung gilt daher serverweit, nicht nur im Voice-Chat.
- Der Button **Im Sprachchat anzeigen** im privaten Profil und **Sprachchat-Name an/aus** im öffentlichen Charakterpanel aktivieren bzw. deaktivieren die freiwillige Umbenennung. Der vorherige Servernickname wird möglichst wiederhergestellt. Der Bot überschreibt künftig keinen Nickname, den ein Mitglied nachträglich selbst geändert hat.
- Discord erlaubt Bots **nicht**, die Servernickname des Serverinhabers zu ändern. Auch gleichrangige/höherrangige Mitglieder sind nicht editierbar; der Bot meldet dann das Problem und empfiehlt, den Servernickname über das eigene Discord-Serverprofil selbst zu setzen.
- Der Slash-Befehl `/charakter_loeschen` verwendet dieselbe sichere Datenbereinigung wie der Button. Alle bestehenden Profile, Rollen und Gruppen bleiben weiterhin bestehen; keine zusätzliche Verifizierung.
- Offline-Tests für Namensänderung, Klassenänderung, Löschung, Daten- und Gruppen-Erhalt, Stimme-Anzeigen und UI-Verfügbarkeit.

## 1.0.17 – Charakterregistrierung ohne Level, direkt in #rollenwahl

- Ingame-Charaktere benötigen **nur Ingame-Name und Klasse**. `/charakter` fragt weder Stufe noch Berufe ab.
- Bereits gespeicherte Charaktere, Klassen, Stufen und Berufe bleiben in der bestehenden SQLite-Tabelle erhalten. Neue Charaktere bekommen lediglich einen internen Standardwert in der unveränderten Alt-Tabelle; dieser Wert wird im Bot nirgendwo angezeigt.
- Alle Charakterkarten, privaten Profile, Hauptcharakter-Dropdowns, Gruppen-Anmeldeauswahl und Dungeon-/Levelgruppen-Spielerlisten zeigen **Name + Klasse**, ohne individuelle Charakterstufen. Die für die Gruppenplanung benötigten **Levelbereiche von Levelgruppen** bleiben natürlich bestehen.
- In `#rollenwahl` wird automatisch eine eigenständige, möglichst angepinnte **Charakter-Karte** mit **Charakter registrieren**, **Meine Charaktere** und **Servername an/aus** eingerichtet. Funktioniert auch am Handy ohne Slash-Befehle.
- Button **Charakter registrieren** → private Klassen-Auswahl → Namenseingabe per Discord-Modal → sofortiges Speichern. Bestehende Einträge können über die gleiche UI aktualisiert werden; keine Freischaltung nötig.
- Button **Meine Charaktere** → privates Profil mit **Hauptcharakter ändern**. Hauptcharakter und Twinks funktionieren wie bisher.
- Button **Servername an/aus** aktiviert/deaktiviert den optionalen Ingame-Nicknamen (sofern der Bot über die nötigen Discord-Rechte verfügt); andernfalls bleibt der bestehende Servernickname unverändert.
- Der Bot aktualisiert die vorhandene Willkommenskarte und informiert neue Mitglieder beim Beitritt ausdrücklich über **Rollen wählen → Charakter registrieren**.
- Bei Neustarts bleibt das Charakter-Panel verfügbar und verwendet sein gespeichertes Nachrichten-ID; eine erneute Installation erzeugt keine endlosen Duplikate.
- Charakterdaten und alte Gruppenanmeldungen bleiben erhalten. Bestehende Spieler können ihre Daten jederzeit über die Buttons pflegen, ohne eine neue Registrierung zu beantragen.
- Offline-Regressionstests prüfen Registrierung, Datenbestand und persistente Buttons. Installierbar über `/bot_update`.

## 1.0.16 – Ingame-Namen, Hauptcharakter, Twinks und Gruppen-Anmeldung

- Die bestehende `characters`-Datenbank bleibt bestehen; die neuen Zuordnungen für Hauptcharakter, pro-Termin-Charakter und freiwillige Discord-Nicknames werden in eigenen SQLite-Tabellen gespeichert.
- `/charakter` legt Charaktere an oder aktualisiert sie (max. 25 pro Discord-Mitglied). Der erste eingetragene Charakter wird automatisch Hauptcharakter; bereits vorhandene Profile werden automatisch weiterverwendet.
- `/hauptcharakter name:<Name>` setzt den Main; `/meine_charaktere` zeigt eine private Übersicht aller Hauptcharaktere und Twinks.
- Dungeon- und Levelgruppen-Anmeldebuttons fragen bei mehreren Charakteren über ein nur für den jeweiligen Spieler sichtbares Dropdown, welcher Charakter teilnimmt. Bei einem Charakter erfolgt die Auswahl direkt; ohne registrierten Charakter wird die Nutzung von `/charakter` empfohlen.
- Auch die Dungeon- und Levelgruppen-Erstellungsassistenten besitzen eine Charakterauswahl. Der Hauptcharakter ist vorausgewählt. Bei Slash-Erstellung wird automatisch der Hauptcharakter verwendet; über den neuen Button `Charakter ändern` lässt er sich nachträglich wechseln.
- Gruppenkarten zeigen die Ingame-Namen mit Klasse und Stufe an erster Stelle, gefolgt vom klickbaren Discord-Account. Auch persönliche Gruppen-Erinnerungen nennen den Ingame-Namen.
- Die vorhandene Anmeldung eines Spielers bleibt anhand seiner Discord-ID einzigartig: maximal ein Platz pro Dungeon oder Levelgruppe, auch mit mehreren Twinks. Keine Verifizierung der Spieler im Spiel und keine speziellen Multiboxing-Regeln.
- Bereits vorhandene Gruppen, Anmeldungen und Charaktere bleiben erhalten. Wer neu einen Charakter anlegt, sieht dessen Namen auch in bestehenden offenen Anmeldungen. Individuelle pro-Termin-Auswahlen ändern sich nicht, wenn der globale Hauptcharakter später wechselt.
- `/ingame_nickname aktiv:true` setzt *auf ausdrücklichen Wunsch* einen Servernickname in der Form `Grumok | Discordname`; `aktiv:false` versucht, den vorherigen Nicknamen wiederherzustellen. Erfordert Nicknames-verwalten-Berechtigung und ausreichende Rollenposition, keine automatische Zwangsumbenennung.
- Alle Änderungen laufen wie gewohnt über `/bot_update`; keine Home-Assistant-App-Neuinstallation nötig.

## 1.0.15 – Forever-News direkt im Discord-Chat lesen

- Jede neue Forever-News wird in derselben Discord-Nachricht als deutschsprachiger Überblick angezeigt, ohne zusätzlichen Button „Ausführlicher lesen“.
- Build- und Changelog-Meldungen zeigen nun konkrete veröffentlichte Fakten, etwa Buildnummern, neue/geänderte/entfernte Zauber und Gegenstände, Klassen- und Talenthinweise.
- Der Link auf den Originalartikel ist als Quellenbeleg weiterhin optional verfügbar, aber zum Lesen der Kurzfassung nicht erforderlich.
- RSS-/Atom-Content wird zur Ermittlung tatsächlicher Zahlen berücksichtigt; ganze fremde Artikel werden aus Urheberrechtsgründen nicht kopiert.
- Der Bot nutzt nachvollziehbare faktenbasierte Vorlagen. Wenn eine detailgetreue deutsche Inhaltswiedergabe technisch nicht möglich ist, meldet er diese Grenze, statt Inhalte zu erfinden.
- Bereits veröffentlichte Forever-Community-News werden anhand der gespeicherten Nachrichten-ID nachträglich im vorhandenen Post aktualisiert, soweit Artikel/Feed noch verfügbar sind; keine Doppelpostings.
- Wie bisher per /bot_update installierbar, keine neue HA-App und keine zusätzlichen API-Schlüssel nötig.

## 1.0.14 – Mehr Forever-News und neuer #addons-Kanal

- Der bisherige #forever-news-Kanal wird nicht mehr ausschließlich aus seltenen Blizzard-Artikeln gespeist: die klar gekennzeichneten Communityquellen Wowhead (/forever/news) und wow-forever.gg (RSS) ergänzen die offiziellen Blizzard-Posts.
- Das angepinnte Nachrichten-Panel zeigt die Quellen klar getrennt. Drei echte Forever-Artikel bei Wowhead werden als Einstieg empfohlen, selbst wenn offizielle News fehlen oder Quellen gerade nicht erreichbar sind.
- Community-News nur mit einem lesbaren Veröffentlichungsdatum innerhalb der letzten sieben Tage. Pro Prüflauf maximal fünf Beiträge, keine Doppelpostings; HTML und RSS-Feeds werden sicher gefiltert.
- Neuer, eigener Textkanal #addons in der WoW-Start-Kategorie direkt unter #forever-news und über #rollenwahl.
- Angepinnte Forever-Addon-Empfehlungsliste mit Questie, Leatrix Plus/Maps, Auctionator, Baganator, TomTom, DBM und QuestForever, jeweils mit Links zur eigenen CurseForge-Projektseite.
- Automatische CurseForge-Prüfung alle sechs Stunden: ausdrücklich als Forever (Spielversion 1.60.1) ausgewiesene Dateien erkennen, Updates bekannter Addons veröffentlichen und neue Forever-Projekte aus der Suche entdecken.
- Entdeckte, noch nicht kuratierte Projekte erhalten einen eigenen Warnhinweis; es gibt keine automatischen Addon-Downloads oder Installationen.
- Neuer Befehl /addons_pruefen für Administratoren sowie /addons_status und erweitertes /forever_news_status.
- Fehlgeschlagene Abfragen werden protokolliert; die statischen Empfehlungen bleiben im Discord erhalten.
- Keine Änderungen an Home Assistant / Python-Abhängigkeiten; Installation weiterhin über /bot_update.

## 1.0.13 – #forever-news: Offizielle Blizzard-Neuigkeiten
- Neuer Textkanal #forever-news in der WoW-Start-Kategorie direkt unter #ankündigungen, vor #rollenwahl.
- Ausschließlich deutsche offizielle Blizzard-Artikel zu World of Warcraft: Forever; andere Retail-, Midnight- und Classic-Nachrichten ausgeschlossen.
- Automatische Prüfung alle 30 Minuten via offizieller Blizzard-News-Übersicht.
- Beim ersten Start werden passende Meldungen aus den letzten 48 Stunden anhand des ursprünglichen Veröffentlichungsdatums nachgetragen. Fehlen aktuelle Artikel, bleibt nur die angepinnte Info-Karte.
- Permanente SQLite-Artikel-ID-Speicherung verhindert wiederholte Veröffentlichungen nach Neustarts.
- /forever_news_pruefen (Admin) prüft manuell; /forever_news_status zeigt letzte Prüfung und Artikelzahl.
- Fehler beim Quellenabruf werden protokolliert, ohne erfundene Meldungen zu posten.
- Kein Home-Assistant-App-Update nötig; /bot_update installiert die Änderung.

## 1.0.12 – Das große Corpsegrinder-Horde-Update

- Neuer Warcraft-/Lagerfeuer-Look: Willkommen mit originalem Corpsegrinder-Banner, neue Rollenwahl und humorvolle Bildpanels für Dungeon- und Levelgruppen.
- Dynamische Gruppenzentralen zeigen die nächsten drei Termine inklusive Belegung; die Buttons bleiben aufrufbar.
- Private Gruppen-Erinnerungen 15 Minuten vor Spielbeginn. Jeder Spieler kann sie über /erinnerungen oder in #rollenwahl aus- und einschalten.
- Sobald ein Dungeon 5/5 Spieler erreicht, erhalten alle Teilnehmer eine Nachricht, falls Benachrichtigungen aktiv sind.
- Geplante PvE-Sprachkanäle entstehen 15 Minuten vor Start nur für vollständige Dungeon-/Levelgruppen (5/5). Wird die Gruppe später vor dem Start voll, öffnet der Raum sofort.
- Sprachräume haben fünf Plätze und den jeweiligen Dungeon/das Levelgebiet samt Termin im Namen; ungenutzte Räume werden nach einer Stunde automatisch bereinigt, genutzte Räume nach Verlassen des letzten Spielers.
- Gruppenkarten erhalten eine Stunde nach Start den Status Abgelaufen; fünf Minuten danach wird die Discord-Nachricht entfernt (Daten bleiben archiviert).
- Organisatoren und Administratoren können ihre Gruppen über den neuen Abschließen-Button sofort aus den aktiven Übersichten nehmen; fünf Minuten danach verschwindet die Karte.
- Der separate alte Bereich 🔒 WOW FOREVER | GILDE und nur seine drei bekannten Kanäle werden beim ersten Start gezielt gelöscht. Andere Bereiche und unbekannte Unterkanäle werden geschützt.
- Alle Zeitsteuerungen und Erinnerungslieferungen werden in SQLite gespeichert, funktionieren also nach Neustarts weiter.
- Alle gewöhnlichen Änderungen werden wie gewohnt mit /bot_update eingespielt.

## 1.0.11 – Dungeon-Planer verlegt, Levelgruppen und automatischer Voice-Beitritt
- Neue Dungeon-Termine und angeheftetes Dungeon-Dashboard erscheinen nun in #dungeons (PvE-Textkanal). Das alte, vom Bot erstellte Panel in #pve-gruppensuche wird beim Wechsel gezielt entfernt; bestehende Termin-Karten bleiben erhalten.
- Neue Levelgruppen-Steuerzentrale in #pve-gruppensuche mit Gebietswahl (Horde-Classic-Gebiete und eigenes Ziel), Levelbereich, Tag/Stunde/Minuten und optionalem Hinweis.
- Levelgruppen für bis zu fünf Spieler mit "Dabei sein", "Abmelden", Terminsuche und Meine-Gruppen-Übersicht.
- /levelpanel erneuert die Level-Steuerzentrale; /leveltermin_verschieben und /leveltermin_absagen helfen Organisatoren.
- Der Ersteller temporärer PvE- und PvP-Sprachkanäle wird durch den Bot direkt in den neuen Kanal verschoben. Fehlt das Recht "Mitglieder verschieben", gibt der Bot eine verständliche Fehlermeldung aus und vermeidet verwaiste Räume.
- Alle neuen Gruppen und Anmeldungen bleiben in SQLite und nach Bot-Neustarts erhalten. Andere Spielekanäle werden nicht verändert.
- Keine neue Home-Assistant-App nötig, Update über /bot_update.

## 1.0.10 – PvE-Gruppenplaner zum Anklicken
- Eine öffentliche Dungeon-Steuerzentrale in #pve-gruppensuche mit drei dauerhaften Buttons.
- Private Zwei-Schritt-Auswahl für Instanz und Rolle sowie Datum/Stunde/Minute per Dropdown.
- Auswahl für die nächsten 21 Tage und alle 24 Stunden, Minuten in 15-Minuten-Schritten.
- Bekannte Classic-Instanzen als Dropdown; eigene Instanz/Notiz bei Bedarf als Texteingabe.
- Bestehende Planungs-, Anmelde- und Absagefunktionen weiterverwendet.
- Automatische Veröffentlichung und versuchtes Anpinnen; bei fehlenden Pin-Rechten manuell anpinnen.
- Neue Admin-Funktion /gruppenpanel aktualisiert das Panel ohne doppelte Nachrichten.
- Direktlink im Kanalthema, falls noch kein eigenes Kanalthema existiert.
- Das Menü bleibt nach Bot-Neustarts nutzbar; persönliche Zwischenauswahlen sind nur temporär.

## 1.0.9 – Planbare Instanzgruppen
- Neues /gruppe_planen mit Instanz, heute/morgen/übermorgen oder Datum, Uhrzeit (Deutschland), eigener Rolle und Notiz.
- Interaktive Anmeldeschaltflächen für genau 1 Tank, 1 Heiler, 3 DD, inklusive Rollenwechsel und Abmelden.
- /termine listet die nächsten Gruppen mit Links zur Anmeldung.
- /termin_verschieben und /termin_absagen können Organisator oder Admin verwenden.
- Persistente SQLite-Termine und Anmeldebuttons nach Neustarts.
- Vorschläge für bekannte Classic-Instanzen und Prüfung der Sommer-/Winterzeit.

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
