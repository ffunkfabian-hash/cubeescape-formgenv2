# Vorschlag: geerbte 01-Lücken und Kopfaufnahme

Alle 01-Parameterblöcke sind in 02 vorhanden und über dieselben Konstruktoren auf gemessene 02-Teile kalibriert. Profilreferenzen sind Vorgabe01, Zuordnung ist eine deklarierte Annahme, die Basis ist gemessen. Zubehör folgt seinem Elternprofil. Geänderte Vent-Cuts bauen die gemessene Vor-Boolean-Form neu auf; daher bleiben keine alten Vent-Löcher zurück.

Der aktuelle Vertrag aus `docs/robot.md` (01-Stand cf294c4) ist in 02 übernommen: zehn Einzelteile unter vier Baugruppen, A-Position in PARAMS und separate REFERENCE_PARAMS für die Quellabnahme. Schulterkappen drehen über pose.shoulder_open um den Arm-Drehpunkt. Die inneren, als interface_clearance markierten Aufnahme-Cuts bleiben beim Neubau von Zierfugen erhalten; sie sind unabhängig von diesen Profilmerkmalen. Geprüft wird die rechte Armkette ohne den fremden Schulterpanzer, in beiden Haltungen. Einzelheiten und Grenzen stehen in [roboterbasic-02.md](roboterbasic-02.md).

In 01 werden torso.chest.tip und torso.chest.plate nicht konsumiert. Das geschützte 01-Modell bleibt unverändert. 02 erfindet dafür keine abweichende Semantik, sondern meldet Änderungen sichtbar. Vorschlag: diese zwei Felder bei einer späteren, ausdrücklich beauftragten 01-Vertragskorrektur wirksam machen und beide Typen gemeinsam migrieren/testen.

Für weniger surface-Rückfälle fehlen im Kit unabhängig schließbare Loft-Enden, wechselnde Ringpunktzahlen und deklarative Solidify/Bevel/Cut-Reihenfolge. Keine solche Kernerweiterung im Auftrag.

Kopfaufnahme: Socket_Neck benennt den Drehpunkt, aber keinen Querschnitt, Einsteckbereich oder Freiraum. 01-Hals und 02-Brust kollidieren bei bloßer Punktanbindung. Vorschlag: Querschnitt, Anschlusstiefe und Freiraum versioniert ergänzen und 01/02 separat migrieren. Ankernamen/IDs bleiben bestehen. Kein Kopftausch freigegeben.
