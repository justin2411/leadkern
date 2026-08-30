# -*- coding: utf-8 -*-
"""Dedupe-Schlüssel und Zusammenführen von Treffern verschiedener Quellen."""

from __future__ import annotations

from .normalisierung import firmenname, telefon


def schluessel(firma: dict) -> dict:
    """Beide Dedupe-Schlüssel einer Firma: telefon_key und name_plz_key.

    Fehlt die Grundlage (keine Nummer bzw. kein Name+PLZ), ist der
    jeweilige Schlüssel None.
    """
    tel = telefon(firma.get("telefon") or "")
    name_norm = firmenname(firma.get("name") or "")
    plz = (firma.get("plz") or "").strip()
    return {
        "telefon_key": tel["key"],
        "name_plz_key": f"{name_norm}|{plz}" if name_norm and plz else None,
    }


def zusammenfuehren(treffer: list[dict]) -> list[dict]:
    """Treffer-Liste (ggf. aus mehreren Quellen) zu Firmen zusammenführen.

    Gleiche Firma = gleicher telefon_key ODER gleicher name_plz_key.
    Beim Zusammenführen werden die Quellen-Badges vereinigt (unique nach
    `quelle`) und leere Felder aus späteren Treffern aufgefüllt — der
    erste Treffer gewinnt bei Konflikten.
    """
    firmen: list[dict] = []
    nach_tel: dict[str, dict] = {}
    nach_name_plz: dict[str, dict] = {}

    for t in treffer:
        keys = schluessel(t)
        vorhanden = None
        if keys["telefon_key"] and keys["telefon_key"] in nach_tel:
            vorhanden = nach_tel[keys["telefon_key"]]
        elif keys["name_plz_key"] and keys["name_plz_key"] in nach_name_plz:
            vorhanden = nach_name_plz[keys["name_plz_key"]]

        if vorhanden is None:
            firma = dict(t)
            firma["quellen"] = _quellen_liste(t)
            firmen.append(firma)
            vorhanden = firma
        else:
            for feld, wert in t.items():
                if feld == "quellen":
                    continue
                if wert and not vorhanden.get(feld):
                    vorhanden[feld] = wert
            bekannte = {q.get("quelle") for q in vorhanden["quellen"]}
            for q in _quellen_liste(t):
                if q.get("quelle") not in bekannte:
                    vorhanden["quellen"].append(q)
                    bekannte.add(q.get("quelle"))

        # Register auch nach dem Auffüllen aktualisieren — eine Firma kann
        # ihren zweiten Schlüssel erst durch einen späteren Treffer bekommen.
        keys_neu = schluessel(vorhanden)
        if keys_neu["telefon_key"]:
            nach_tel[keys_neu["telefon_key"]] = vorhanden
        if keys_neu["name_plz_key"]:
            nach_name_plz[keys_neu["name_plz_key"]] = vorhanden

    return firmen


def _quellen_liste(t: dict) -> list[dict]:
    quellen = t.get("quellen")
    if isinstance(quellen, list) and quellen:
        return [dict(q) for q in quellen]
    if t.get("quelle"):
        return [{"quelle": t["quelle"]}]
    return []
