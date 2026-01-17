# Bekannte Probleme & TODOs

## Unicode-Geschlechtszeichen in PDFs

### Problem
Pokémon mit Geschlechtssymbolen (♀/♂) wie Nidoran, Volbeat, Illumise etc. werden in den PDF-Dateien mit diesen schönen Unicode-Zeichen nicht korrekt dargestellt. Stattdessen erscheinen schwarze Kästen oder andere Darstellungsprobleme.

### Aktuelle Lösung (v1.0.1+)
Derzeit werden die Geschlechtszeichen durch ASCII-Alternativen ersetzt:
- `♀` → `(w)` (weiblich)
- `♂` → `(m)` (männlich)

**Beispiel:**
- Nidoran (w) statt Nidoran♀
- Nidoran (m) statt Nidoran♂

Dies ist zuverlässig und funktioniert auf allen Systemen, wirkt aber weniger elegant.

### TODO für Community
Wenn du eine bessere Lösung hast, sind wir offen für Beiträge! Mögliche Ansätze:
- Custom Symbol-Fonts in die PDF einbetten
- Unicode-Zeichen in Bildern rendern
- Alternative PDF-Generierungs-Bibliotheken testen (z.B. PDFKit)
- ReportLab-Configuration für bessere Unicode-Unterstützung

**Falls du eine Lösung hast:**
1. Forke das Repo
2. Implementiere den Fix in `scripts/generate_pdf.py`
3. Teste die PDFs
4. Erstelle einen Pull Request mit Erklärung

---

## Weitere bekannte Probleme

Keine weiteren bekannten Probleme. Wenn du eines findest, erstelle bitte ein Issue! 🐛
