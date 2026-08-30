# leadkern

Gemeinsames Python-Paket der Lead-Fabriken (Lead-Maschine 2.0, **M0** —
Arbeitsauftrag v2 §3.1). Enthält die gesamte **quellenunabhängige**
Prüf- und Normalisierungslogik — komplett neu geschrieben, jede Funktion
rein und deterministisch. Netzwerkzugriff nur in `web` (Impressum/URL)
und `email` (MX-Nachschlag), dort vermerkt und für Tests injizierbar.

Quellenspezifisches (OSM-Tags, Verzeichnis-Parser, Verbands-Rezepte)
gehört NICHT hierher, sondern in den jeweiligen Worker.

## Installation (aus GitHub)

```
pip install "leadkern @ git+https://github.com/justin2411/leadkern@main"
```

Semantische Versionierung über `version` in pyproject.toml (0.1.0, 0.2.0, …) — Schlüssel-Semantik
(telefon_key, Firmennamen-Vergleichsform) ist mit der Fabrik-2-App
abgestimmt; Änderungen daran sind ein Major-/Minor-Schritt, nie ein Patch.

## Module

| Modul | Funktionen |
| --- | --- |
| `normalisierung` | `firmenname`, `inhaber_kandidat`, `telefon` (e164/key/**art: mobil\|festnetz\|ungueltig** — Handy-Fokus!), `adresse` |
| `dedupe` | `schluessel` (telefon_key + name_plz_key), `zusammenfuehren` (Quellen-Badges mergen) |
| `vorfilter` | `ist_institution`, `ist_kette_oder_filiale` |
| `web` | `impressum_finden`, `impressum_auslesen` (Regelwerk + optionaler KI-Callable, Prompt versioniert), `url_pruefen` |
| `email` | `validieren` (Syntax + MX via dnspython, generische Postfächer markiert) |
| `drossel` | `Quelle` (1 Anfrage/s, ehrlicher User-Agent aus `USER_AGENT_KONTAKT`, Stopp bei Captcha/429-403-Serie — kein Umgehen, M-2) |

## Tests

```
pip install -e ".[test]"
python3 -m pytest tests/
```

30 Firmennamen, 30 Telefonnummern, 10 Impressum-HTML-Fixtures — alles
offline (Netz-Funktionen mit injizierten Stubs).
