# -*- coding: utf-8 -*-
"""Tests für leadkern.email und leadkern.drossel (alles offline)."""

import pytest

from leadkern.drossel import Quelle, QuelleGesperrt
from leadkern.email import validieren


# ── email.validieren ─────────────────────────────────────────────────

def test_email_syntax_kaputt():
    assert validieren("kein-at-zeichen.de")["status"] == "ungueltig"
    assert validieren("a@b")["status"] == "ungueltig"
    assert validieren("")["status"] == "ungueltig"


def test_email_gueltig_mit_mx():
    ergebnis = validieren("hans.marx@marx-fenster.de", mx_nachschlag=lambda d: True)
    assert ergebnis == {"status": "gueltig", "generisch": False}


def test_email_domain_ohne_mx():
    ergebnis = validieren("hans@gibtsnicht.example", mx_nachschlag=lambda d: False)
    assert ergebnis["status"] == "ungueltig"


def test_email_mx_nicht_pruefbar():
    ergebnis = validieren("hans@irgendwo.de", mx_nachschlag=lambda d: None)
    assert ergebnis["status"] == "gueltig"


def test_email_generisch_markiert():
    for adresse in ("info@firma.de", "kontakt@firma.de", "office@firma.de"):
        assert validieren(adresse, mx_nachschlag=lambda d: True)["generisch"] is True
    assert validieren("petra.klein@firma.de", mx_nachschlag=lambda d: True)["generisch"] is False


# ── drossel.Quelle ───────────────────────────────────────────────────

def test_drossel_haelt_rate_ein():
    schlaefchen = []
    zeit = [0.0]

    def uhr():
        return zeit[0]

    def schlaf(s):
        schlaefchen.append(round(s, 3))
        zeit[0] += s

    with Quelle("test", rate=1.0, schlaf=schlaf, uhr=uhr) as q:
        q.warte()          # erste Anfrage: kein Warten
        zeit[0] += 0.3     # 0,3 s „Arbeit"
        q.warte()          # muss ~0,7 s nachwarten
    assert schlaefchen == [0.7]
    assert q.anfragen == 2


def test_drossel_captcha_stoppt_sofort():
    q = Quelle("test")
    with pytest.raises(QuelleGesperrt):
        q.pruefe_antwort(200, "<html>Bitte lösen Sie das CAPTCHA</html>")


def test_drossel_403_serie_stoppt():
    q = Quelle("test")
    q.pruefe_antwort(403)
    q.pruefe_antwort(403)
    with pytest.raises(QuelleGesperrt):
        q.pruefe_antwort(403)


def test_drossel_serie_wird_von_erfolg_unterbrochen():
    q = Quelle("test")
    q.pruefe_antwort(429)
    q.pruefe_antwort(429)
    q.pruefe_antwort(200)  # Serie unterbrochen
    q.pruefe_antwort(429)
    q.pruefe_antwort(429)  # erst wieder bei 3 in Folge …
    with pytest.raises(QuelleGesperrt):
        q.pruefe_antwort(429)


def test_drossel_user_agent_mit_kontakt(monkeypatch):
    monkeypatch.setenv("USER_AGENT_KONTAKT", "kontakt@beispiel.de")
    assert Quelle("test").user_agent == "LeadMaschine2-Suchlauf/1.0 (kontakt@beispiel.de)"
    monkeypatch.delenv("USER_AGENT_KONTAKT")
    assert Quelle("test").user_agent == "LeadMaschine2-Suchlauf/1.0"
