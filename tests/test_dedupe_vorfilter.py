# -*- coding: utf-8 -*-
"""Tests für leadkern.dedupe und leadkern.vorfilter."""

from leadkern.dedupe import schluessel, zusammenfuehren
from leadkern.vorfilter import ist_institution, ist_kette_oder_filiale


def test_schluessel_beide():
    keys = schluessel({"name": "Marx Fenstermontage GmbH", "plz": "12345", "telefon": "0151 2345678"})
    assert keys == {"telefon_key": "491512345678", "name_plz_key": "marxfenstermontage|12345"}


def test_schluessel_fehlend():
    keys = schluessel({"name": "Marx Fenstermontage"})
    assert keys == {"telefon_key": None, "name_plz_key": None}


def test_zusammenfuehren_ueber_telefon():
    treffer = [
        {"name": "Marx Fenstermontage", "telefon": "0151 2345678", "quelle": "osm"},
        {"name": "Fenstermontage Marx GmbH", "telefon": "+49 151 2345678", "quelle": "verband:xyz", "website": "marx.de"},
    ]
    firmen = zusammenfuehren(treffer)
    assert len(firmen) == 1
    assert {q["quelle"] for q in firmen[0]["quellen"]} == {"osm", "verband:xyz"}
    assert firmen[0]["website"] == "marx.de"       # leeres Feld aufgefüllt
    assert firmen[0]["name"] == "Marx Fenstermontage"  # erster Treffer gewinnt


def test_zusammenfuehren_ueber_name_plz():
    treffer = [
        {"name": "Yoga Loft Berlin", "plz": "10115", "quelle": "osm"},
        {"name": "Yoga Loft Berlin GmbH", "plz": "10115", "quelle": "osm"},
        {"name": "Yoga Loft Berlin", "plz": "20095", "quelle": "osm"},
    ]
    firmen = zusammenfuehren(treffer)
    assert len(firmen) == 2  # andere PLZ = andere Firma


def test_zusammenfuehren_quelle_nur_einmal():
    treffer = [
        {"name": "Elektro Krause", "plz": "50667", "quelle": "osm"},
        {"name": "Elektro Krause AG", "plz": "50667", "quelle": "osm"},
    ]
    firmen = zusammenfuehren(treffer)
    assert len(firmen) == 1
    assert firmen[0]["quellen"] == [{"quelle": "osm"}]


def test_ist_institution():
    assert ist_institution({"name": "AWO Kita Regenbogen e.V."})
    assert ist_institution({"name": "Stadtwerke Musterstadt"})
    assert ist_institution({"name": "Pflegedienst Nord", "branche": "Caritas Sozialstation"})
    assert ist_institution({"name": "Branchenbuch24 GmbH"})
    assert not ist_institution({"name": "Marx Fenstermontage GmbH"})
    assert not ist_institution({"name": "Hebammenpraxis Schmidt"})


def test_ist_kette_ueber_namen():
    assert ist_kette_oder_filiale({"name": "SuperCut Filiale Berlin"}, [])
    assert not ist_kette_oder_filiale({"name": "Friseursalon Haarmonie"}, [])


def test_ist_kette_ueber_plz_streuung():
    lauf = [
        {"name": "SuperCut GmbH", "plz": "10115"},
        {"name": "SuperCut", "plz": "20095"},
        {"name": "SuperCut GmbH", "plz": "50667"},
        {"name": "Haarmonie", "plz": "10115"},
    ]
    assert ist_kette_oder_filiale({"name": "SuperCut"}, lauf)
    assert not ist_kette_oder_filiale({"name": "Haarmonie"}, lauf)
