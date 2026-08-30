# -*- coding: utf-8 -*-
"""E-Mail-Prüfung: Syntax, MX-Nachschlag (dnspython), generische Postfächer.

⚠️ Netzwerkzugriff: der MX-Nachschlag fragt DNS ab. Für Tests ist der
Resolver injizierbar (`mx_nachschlag`).
"""

from __future__ import annotations

import re

_SYNTAX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

GENERISCHE_POSTFAECHER = {
    "info", "kontakt", "mail", "office", "post", "hallo", "hello",
    "service", "kanzlei", "praxis", "buero", "büro", "zentrale",
    "webmaster", "admin", "kontaktformular", "anfrage", "bewerbung",
    "noreply", "no-reply",
}


def _mx_dns(domain: str) -> bool | None:
    """True = MX vorhanden, False = sicher keiner, None = nicht prüfbar."""
    try:
        import dns.resolver  # dnspython
    except ImportError:
        return None
    try:
        antworten = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(list(antworten)) > 0
    except Exception as ex:
        name = type(ex).__name__
        if name in ("NXDOMAIN", "NoAnswer"):
            return False
        return None  # Timeout / kein Netz -> nicht bewerten


def validieren(adresse: str, mx_nachschlag=_mx_dns) -> dict:
    """{status: gueltig|catch_all|ungueltig, generisch: bool}

    - Syntax kaputt oder Domain ohne MX -> ungueltig
    - MX vorhanden -> gueltig (catch_all bleibt einer späteren
      SMTP-Prüfung vorbehalten — wir raten nicht)
    - MX nicht prüfbar (kein Netz/Timeout) -> gueltig nach Syntax,
      generisch wird trotzdem markiert
    """
    adresse = (adresse or "").strip()
    if not _SYNTAX.match(adresse):
        return {"status": "ungueltig", "generisch": False}

    lokal, _, domain = adresse.partition("@")
    generisch = lokal.lower() in GENERISCHE_POSTFAECHER

    mx = mx_nachschlag(domain)
    if mx is False:
        return {"status": "ungueltig", "generisch": generisch}
    return {"status": "gueltig", "generisch": generisch}
