# -*- coding: utf-8 -*-
"""Normalisierung von Firmennamen, Telefonnummern und Adressen.

Die Schlüssel-Semantik (telefon_key als 49…-Ziffernfolge, Firmenname als
kompakte a-z0-9-Folge) ist mit der Fabrik-2-App abgestimmt — Änderungen
hier ändern das Dedupe-Verhalten beider Fabriken.
"""

from __future__ import annotations

import re

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})

# Mehrwort-Rechtsformen zuerst (als Phrase), dann Einzel-Token.
_RECHTSFORM_PHRASEN = [
    r"gmbh\s*&\s*co\.?\s*kg",
    r"ug\s*\(haftungsbeschraenkt\)",
    r"ug\s*haftungsbeschraenkt",
    r"e\.\s*k\.",
    r"e\.\s*kfr\.",
    r"e\.\s*kfm\.",
    r"e\.\s*v\.",
    r"partg\s*mbb",
]
_RECHTSFORM_TOKEN = {
    "gmbh", "ggmbh", "mbh", "ug", "ag", "kg", "ohg", "gbr", "partg",
    "ek", "ev", "co", "inh", "inhaber", "inhaberin", "nachf", "vorm",
}

_GEWERKE = {
    "fenstermontage", "montage", "montagen", "bau", "baugeschaeft", "bauservice",
    "friseur", "friseursalon", "salon", "kosmetik", "kosmetikstudio",
    "fusspflege", "nagelstudio", "pflege", "pflegedienst", "hauskrankenpflege",
    "elektro", "elektrotechnik", "elektroservice", "sanitaer", "heizung",
    "haustechnik", "maler", "malerbetrieb", "malermeister", "lackierer",
    "dachdeckerei", "dachdecker", "zimmerei", "schreinerei", "tischlerei",
    "geruestbau", "trockenbau", "fliesen", "fliesenleger", "estrich",
    "fotografie", "foto", "fotostudio", "catering", "partyservice",
    "umzuege", "transporte", "spedition", "kurierdienst", "hausmeisterservice",
    "gebaeudereinigung", "reinigung", "glasreinigung", "gartenbau",
    "gartenpflege", "landschaftsbau", "physiotherapie", "krankengymnastik",
    "massage", "praxis", "naturheilpraxis", "heilpraxis", "immobilien",
    "hausverwaltung", "versicherungen", "finanzberatung", "steuerberatung",
    "buchhaltung", "nachhilfe", "musikschule", "fahrschule", "sprachschule",
    "baeckerei", "backstube", "konditorei", "metzgerei", "fleischerei",
    "autohaus", "kfz", "autoservice", "werkstatt", "reifenservice",
    "yoga", "yogastudio", "pilates", "coaching", "beratung", "consulting",
    "webdesign", "mediendesign", "werbetechnik", "schluesseldienst",
    "bestattungen", "gastronomie", "eventservice", "hebammenpraxis",
}


def _falte(text: str) -> str:
    return text.lower().translate(_UMLAUTE)


def firmenname(name: str) -> str:
    """Vergleichsform eines Firmennamens: Kleinschreibung, Umlaute
    ausgeschrieben, Rechtsformen entfernt, nur noch a-z0-9 (kompakt).

    „Marx Fenstermontage GmbH & Co. KG" -> „marxfenstermontage"
    """
    s = _falte(name or "")
    for phrase in _RECHTSFORM_PHRASEN:
        s = re.sub(phrase, " ", s)
    tokens = re.split(r"[^a-z0-9]+", s)
    tokens = [t for t in tokens if t and t not in _RECHTSFORM_TOKEN]
    return "".join(tokens)


_NAMENS_STOP = {"soehne", "sohn", "toechter", "partner", "team", "kollegen", "meister", "und"}


def inhaber_kandidat(name: str) -> str | None:
    """Nachnamen-Kandidat aus einem Firmennamen wie „Marx Fenstermontage".

    Heuristik: es gibt ein Gewerk-Wort UND höchstens zwei weitere
    „Namens-Wörter" (großgeschrieben, keine Rechtsform, keine Ziffern) —
    dann ist das letzte Namens-Wort der Kandidat („Peter Marx
    Fenstermontage" -> „Marx"). Sonst None — lieber kein Name als ein
    falscher.
    """
    tokens = re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]*", name or "")
    gewerk_dabei = False
    kandidaten: list[str] = []
    for t in tokens:
        gefaltet = _falte(t)
        if gefaltet in _GEWERKE:
            gewerk_dabei = True
            continue
        if gefaltet in _RECHTSFORM_TOKEN or gefaltet in _NAMENS_STOP or len(t) < 3:
            continue
        if t[0].isupper():
            kandidaten.append(t)
    if gewerk_dabei and 1 <= len(kandidaten) <= 2:
        return kandidaten[-1]
    return None


_MOBIL_VORWAHLEN = ("4915", "4916", "4917")


def telefon(roh: str) -> dict:
    """Deutsche Telefonnummer normalisieren.

    Rückgabe: {e164, key, art} mit art in mobil|festnetz|ungueltig.
    key ist die reine Ziffernfolge ab Ländercode (49…), identisch mit
    dem telefon_key der Fabrik-2-App.
    """
    ungueltig = {"e164": None, "key": None, "art": "ungueltig"}
    ziffern = re.sub(r"\D", "", roh or "")
    if not ziffern:
        return ungueltig
    if ziffern.startswith("00"):
        ziffern = ziffern[2:]
    elif ziffern.startswith("0"):
        ziffern = "49" + ziffern[1:]
    if not ziffern.startswith("49"):
        return ungueltig
    # Schreibweise „+49 (0) 151 …" — die eingeklammerte 0 fällt weg
    if ziffern.startswith("490"):
        ziffern = "49" + ziffern[3:]
    # 49 + 8–13 Rufnummern-Ziffern; Wiederholungs-Attrappen (0000000…) raus
    rumpf = ziffern[2:]
    if not (8 <= len(rumpf) <= 13) or len(set(rumpf)) == 1:
        return ungueltig
    art = "mobil" if ziffern.startswith(_MOBIL_VORWAHLEN) else "festnetz"
    return {"e164": f"+{ziffern}", "key": ziffern, "art": art}


def adresse(roh: str) -> dict:
    """Adress-Zeile in {strasse, plz, ort} zerlegen.

    „Musterstraße 12, 12345 Berlin" — die PLZ (5 Ziffern) ist der Anker;
    ohne PLZ bleibt alles außer strasse leer.
    """
    text = re.sub(r"\s+", " ", (roh or "")).strip()
    m = re.search(r"\b(\d{5})\b", text)
    if not m:
        return {"strasse": text.strip(" ,;"), "plz": "", "ort": ""}
    strasse = text[: m.start()].strip(" ,;")
    ort = text[m.end():].strip(" ,;")
    ort = re.split(r"[,;]", ort)[0].strip()
    return {"strasse": strasse, "plz": m.group(1), "ort": ort}
