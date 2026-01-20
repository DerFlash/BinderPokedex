# Architektur-Refactoring Plan: Vereinheitlichung der PDF-Rendering-Module

## Problem-Analyse: Typ-Übersetzungen in Karten

### Symptom
Nach Implementation von Pokémon-Typ-Übersetzungen (Water → Wasser, Fire → Feuer, etc.) zeigte sich ein kritisches Problem:
- **Ex-Variant PDFs**: Typen wurden korrekt übersetzt (Deutsch, Französisch, etc.)
- **Basis-Pokédex PDFs**: Typen blieben auf Englisch

### Root Cause
Die Codebase hat **mehrere parallele Implementierungen** für Karten-Rendering:

```
Rendering-Architektur (Status Quo - PROBLEMATISCH)
┌─────────────────────────────────────────────────────────┐
│                                                           │
├─ pdf_generator.py                                        │
│  └─ PDFGenerator._draw_card()  ← Generation PDFs         │
│     └─ Type rendering: types[0] (NO translation)        │
│                                                           │
├─ card_template.py                                        │
│  └─ CardTemplate.draw_card()  ← Variant PDFs            │
│     └─ Type rendering: TYPE_TRANSLATIONS (translated)   │
│                                                           │
└─ variant_pdf_generator.py                                │
   └─ Nutzt CardTemplate ← Ex-Variant PDFs                │
      └─ Type rendering: translated ✓                     │
```

### Der Fehler
1. **card_template.py** wurde aktualisiert mit Type-Übersetzungen
2. **pdf_generator.py** hatte eigene `_draw_card()` Methode - NICHT aktualisiert
3. Basis-PDFs (Gen1-9) nutzen pdf_generator.py → keine Übersetzungen
4. Variant-PDFs nutzen card_template.py → haben Übersetzungen

### Lösungsversuch #1 (FALSCH)
Annahme: Übersetzungen in card_template.py hinzufügen genügt
```python
# card_template.py - nur hier aktualisiert
TYPE_TRANSLATIONS = _load_type_translations()  # Neu hinzugefügt
```
**Problem**: pdf_generator.py wurde nicht aktualisiert

### Lösungsversuch #2 (UNVOLLSTÄNDIG)
Regex-Regenerierung aller PDFs mit `--skip-images`
```bash
for gen in {1..9}; do
    python generate_pdf.py --generation $gen --language de --skip-images
done
```
**Problem**: Entfernte alle Pokémon-Bilder statt nur Caches zu nutzen

### Finale Lösung (RICHTIG)
1. Typ-Übersetzungen in **pdf_generator.py** hinzufügen
2. `_load_type_translations()` Methode in pdf_generator.py implementieren
3. `_draw_card()` Methode anpassen
4. Absolute Pfade mit `.resolve()` für robustes Laden
5. Alle 9 Generationen + alle Varianten neu generieren

```python
# pdf_generator.py - nachträglich aktualisiert
def _load_type_translations(self):
    """Load type translations from i18n/translations.json"""
    try:
        pdf_generator_file = Path(__file__).resolve()  # Absolut!
        translations_path = pdf_generator_file.parent.parent.parent / 'i18n' / 'translations.json'
        ...
    return {}

def _draw_card(self, canvas_obj, pokemon_data):
    ...
    # Translate type to current language
    type_translations = self._load_type_translations()
    language_types = type_translations.get(self.language, {})
    type_text = language_types.get(type_english, type_english)
```

---

## Architektur-Problem: Code-Duplikation

### Redundante Card-Rendering-Implementierungen

```
Aktuelle Situation (DUPLIKATION):
┌────────────────────────────────────────────────────────────┐
│                   PDF Generation                            │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  PDFGenerator (pdf_generator.py)                            │
│  ├─ _draw_card()                                            │
│  ├─ Card styling (border, header, background)              │
│  ├─ Type display & translation                             │
│  ├─ Name rendering                                         │
│  ├─ Image handling                                         │
│  ├─ Number/ID rendering                                    │
│  └─ Stats rendering                                        │
│                                                              │
│  CardTemplate (card_template.py)                           │
│  ├─ draw_card()                                            │
│  ├─ Card styling (border, header, background) [DUP]       │
│  ├─ Type display & translation [DUP]                      │
│  ├─ Name rendering [DUP]                                  │
│  ├─ Image handling [DUP]                                  │
│  ├─ Number/ID rendering [DUP]                             │
│  └─ Stats rendering [DUP]                                 │
│                                                              │
│  Problem: Änderungen an einer Stelle nicht an der anderen! │
└────────────────────────────────────────────────────────────┘
```

### Ähnliche Probleme bei Cover-Rendering

```
Cover Rendering (auch dupliziert):
├─ pdf_generator.py
│  └─ _draw_cover()
│     ├─ Title rendering
│     ├─ Featured Pokemon images
│     ├─ Generation info
│     └─ Footer
│
├─ cover_template.py
│  └─ draw_cover()
│     ├─ Title rendering [DUP]
│     ├─ Featured Pokemon images
│     ├─ Generation info [DUP]
│     └─ Footer [DUP]
│
└─ variant_pdf_generator.py
   └─ Nutzt cover_template.py
```

---

## Zielarchitektur: Modularisierung

### Design-Prinzipien
1. **Single Responsibility**: Jede Komponente hat genau eine Aufgabe
2. **DRY (Don't Repeat Yourself)**: Keine Code-Duplikation
3. **Composition over Inheritance**: Komponenten zusammenstellen
4. **Dependency Injection**: Services übergeben statt hart codiert

### Proposed Module-Struktur

```
scripts/lib/
├─ rendering/                          [NEW] Zentrale Rendering-Module
│  ├─ __init__.py
│  ├─ card_renderer.py                 [NEW] Unified Card Rendering
│  │  ├─ class CardRenderer
│  │  │  ├─ render_card()              [unified, replaces both]
│  │  │  ├─ _draw_header()
│  │  │  ├─ _draw_type()               [mit Übersetzungen]
│  │  │  ├─ _draw_name()
│  │  │  ├─ _draw_image()
│  │  │  ├─ _draw_stats()
│  │  │  └─ _load_translations()       [shared method]
│  │  └─ class CardStyle              [unified styling]
│  │     ├─ COLORS
│  │     ├─ DIMENSIONS
│  │     └─ FONTS
│  │
│  ├─ cover_renderer.py                [NEW] Unified Cover Rendering
│  │  ├─ class CoverRenderer
│  │  │  ├─ render_cover()
│  │  │  ├─ _draw_title()
│  │  │  ├─ _draw_featured_pokemon()
│  │  │  ├─ _draw_info()
│  │  │  └─ _load_translations()
│  │  └─ class CoverStyle             [unified styling]
│  │
│  ├─ page_renderer.py                 [NEW] Page Layout
│  │  └─ class PageRenderer
│  │     ├─ create_page()
│  │     ├─ add_cards()
│  │     ├─ add_cover()
│  │     └─ _calculate_layout()
│  │
│  └─ translation_loader.py            [NEW] Centralized i18n
│     └─ class TranslationLoader
│        ├─ load_types(language)
│        ├─ load_ui(language)
│        └─ _get_translations_path()   [with .resolve()]
│
├─ pdf_generator.py                    [REFACTORED]
│  ├─ class PDFGenerator
│  │  ├─ generate()
│  │  ├─ _prepare_data()
│  │  └─ ← uses CardRenderer, CoverRenderer, PageRenderer
│  └─ [removes _draw_card, _draw_cover - now in CardRenderer]
│
├─ variant_pdf_generator.py            [REFACTORED]
│  ├─ class VariantPDFGenerator
│  │  ├─ generate()
│  │  ├─ _prepare_data()
│  │  └─ ← uses CardRenderer, CoverRenderer, PageRenderer
│  └─ [removes duplication - uses shared modules]
│
├─ card_template.py                    [DEPRECATED]
│  └─ [Keep for backward compatibility during transition]
│
└─ cover_template.py                   [DEPRECATED]
   └─ [Keep for backward compatibility during transition]
```

### Refactored Flow

```
Gewünschte Situation (MODULAR):

PDFGenerator.generate()
  ├─ TranslationLoader.load_types('de')  ← shared
  ├─ TranslationLoader.load_ui('de')     ← shared
  ├─ CoverRenderer.render_cover()        ← shared
  │  └─ Type/translation handling unified
  ├─ PageRenderer.create_page()          ← shared
  ├─ CardRenderer.render_card() × 9      ← shared
  │  └─ Type rendering uses TranslationLoader ✓
  └─ Save PDF

VariantPDFGenerator.generate()
  ├─ TranslationLoader.load_types('de')  ← shared (!)
  ├─ TranslationLoader.load_ui('de')     ← shared (!)
  ├─ CoverRenderer.render_cover()        ← shared (!)
  │  └─ Type/translation handling unified
  ├─ PageRenderer.create_page()          ← shared (!)
  ├─ CardRenderer.render_card() × 150    ← shared (!)
  │  └─ Type rendering uses TranslationLoader ✓
  └─ Save PDF
```

### Vorteile dieser Architektur

| Problem | Vorher | Nachher |
|---------|--------|---------|
| **Typ-Übersetzungen vergessen** | Muss an 2+ Stellen updaten | Nur 1 Stelle (CardRenderer) |
| **Änderungen an Styling** | Dupliziert in 2 Dateien | 1 Stelle (CardStyle) |
| **Translation Loading** | Verschiedene Implementierungen | 1 zentrales TranslationLoader Modul |
| **Pfad-Fehler** | In mehreren Dateien wiederholt | Nur 1 Stelle mit `.resolve()` |
| **Feature Parity** | Gen PDFs vs. Variant PDFs unterschiedlich | Automatisch identisch |
| **Testing** | Testen beider Implementierungen nötig | 1 Test pro Komponente |

---

## Implementierungs-Strategie (Später)

### Phase 1: Schaffung von Foundations (Grundlagen)
```python
# scripts/lib/rendering/translation_loader.py [NEW]
class TranslationLoader:
    @staticmethod
    def get_translations_path():
        """Unified path resolution with .resolve()"""
        ...
    
    @classmethod
    def load_types(cls, language: str) -> dict:
        """Load and cache type translations"""
        ...
    
    @classmethod
    def load_ui(cls, language: str) -> dict:
        """Load UI translations"""
        ...
```

### Phase 2: Unified Renderers
```python
# scripts/lib/rendering/card_renderer.py [NEW]
class CardRenderer:
    def __init__(self, language: str, style: CardStyle = None):
        self.language = language
        self.style = style or CardStyle()
        self.translations = TranslationLoader.load_types(language)
    
    def render_card(self, canvas, pokemon_data, x, y):
        """Single implementation replaces both old versions"""
        self._draw_header(canvas, pokemon_data, x, y)
        self._draw_type(canvas, pokemon_data, x, y)  # ← uses translations
        self._draw_name(canvas, pokemon_data, x, y)
        ...
```

### Phase 3: Refactoring Existing Generators
1. PDFGenerator anpassen → nutzt CardRenderer
2. VariantPDFGenerator anpassen → nutzt CardRenderer
3. Tests aktualisieren

### Phase 4: Cleanup
1. card_template.py deprecation notices hinzufügen
2. Dokumentation aktualisieren
3. Alte Module optional behalten oder entfernen

---

## Erkannte Anti-Patterns

### 1. **Siloisation von Rendering-Code**
- **Problem**: Card-Rendering ist in 2 Dateien
- **Ursache**: Wurde parallel für verschiedene Use-Cases entwickelt
- **Lösung**: Zentrale Rendering-Module

### 2. **Scattered Translation Loading**
- **Problem**: i18n wird an mehreren Stellen geladen
- **Ursache**: Keine zentrale TranslationService
- **Lösung**: TranslationLoader Modul mit Caching

### 3. **Hardcoded Paths ohne `.resolve()`**
- **Problem**: `Path(__file__).parent.parent.parent` funktioniert nur mit relativen Paths
- **Ursache**: Path Calculation wurde nicht robust implementiert
- **Lösung**: `.resolve()` für absolute Paths verwenden

### 4. **No Shared Constants**
- **Problem**: CardStyle, Colors, Fonts dupliziert
- **Ursache**: Keine Shared Constants Modul
- **Lösung**: CardStyle, CoverStyle Klassen mit allen Konstanten

---

## Fazit & Empfehlungen

### Sofortmassnahmen (DONE)
✅ Typ-Übersetzungen in pdf_generator.py hinzugefügt
✅ Absolute Paths mit `.resolve()` implemented
✅ Alle PDFs neu generiert

### Mittelfristig (TODO - Refactoring)
- [ ] TranslationLoader Modul erstellen
- [ ] CardRenderer Modul erstellen  
- [ ] CoverRenderer Modul erstellen
- [ ] PageRenderer Modul erstellen
- [ ] PDFGenerator refaktorieren (nutzt neue Module)
- [ ] VariantPDFGenerator refaktorieren (nutzt neue Module)
- [ ] Tests aktualisieren

### Langfristig (Architektur)
- [ ] Alte card_template.py deprecieren
- [ ] Alte cover_template.py deprecieren
- [ ] Dokumentation: Rendering Architecture
- [ ] Plugin System für Custom Rendering?

### Gewonnene Lessons Learned
1. **Centralize, don't duplicate** - Shared code führt zu konsistenten Features
2. **Path resolution robustness** - `.resolve()` ist wichtig für Flexibilität
3. **Single source of truth** - i18n, Styling, Rendering sollte zentral sein
4. **Test coverage matters** - Hätte duplizierte Methode früh erkannt

---

## Anhang: Code-Beispiele für Zielarchitektur

### Beispiel: TranslationLoader
```python
# scripts/lib/rendering/translation_loader.py
class TranslationLoader:
    _cache = {}
    
    @staticmethod
    def _get_translations_path():
        """Get absolute path to translations.json"""
        loader_file = Path(__file__).resolve()  # Absolut!
        return loader_file.parent.parent.parent / 'i18n' / 'translations.json'
    
    @classmethod
    def load_types(cls, language: str) -> dict:
        """Load type translations with caching"""
        cache_key = f"types_{language}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        translations_path = cls._get_translations_path()
        if translations_path.exists():
            with open(translations_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result = data.get('types', {}).get(language, {})
                cls._cache[cache_key] = result
                return result
        return {}
```

### Beispiel: CardRenderer (unified)
```python
# scripts/lib/rendering/card_renderer.py
class CardRenderer:
    def __init__(self, language: str, image_cache=None):
        self.language = language
        self.image_cache = image_cache
        self.type_translations = TranslationLoader.load_types(language)
    
    def render_card(self, canvas_obj, pokemon_data, x, y):
        """Single implementation for both Gen and Variant PDFs"""
        # Header
        pokemon_type = pokemon_data.get('types', ['Normal'])[0]
        header_color = CardStyle.TYPE_COLORS[pokemon_type]
        canvas_obj.setFillColor(HexColor(header_color), alpha=0.1)
        canvas_obj.rect(x, y + CARD_HEIGHT - 12*mm, CARD_WIDTH, 12*mm, ...)
        
        # Type with translation
        type_translated = self.type_translations.get(pokemon_type, pokemon_type)
        canvas_obj.drawString(..., type_translated)
        
        # Rest of card...
```

### Beispiel: PDFGenerator (refactored)
```python
# scripts/lib/pdf_generator.py [REFACTORED]
from rendering.card_renderer import CardRenderer
from rendering.cover_renderer import CoverRenderer

class PDFGenerator:
    def __init__(self, language, generation):
        self.language = language
        self.generation = generation
        self.card_renderer = CardRenderer(language)
        self.cover_renderer = CoverRenderer(language)
    
    def generate(self):
        c = canvas.Canvas(...)
        
        # Cover
        self.cover_renderer.render_cover(c, self.pokemon_list)
        c.showPage()
        
        # Cards
        for pokemon in self.pokemon_list:
            x, y = self._calculate_position()
            self.card_renderer.render_card(c, pokemon, x, y)
        
        c.save()
```
