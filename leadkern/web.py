# -*- coding: utf-8 -*-
"""Impressum finden/auslesen und URLs prüfen.

⚠️ Netzwerkzugriff erlaubt (impressum_finden, url_pruefen) — beide gehen
über `hole_seite`, das den ehrlichen User-Agent nutzt und injektierbar
ist (Tests laufen offline). `impressum_auslesen` ist rein (nur HTML-Text),
optional mit KI-Nachschlag über einen hereingereichten Callable.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request

from .drossel import Quelle
from .normalisierung import firmenname

# Versionierter Prompt für den optionalen KI-Nachschlag (Modul 7).
IMPRESSUM_PROMPT_VERSION = "1.0"
IMPRESSUM_PROMPT = (
    "Du liest den Text eines deutschen Impressums. Gib NUR JSON zurück mit "
    "den Feldern: vorname, nachname, rolle (z. B. Inhaberin, Geschäftsführer), "
    "email, telefon, hrb (Handelsregister-Nr. oder leer), ist_einzelperson "
    "(true, wenn eine einzelne natürliche Person den Betrieb führt). "
    "Erfinde nichts — unbekannte Felder bleiben leer.\n\nImpressum:\n"
)

_IMPRESSUM_LINK = re.compile(r"href=[\"']([^\"']*(?:impressum|imprint|legal-notice)[^\"']*)[\"']", re.IGNORECASE)
_TITEL = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_PARKPLATZ_MARKER = (
    "domain steht zum verkauf", "domain kaufen", "diese domain wurde",
    "sedo", "parkingcrew", "parked domain", "domain parking", "godaddy",
    "buy this domain", "united-domains",
)

# Namen laufen NIE über einen Zeilenumbruch — sonst wird die Folgezeile
# („Musterweg 3", „Tel:") als Namensbestandteil eingesammelt.
_NAME = r"([A-ZÄÖÜ][a-zäöüß\-]+(?:[ \t][A-ZÄÖÜ][a-zäöüß\-]+){1,2})"
_ROLLEN_MUSTER = [
    (re.compile(rf"Inhaber(?:in)?\s*:?\s*{_NAME}"), "Inhaber"),
    (re.compile(rf"Gesch[äa]ftsf[üu]hr(?:er(?:in)?|ung)\s*:?\s*{_NAME}"), "Geschäftsführer"),
    (re.compile(rf"Vertreten\s+durch\s*:?\s*{_NAME}"), "Vertretungsberechtigt"),
    (re.compile(rf"Vertretungsberechtigt(?:er?)?\s*:?\s*{_NAME}"), "Vertretungsberechtigt"),
    (re.compile(rf"Verantwortlich(?:e[r]?)?(?:\s+(?:i\.?\s?S\.?\s?d\.?|im Sinne des?)[^:\n]{{0,40}})?\s*:?\s*{_NAME}"), "Verantwortlich"),
    (re.compile(rf"Betreiber(?:in)?\s*:?\s*{_NAME}"), "Betreiber"),
    (re.compile(rf"Kontakt\s*:?\s*{_NAME}"), "Kontakt"),
]
_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_TELEFON = re.compile(r"(?:Telefon|Tel\.?|Fon|Mobil|Handy)\s*:?\s*((?:\+|0)[\d\s/()\-\.]{6,20}\d)", re.IGNORECASE)
_HRB = re.compile(r"\bHR\s?[AB]\s?-?\s?\d{3,6}\b", re.IGNORECASE)
_KAPITALGESELLSCHAFT = re.compile(r"\b(gmbh|aktiengesellschaft|\bag\b|ug\s*\(|ug\s+haftungs)", re.IGNORECASE)


def hole_seite(url: str, timeout: int = 15) -> tuple[int, str]:
    """(Status, HTML) einer Seite — ehrlicher User-Agent, kein Umgehen."""
    req = urllib.request.Request(url, headers={"User-Agent": Quelle("web").user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as antwort:
            roh = antwort.read(1_500_000)
            return antwort.status, roh.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, ""
    except Exception:
        return 0, ""


def impressum_finden(domain: str, hole=hole_seite) -> str | None:
    """Impressum-URL einer Domain finden (Netzwerk).

    1. Startseite laden und Impressum-/Imprint-Links suchen,
    2. sonst die üblichen Pfade (/impressum, /imprint) direkt probieren.
    """
    basis = domain if domain.startswith("http") else f"https://{domain}"
    basis = basis.rstrip("/")
    status, html = hole(basis)
    if status == 200 and html:
        m = _IMPRESSUM_LINK.search(html)
        if m:
            return urllib.parse.urljoin(basis + "/", m.group(1))
    for pfad in ("/impressum", "/imprint", "/impressum.html"):
        status, html = hole(basis + pfad)
        if status == 200 and html:
            return basis + pfad
    return None


def _text_aus_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ").replace("&auml;", "ä") \
        .replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&szlig;", "ß") \
        .replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
    return re.sub(r"[ \t]+", " ", text)


def impressum_auslesen(html: str, ki_abfrage=None) -> dict:
    """Impressum-HTML regelbasiert auslesen; optional KI-Nachschlag.

    Rückgabe: {vorname, nachname, rolle, email, telefon, hrb,
    ist_einzelperson}. `ki_abfrage` (Callable[str] -> dict) wird nur
    gerufen, wenn die Regeln KEINEN Namen finden — der Prompt ist im
    Paket versioniert (IMPRESSUM_PROMPT).
    """
    text = _text_aus_html(html or "")
    ergebnis = {
        "vorname": "", "nachname": "", "rolle": "", "email": "",
        "telefon": "", "hrb": "", "ist_einzelperson": False,
    }

    for muster, rolle in _ROLLEN_MUSTER:
        m = muster.search(text)
        if m:
            teile = m.group(1).split()
            ergebnis["vorname"] = " ".join(teile[:-1])
            ergebnis["nachname"] = teile[-1]
            ergebnis["rolle"] = rolle
            break

    m = _EMAIL.search(text)
    if m:
        ergebnis["email"] = m.group(0)
    m = _TELEFON.search(text)
    if m:
        ergebnis["telefon"] = m.group(1).strip()
    m = _HRB.search(text)
    if m:
        ergebnis["hrb"] = re.sub(r"\s+", " ", m.group(0)).upper()

    if not ergebnis["nachname"] and ki_abfrage is not None:
        try:
            ki = ki_abfrage(IMPRESSUM_PROMPT + text[:6000]) or {}
            for feld in ("vorname", "nachname", "rolle", "email", "telefon", "hrb"):
                if not ergebnis[feld] and ki.get(feld):
                    ergebnis[feld] = str(ki[feld]).strip()
            if isinstance(ki.get("ist_einzelperson"), bool):
                ergebnis["ist_einzelperson"] = ki["ist_einzelperson"]
        except Exception:
            pass  # KI ist Zusatz — Regel-Ergebnis bleibt gültig

    if ergebnis["nachname"] and not ergebnis["hrb"] and not _KAPITALGESELLSCHAFT.search(text):
        ergebnis["ist_einzelperson"] = True
    return ergebnis


def url_pruefen(url: str, firmen_name: str, hole=hole_seite) -> dict:
    """Erreichbarkeit + Plausibilität einer Firmen-URL (Netzwerk).

    titel_passt: mindestens ein Namens-Bestandteil (>= 4 Zeichen) der
    Firma taucht im <title> auf. ist_parkplatz: geparkte/verkäufliche Domain.
    """
    ziel = url if url.startswith("http") else f"https://{url}"
    status, html = hole(ziel)
    if status != 200 or not html:
        return {"erreichbar": False, "titel_passt": False, "ist_parkplatz": False}

    klein = html[:20000].lower()
    parkplatz = any(marker in klein for marker in _PARKPLATZ_MARKER)

    titel_passt = False
    m = _TITEL.search(html)
    if m:
        titel_norm = firmenname(m.group(1))
        for wort in re.split(r"[^a-zäöüß0-9]+", (firmen_name or "").lower()):
            if len(wort) >= 4 and firmenname(wort) and firmenname(wort) in titel_norm:
                titel_passt = True
                break
    return {"erreichbar": True, "titel_passt": titel_passt, "ist_parkplatz": parkplatz}
