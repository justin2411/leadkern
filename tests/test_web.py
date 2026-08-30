# -*- coding: utf-8 -*-
"""Tests für leadkern.web — 10 Impressum-Fixtures, alles offline."""

from pathlib import Path

import pytest

from leadkern.web import impressum_auslesen, impressum_finden, url_pruefen

FIXTURES = Path(__file__).parent / "fixtures"


def lade(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("datei,erwartet", [
    ("impressum_01_einzelunternehmer.html", {
        "vorname": "Hans", "nachname": "Marx", "rolle": "Inhaber",
        "email": "hans.marx@marx-fenster.de", "telefon": "0151 2345678",
        "hrb": "", "ist_einzelperson": True,
    }),
    ("impressum_02_gmbh.html", {
        "vorname": "Petra", "nachname": "Klein", "rolle": "Geschäftsführer",
        "email": "info@klein-kosmetik.de", "telefon": "089 998877",
        "hrb": "HRB 123456", "ist_einzelperson": False,
    }),
    ("impressum_03_vertreten_durch.html", {
        "vorname": "Anna Maria", "nachname": "Schmidt", "rolle": "Vertretungsberechtigt",
        "email": "anna@yogaloft.berlin", "telefon": "+49 30 5551234",
        "hrb": "", "ist_einzelperson": True,
    }),
    ("impressum_04_mstv.html", {
        "vorname": "Jonas", "nachname": "Weber", "rolle": "Verantwortlich",
        "email": "", "telefon": "0176 8887766", "hrb": "", "ist_einzelperson": True,
    }),
    ("impressum_05_umlaut_entities.html", {
        "vorname": "Ulrike", "nachname": "Grün", "rolle": "Inhaber",
        "email": "post@gruen-catering.de", "telefon": "0221 445566",
        "hrb": "", "ist_einzelperson": True,
    }),
    ("impressum_06_ohne_name.html", {
        "vorname": "", "nachname": "", "rolle": "",
        "email": "kontakt@studio-nord.de", "telefon": "040 123456",
        "hrb": "", "ist_einzelperson": False,
    }),
    ("impressum_07_kontakt.html", {
        "vorname": "Maria", "nachname": "Huber", "rolle": "Kontakt",
        "email": "maria@huber-fotografie.de", "telefon": "0157 9988776",
        "hrb": "", "ist_einzelperson": True,
    }),
    ("impressum_08_mit_noise.html", {
        "vorname": "Karl Otto", "nachname": "Lehmann", "rolle": "Betreiber",
        "email": "", "telefon": "0341 776655", "hrb": "", "ist_einzelperson": True,
    }),
])
def test_impressum_auslesen_regeln(datei, erwartet):
    assert impressum_auslesen(lade(datei)) == erwartet


def test_impressum_auslesen_ki_nachschlag():
    """Fixture 9: Regeln finden keinen Namen — der KI-Callable ergänzt ihn."""
    html = lade("impressum_09_freitext.html")
    ohne_ki = impressum_auslesen(html)
    assert ohne_ki["nachname"] == ""

    def ki_stub(prompt):
        assert "Milan Novak" in prompt
        return {"vorname": "Milan", "nachname": "Novak", "rolle": "Inhaber"}

    mit_ki = impressum_auslesen(html, ki_abfrage=ki_stub)
    assert mit_ki["vorname"] == "Milan"
    assert mit_ki["nachname"] == "Novak"
    assert mit_ki["email"] == "milan@novak-umzuege.de"  # kam schon aus den Regeln
    assert mit_ki["ist_einzelperson"] is True


def test_impressum_auslesen_ki_fehler_ist_harmlos():
    def kaputt(prompt):
        raise RuntimeError("API down")
    ergebnis = impressum_auslesen(lade("impressum_09_freitext.html"), ki_abfrage=kaputt)
    assert ergebnis["nachname"] == ""


def test_impressum_finden_ueber_link():
    def hole(url, timeout=15):
        if url == "https://marx-fenster.de":
            return 200, '<a href="/impressum.html">Impressum</a>'
        return 404, ""
    assert impressum_finden("marx-fenster.de", hole=hole) == "https://marx-fenster.de/impressum.html"


def test_impressum_finden_ueber_standardpfad():
    def hole(url, timeout=15):
        if url.endswith("/impressum"):
            return 200, "<h1>Impressum</h1>"
        return 200, "<p>Willkommen</p>"  # Startseite ohne Link
    assert impressum_finden("https://beispiel.de", hole=hole) == "https://beispiel.de/impressum"


def test_impressum_finden_nichts():
    def hole(url, timeout=15):
        return 404, ""
    assert impressum_finden("weg.example", hole=hole) is None


def test_url_pruefen_passend():
    def hole(url, timeout=15):
        return 200, "<html><head><title>Fenstermontage Marx – Startseite</title></head><body>ok</body></html>"
    ergebnis = url_pruefen("marx-fenster.de", "Marx Fenstermontage GmbH", hole=hole)
    assert ergebnis == {"erreichbar": True, "titel_passt": True, "ist_parkplatz": False}


def test_url_pruefen_parkplatz():
    """Fixture 10: geparkte Domain wird erkannt."""
    def hole(url, timeout=15):
        return 200, lade("impressum_10_parkplatz.html")
    ergebnis = url_pruefen("https://domain-zu-verkaufen.de", "Marx Fenstermontage", hole=hole)
    assert ergebnis["erreichbar"] is True
    assert ergebnis["ist_parkplatz"] is True
    assert ergebnis["titel_passt"] is False


def test_url_pruefen_nicht_erreichbar():
    def hole(url, timeout=15):
        return 0, ""
    assert url_pruefen("kaputt.example", "Egal", hole=hole) == {
        "erreichbar": False, "titel_passt": False, "ist_parkplatz": False,
    }
