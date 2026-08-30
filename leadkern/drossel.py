# -*- coding: utf-8 -*-
"""Drosselung und Stopp-Erkennung für Quellen-Zugriffe (Vorgabe M-2).

Kein Umgehen: ehrlicher User-Agent mit Kontaktangabe, 1 Anfrage/Sekunde
je Quelle, automatischer Stopp bei Captcha oder 429-/403-Serie. Sperren
werden protokolliert, nie überwunden.
"""

from __future__ import annotations

import os
import time

_CAPTCHA_MARKER = (
    "captcha", "are you a robot", "unusual traffic", "access denied",
    "bot detection", "cf-challenge", "challenge-platform",
)

# Ab so vielen 429/403 IN FOLGE gilt die Quelle als gesperrt.
SPERR_SERIE = 3


class QuelleGesperrt(RuntimeError):
    """Die Quelle zeigt Sperr-Signale — Lauf für diese Quelle beenden."""


class Quelle:
    """Kontextmanager für den Zugriff auf EINE Quelle.

        with Quelle("gelbe_seiten") as q:
            q.warte()                     # hält die Rate ein (Default 1/s)
            antwort = hole(url, headers={"User-Agent": q.user_agent})
            q.pruefe_antwort(antwort.status, antwort.text)

    `pruefe_antwort` wirft QuelleGesperrt bei Captcha-Markern oder einer
    429-/403-Serie. Der Aufrufer protokolliert und stoppt — kein Retry,
    kein Umgehen.
    """

    def __init__(self, name: str, rate: float = 1.0, schlaf=time.sleep, uhr=time.monotonic):
        if rate <= 0:
            raise ValueError("rate muss > 0 sein")
        self.name = name
        self.abstand = 1.0 / rate
        self._schlaf = schlaf
        self._uhr = uhr
        self._zuletzt: float | None = None
        self._sperr_zaehler = 0
        self.anfragen = 0

    def __enter__(self) -> "Quelle":
        return self

    def __exit__(self, *exc) -> None:
        return None

    @property
    def user_agent(self) -> str:
        kontakt = os.environ.get("USER_AGENT_KONTAKT", "").strip()
        basis = "LeadMaschine2-Suchlauf/1.0"
        return f"{basis} ({kontakt})" if kontakt else basis

    def warte(self) -> None:
        """Vor jeder Anfrage aufrufen — hält die konfigurierte Rate ein."""
        jetzt = self._uhr()
        if self._zuletzt is not None:
            rest = self.abstand - (jetzt - self._zuletzt)
            if rest > 0:
                self._schlaf(rest)
                jetzt = self._uhr()
        self._zuletzt = jetzt
        self.anfragen += 1

    def pruefe_antwort(self, status: int, text: str = "") -> None:
        """Nach jeder Antwort aufrufen — erkennt Sperr-Signale."""
        klein = (text or "")[:5000].lower()
        if any(marker in klein for marker in _CAPTCHA_MARKER):
            raise QuelleGesperrt(f"{self.name}: Captcha-/Bot-Schutz erkannt — Stopp.")
        if status in (429, 403):
            self._sperr_zaehler += 1
            if self._sperr_zaehler >= SPERR_SERIE:
                raise QuelleGesperrt(
                    f"{self.name}: {self._sperr_zaehler}× HTTP {status} in Folge — Stopp."
                )
        else:
            self._sperr_zaehler = 0
