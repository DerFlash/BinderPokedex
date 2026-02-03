#!/usr/bin/env python3
"""Check dexId in TCG source data"""

import json
from pathlib import Path

# Load source data
data_file = Path(__file__).parent.parent.parent / 'data' / 'source' / 'tcg_sv_ex.json'
data_wrapper = json.load(open(data_file))
data = data_wrapper.get('cards', [])

print(f"Total cards: {len(data)}")

# Check dexId presence
with_dex = [c for c in data if c.get('dexId')]
without_dex = [c for c in data if not c.get('dexId')]

print(f"Cards WITH dexId: {len(with_dex)}")
print(f"Cards WITHOUT dexId: {len(without_dex)}")

print("\n=== Sample cards WITH dexId ===")
for card in with_dex[:10]:
    print(f"  - {card.get('name')}: dexId={card.get('dexId')}, category={card.get('category')}")

print("\n=== Cards WITHOUT dexId ===")
for card in without_dex[:20]:
    print(f"  - {card.get('name')}: category={card.get('category')}")

# Check specific problem cards mentioned in errors
problem_names = [
    "Lillie's Clefairy ex",
    "Erika's Vileplume ex",
    "Mega Meganium ex",
    "Team Rocket's Mewtwo ex"
]

print("\n=== Checking problem cards ===")
for name in problem_names:
    card = next((c for c in data if c.get('name') == name), None)
    if card:
        print(f"  - {name}: dexId={card.get('dexId')}, category={card.get('category')}")
    else:
        print(f"  - {name}: NOT FOUND in source data")
