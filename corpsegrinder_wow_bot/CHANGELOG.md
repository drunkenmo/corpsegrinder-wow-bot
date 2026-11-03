# Changelog

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
