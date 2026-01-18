# 🤝 Contributing to BinderPokedex

Thank you for your interest in contributing to this project! Here's a guide on how to do it correctly.

---

## 🚀 Getting Started

### 1. Fork the Repository
Click the "Fork" button in the top right corner to create a copy of this project in your GitHub account.

### 2. Clone Your Local Copy
```bash
git clone https://github.com/YOUR_USERNAME/BinderPokedex.git
cd BinderPokedex
```

### 3. Set Up Your Development Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# or: .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4. Create a Feature Branch
```bash
git checkout -b feature/description-of-your-changes
```

---

## 📝 Commit Guidelines

Write meaningful commit messages in English:

**Good Examples:**
```
- Add German type names for Gen 2
- Fix black background in Pokemon images  
- Improve PDF cutting line positioning
- Add support for custom paper sizes
```

**Bad Examples:**
```
- fix bug
- changes
- update stuff
```

---

## 🎯 Contribution Ideas

### 🌟 Major Features
- [ ] Additional Pokémon generations (Gen 10+)
- [ ] Alternative card layouts (2×2, 4×4 per page)
- [ ] Shiny variants
- [ ] Additional language support

### 🐛 Bug Fixes & Improvements
- [ ] Further PDF optimization
- [ ] Automated tests
- [ ] Performance improvements

### 📚 Documentation
- [ ] Translations to other languages
- [ ] Video tutorials
- [ ] Improved printing guides
- [ ] FAQ expansion

### 🎨 Design
- [ ] New color schemes
- [ ] Card back design (optional)
- [ ] Alternative templates

---

## 📋 Pull Request Process

### 1. Make Your Changes
Implement your change and test it thoroughly.

```bash
# Test PDF generation
python scripts/generate_pdf.py

# Check the result
open output/pokemon_gen1_en.pdf  # Mac
# or: xdg-open output/pokemon_gen1_en.pdf  # Linux
```

### 2. Commit Your Changes
```bash
git add .
git commit -m "Meaningful message here"
```

### 3. Push to GitHub
```bash
git push origin feature/description-of-your-changes
```

### 4. Open a Pull Request
- Go to your fork on GitHub
- Click "New Pull Request"
- Select `main` as the target branch
- Write a detailed description
- Submit!

### 5. Wait for Review
Comments and improvement suggestions are part of the process. Accept them constructively!

---

## 📋 PR Description Template

```markdown
## 📝 Description
Brief summary of what this PR does.

## 🔄 Type of Change
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 📚 Documentation
- [ ] 🎨 Design/Style
- [ ] ♻️ Refactoring

## 🧪 Testing
Explain how the change was tested:
- [ ] Tested locally
- [ ] PDF generation successful
- [ ] No known errors

## 📸 Screenshots (if applicable)
If visual changes: attach images here

## ✅ Checklist
- [ ] My code follows the project style
- [ ] I've added comments where needed
- [ ] I've updated documentation
- [ ] No new warnings when running
```

---

## 🎓 Coding Guidelines

### Python Style
Follow [PEP 8](https://pep8.org/):
```python
# Good
def generate_pokemon_cards(generation, output_path):
    """Generate Pokemon cards as PDF."""
    cards = []
    for pokemon in get_pokemon_data(generation):
        card = create_card(pokemon)
        cards.append(card)
    return cards

# Not so good
def gen_cards(gen,out):
    c=[]
    for p in get_pkmn(gen):
        c.append(create_card(p))
    return c
```

### Comments
```python
# Use English comments consistently
# Explain the "why", not the "what" (code shows that already)

# Good:
# Images are converted to RGBA because PNG transparency
# creates black areas in the PDF
img = Image.open(path).convert('RGBA')

# Not necessary:
# Open the image
img = Image.open(path)
```

### Function Documentation
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

### Test Before Pushing:
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Generate PDF
python scripts/generate_pdf.py

# 3. Check that no errors occur
# 4. Open PDF and verify visually

# 5. Optional: Test other generations
# (if you're working on fetch_pokemon_from_pokeapi.py)
```

### What Should Be Tested?
- ✅ PDF generates without errors
- ✅ All Pokemon are included
- ✅ Cutting lines are visible
- ✅ Images are displayed
- ✅ Languages are correct
- ✅ Page layout is correct (3×3 grid)

---

## 📞 Support & Questions

- **Questions?** Open a [Discussion](../../discussions)
- **Found a bug?** Create an [Issue](../../issues)
- **Not sure?** Ask in [Discussions](../../discussions) - better to ask than to implement incorrectly!

---

## 📜 Code of Conduct

We are a welcoming and respectful community. Please:
- ✅ Be friendly and constructive
- ✅ Listen to feedback
- ✅ Respect different opinions
- ✅ Help others

---

## 🏆 Recognition

All contributors are mentioned in our [Hall of Fame](../README.md)!

---

**Thank you for making this project better! 🎉**
