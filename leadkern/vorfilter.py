# -*- coding: utf-8 -*-
"""Vorfilter: Ketten/Filialen und Institutionen erkennen.

Zielgruppe der Fabriken sind inhabergeführte Betriebe — Konzerne,
Träger, Behörden, Vereine und Verzeichnis-Eigeneinträge fliegen raus.
"""

from __future__ import annotations

import re

from .normalisierung import firmenname

_INSTITUTION_MUSTER = re.compile(
    r"\b(e\.\s?v\.|ev\b|verein|stiftung|ggmbh|kommunal|stadt(?:werke|verwaltung)?|"
    r"gemeinde|landkreis|bezirksamt|amt\b|behoerde|behörde|ministerium|"
    r"kirche|kirchengemeinde|bistum|diakonie|caritas|awo\b|drk\b|malteser|"
    r"johanniter|arbeiterwohlfahrt|klinik|klinikum|krankenhaus|krankenkasse|"
    r"universitaet|universität|hochschule|volkshochschule|vhs\b|"
    r"grundschule|gesamtschule|gymnasium|berufsschule|jobcenter|agentur\s+für\s+arbeit)\b",
    re.IGNORECASE,
)

_PORTAL_MUSTER = re.compile(
    r"\b(branchenbuch\w*|verzeichnis\w*|portal\w*|gelbe\s?seiten|11880|dasoertliche|"
    r"das\s?örtliche|golocal|yelp|werkenntdenbesten|firmenwissen|northdata)",
    re.IGNORECASE,
)

_KETTEN_MUSTER = re.compile(
    r"\b(filiale|niederlassung|zweigstelle|franchise|zentrale|"
    r"standort\s+[a-zäöü]|deutschland\s?gmbh|holding|group|konzern)\b",
    re.IGNORECASE,
)


def ist_institution(firma: dict) -> bool:
    """Portale, Verzeichnis-Eigeneinträge, Vereine, Träger, Behörden usw."""
    text = " ".join(str(firma.get(f) or "") for f in ("name", "branche", "website"))
    return bool(_INSTITUTION_MUSTER.search(text) or _PORTAL_MUSTER.search(text))


def ist_kette_oder_filiale(firma: dict, alle_treffer: list[dict]) -> bool:
    """Kette/Filiale: Ketten-Indiz im Namen ODER derselbe (normalisierte)
    Name taucht im selben Lauf an >= 3 verschiedenen PLZ auf."""
    name = str(firma.get("name") or "")
    if _KETTEN_MUSTER.search(name):
        return True
    norm = firmenname(name)
    if not norm:
        return False
    plzs = {
        str(t.get("plz") or "").strip()
        for t in alle_treffer
        if firmenname(str(t.get("name") or "")) == norm and str(t.get("plz") or "").strip()
    }
    return len(plzs) >= 3
