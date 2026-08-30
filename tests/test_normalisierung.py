# -*- coding: utf-8 -*-
"""Tests für leadkern.normalisierung — 30 Firmennamen, 30 Telefonnummern."""

import pytest

from leadkern.normalisierung import adresse, firmenname, inhaber_kandidat, telefon

FIRMENNAMEN = [
    ("Marx Fenstermontage GmbH & Co. KG", "marxfenstermontage"),
    ("Müller & Söhne GbR", "muellersoehne"),
    ("Kosmetikstudio Schön UG (haftungsbeschränkt)", "kosmetikstudioschoen"),
    ("Bäckerei Öztürk e.K.", "baeckereioeztuerk"),
    ("Physiotherapie Weiß", "physiotherapieweiss"),
    ("Hebammenpraxis Anna Schmidt", "hebammenpraxisannaschmidt"),
    ("Yoga Loft Berlin GmbH", "yogaloftberlin"),
    ("Pflegedienst Sonnenschein gGmbH", "pflegedienstsonnenschein"),
    ("Friseursalon Haarmonie Inh. Petra Klein", "friseursalonhaarmoniepetraklein"),
    ("AWO Kita Regenbogen e.V.", "awokitaregenbogen"),
    ("Elektro Krause AG", "elektrokrause"),
    ("Nachhilfe-Institut Lernfix", "nachhilfeinstitutlernfix"),
    ("Dr. med. Hanna Vogel", "drmedhannavogel"),
    ("Tagesmutter Sabine's Wichtel", "tagesmuttersabineswichtel"),
    ("Kosmetik & Fußpflege Meyer", "kosmetikfusspflegemeyer"),
    ("MALERBETRIEB HUBER", "malerbetriebhuber"),
    ("Gebäudereinigung Blitz-Blank OHG", "gebaeudereinigungblitzblank"),
    ("Foto Studio 54", "fotostudio54"),
    ("Heilpraktikerin Ute Lang", "heilpraktikerinutelang"),
    ("Doula Herzensweg", "doulaherzensweg"),
    ("Ernährungsberatung Vital GmbH", "ernaehrungsberatungvital"),
    ("Musikschule Notenzauber KG", "musikschulenotenzauber"),
    ("Fahrschule Start Frei e.Kfm.", "fahrschulestartfrei"),
    ("Zimmerei Holzwurm GmbH & Co KG", "zimmereiholzwurm"),
    ("Steuerberatung Zahlenwerk PartG mbB", "steuerberatungzahlenwerk"),
    ("Hausmeisterservice Flink UG", "hausmeisterserviceflink"),
    ("Kita Sternschnuppe gGmbH", "kitasternschnuppe"),
    ("Mobiler Mittagstisch Oma Erna", "mobilermittagstischomaerna"),
    ("Pilates-Studio Balance", "pilatesstudiobalance"),
    ("Schlüsseldienst 24h Nord", "schluesseldienst24hnord"),
]


@pytest.mark.parametrize("roh,erwartet", FIRMENNAMEN)
def test_firmenname(roh, erwartet):
    assert firmenname(roh) == erwartet


TELEFONNUMMERN = [
    ("0151 23456789", "4915123456789", "mobil"),
    ("+49 170 1234567", "491701234567", "mobil"),
    ("0049 160 9876543", "491609876543", "mobil"),
    ("030 1234567", "49301234567", "festnetz"),
    ("089/123456", "4989123456", "festnetz"),
    ("(0221) 98 76 54", "49221987654", "festnetz"),
    ("0176-88877766", "4917688877766", "mobil"),
    ("015789456123", "4915789456123", "mobil"),
    ("+49(0)151 2345678", "491512345678", "mobil"),
    ("0", None, "ungueltig"),
    ("12345", None, "ungueltig"),
    ("0000000000", None, "ungueltig"),
    ("0341 96 85 74 12", "4934196857412", "festnetz"),
    ("+43 660 1234567", None, "ungueltig"),
    ("0800 5551234", "498005551234", "festnetz"),
    ("01777777777", "491777777777", "mobil"),
    ("Tel: 0159 11223344", "4915911223344", "mobil"),
    ("0151-99999999999999", None, "ungueltig"),
    ("", None, "ungueltig"),
    ("Hausnummer 12", None, "ungueltig"),
    ("0163 4455667", "491634455667", "mobil"),
    ("00491522334455", "491522334455", "mobil"),
    ("040-334455", "4940334455", "festnetz"),
    ("+49 30 901820", "4930901820", "festnetz"),
    ("0157 000000", "49157000000", "mobil"),
    ("07071 123456", "497071123456", "festnetz"),
    ("017612345678", "4917612345678", "mobil"),
    ("555-1234", None, "ungueltig"),
    ("+491511111111", "491511111111", "mobil"),
    ("0 30 / 55 44 33 22", "493055443322", "festnetz"),
]


@pytest.mark.parametrize("roh,key,art", TELEFONNUMMERN)
def test_telefon(roh, key, art):
    ergebnis = telefon(roh)
    assert ergebnis["key"] == key
    assert ergebnis["art"] == art
    if key:
        assert ergebnis["e164"] == f"+{key}"
    else:
        assert ergebnis["e164"] is None


def test_adresse_mit_komma():
    assert adresse("Musterstraße 12, 12345 Berlin") == {
        "strasse": "Musterstraße 12", "plz": "12345", "ort": "Berlin",
    }


def test_adresse_ohne_komma():
    assert adresse("Hauptstr. 5a 80331 München") == {
        "strasse": "Hauptstr. 5a", "plz": "80331", "ort": "München",
    }


def test_adresse_nur_plz_ort():
    assert adresse("12345 Kleinstadt") == {"strasse": "", "plz": "12345", "ort": "Kleinstadt"}


def test_adresse_ohne_plz():
    assert adresse("Ohne Postleitzahl 7") == {"strasse": "Ohne Postleitzahl 7", "plz": "", "ort": ""}


def test_adresse_mit_land():
    assert adresse("Am Markt 3, 04109 Leipzig, Deutschland") == {
        "strasse": "Am Markt 3", "plz": "04109", "ort": "Leipzig",
    }


@pytest.mark.parametrize("roh,erwartet", [
    ("Marx Fenstermontage", "Marx"),
    ("Peter Marx Fenstermontage", "Marx"),
    ("Fenstermontage Marx", "Marx"),
    ("Marx & Söhne Fenstermontage", "Marx"),
    ("Autohaus Müller GmbH", "Müller"),
    ("Nagelstudio", None),           # kein Namens-Wort
    ("Schmidt", None),               # kein Gewerk-Wort -> kein Urteil
    ("Sonnenschein Kinderland Abenteuer Welt", None),  # zu viele Kandidaten
])
def test_inhaber_kandidat(roh, erwartet):
    assert inhaber_kandidat(roh) == erwartet
