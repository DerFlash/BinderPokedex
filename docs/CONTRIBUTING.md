# 🤝 Beitragen zu BinderPokedex

Danke, dass du zu diesem Projekt beitragen möchtest! Hier ist eine Anleitung, wie du es richtig machst.

---

## 🚀 Erste Schritte

### 1. Repository Forken
Klicke oben rechts auf "Fork", um eine Kopie dieses Projekts in deinem GitHub-Konto zu erstellen.

### 2. Lokale Kopie klonen
```bash
git clone https://github.com/DEIN_BENUTZERNAME/BinderPokedex.git
cd BinderPokedex
```

### 3. Development-Umgebung einrichten
```bash
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# oder: .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4. Feature-Branch erstellen
```bash
git checkout -b feature/beschreibung-deiner-änderung
```

---

## 📝 Commit-Richtlinien

Schreibe aussagekräftige Commit-Messages auf Deutsch oder Englisch:

**Gute Beispiele:**
```
- Add German type names for Gen 2
- Fix black background in Pokemon images  
- Improve PDF cutting line positioning
- Add support for custom paper sizes
```

**Schlechte Beispiele:**
```
- fix bug
- changes
- update stuff
```

---

## 🎯 Beitrag-Ideen

### 🌟 Große Features
- [ ] Weitere Pokémon-Generationen (Gen 9+)
- [ ] Alternative Kartenlayouts (2×2, 4×4 pro Seite)
- [ ] Shiny-Varianten
- [ ] Mehrsprachige Unterstützung (EN, FR, ES, etc.)

### 🐛 Bug-Fixes & Verbesserungen
- [ ] Unicode-Geschlechtszeichen in PDFs (siehe KNOWN_ISSUES.md)
- [ ] Weitere PDF-Verarbeitungsoptimierungen
- [ ] Automatische Tests

### 📚 Dokumentation
- [ ] Übersetzungen in andere Sprachen
- [ ] Video-Tutorials
- [ ] Verbesserte Druckanleitungen
- [ ] FAQ erweitern

### 🎨 Design
- [ ] Neue Farbschemata für Generationen
- [ ] Kartenseiten-Rückseite (optional)
- [ ] Alternative Design-Vorlagen

---

## 📋 Pull Request Prozess

### 1. Code ändern
Implementiere deine Änderung und teste sie gründlich.

```bash
# Teste die PDF-Generierung
python scripts/generate_pdf.py

# Überprüfe das Ergebnis
open data/BinderPokedex_Gen1.pdf  # Mac
# oder: xdg-open data/BinderPokedex_Gen1.pdf  # Linux
```

### 2. Änderungen committen
```bash
git add .
git commit -m "Aussagekräftige Nachricht hier"
```

### 3. Zu GitHub pushen
```bash
git push origin feature/beschreibung-deiner-änderung
```

### 4. Pull Request öffnen
- Gehe zu deinem Fork auf GitHub
- Klicke auf "New Pull Request"
- Wähle den `main` Branch als Ziel
- Schreibe eine detaillierte Beschreibung
- Submitten!

### 5. Review abwarten
Kommentare und Verbesserungsvorschläge sind Teil des Prozesses. Nimm sie konstruktiv an!

---

## 📋 PR-Beschreibungs-Template

```markdown
## 📝 Beschreibung
Kurze Zusammenfassung, was diese PR bewirkt.

## 🔄 Typ der Änderung
- [ ] 🐛 Bug-Fix
- [ ] ✨ Neue Funktion
- [ ] 📚 Dokumentation
- [ ] 🎨 Design/Style
- [ ] ♻️ Refactoring

## 🧪 Testing
Erkläre, wie die Änderung getestet wurde:
- [ ] Lokal getestet
- [ ] PDF-Generierung erfolgreich
- [ ] Kein bekannter Fehler vorhanden

## 📸 Screenshots (falls relevant)
Falls visuelle Änderungen: hier Bilder einfügen

## ✅ Checklist
- [ ] Mein Code folgt dem Style dieses Projekts
- [ ] Ich habe Kommentare hinzugefügt wo nötig
- [ ] Ich habe die Dokumentation aktualisiert
- [ ] Keine neuen Warnings beim Ausführen
```

---

## 🎓 Coding-Richtlinien

### Python-Style
Folge [PEP 8](https://pep8.org/):
```python
# Gut
def generate_pokemon_cards(generation, output_path):
    """Generate Pokemon cards as PDF."""
    cards = []
    for pokemon in get_pokemon_data(generation):
        card = create_card(pokemon)
        cards.append(card)
    return cards

# Nicht so gut
def gen_cards(gen,out):
    c=[]
    for p in get_pkmn(gen):
        c.append(create_card(p))
    return c
```

### Kommentare
```python
# Verwende Deutsche oder Englische Kommentare konsistent
# Erkläre das "Warum", nicht das "Was" (Code zeigt das bereits)

# Gut:
# Die Bilder werden in RGBA konvertiert, da PNG-Transparenz
# schwarze Bereiche im PDF erzeugt
img = Image.open(path).convert('RGBA')

# Nicht nötig:
# Öffne das Bild
img = Image.open(path)
```

### Funktions-Dokumentation
```python
def draw_pokemon_card(canvas, pokemon, x, y):
    """
    Draw a single Pokemon card on the canvas.
    
    Args:
        canvas: reportlab Canvas object
        pokemon (dict): Pokemon data with name, type, image
        x (float): X-coordinate in mm
        y (float): Y-coordinate in mm
    
    Returns:
        None
    """
```

---

## 🧪 Testing

### Vor dem Push testen:
```bash
# 1. Virtual Environment aktivieren
source .venv/bin/activate

# 2. PDF generieren
python scripts/generate_pdf.py

# 3. Überprüfen, dass keine Fehler auftreten
# 4. PDF öffnen und visuell prüfen

# 5. Optional: Andere Generationen testen
# (wenn du an extract_pokemon_data.py arbeitest)
```

### Was sollte getestet werden?
- ✅ PDF generiert ohne Fehler
- ✅ Alle Pokemon sind enthalten
- ✅ Schnittlinien sind sichtbar
- ✅ Bilder werden angezeigt
- ✅ Deutsch und Englisch korrekt
- ✅ Seitenlayout stimmt (3×3 Grid)

---

## 📞 Support & Fragen

- **Fragen?** Öffne eine [Discussion](../../discussions)
- **Bug gefunden?** Erstelle ein [Issue](../../issues)
- **Nicht sicher?** Frag in den [Discussions](../../discussions) - lieber fragen als falsch implementieren!

---

## 📜 Code of Conduct

Wir sind eine einladende und respektvolle Community. Bitte:
- ✅ Sei freundlich und konstruktiv
- ✅ Höre auf Feedback
- ✅ Respektiere unterschiedliche Meinungen
- ✅ Helfe anderen

---

## 🏆 Anerkennung

Alle Contributors werden in unserem [Hall of Fame](README.md#-danksagungen) erwähnt!

---

**Danke, dass du dieses Projekt besser machst! 🎉**
