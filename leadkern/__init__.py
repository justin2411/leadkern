# -*- coding: utf-8 -*-
"""leadkern — gemeinsame Prüf- und Normalisierungslogik der Lead-Fabriken.

Arbeitsauftrag v2 §3.1 (M0): jede Funktion rein und deterministisch,
ohne Netzwerkzugriff — außer in `web` und `email` (dort vermerkt).
Quellenspezifisches (OSM-Tags, Verzeichnis-Parser, Verbands-Rezepte)
gehört NICHT hierher, sondern in den jeweiligen Worker.
"""

__version__ = "0.1.0"

from . import normalisierung, dedupe, vorfilter, web, email, drossel  # noqa: F401
