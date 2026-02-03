#!/usr/bin/env python3
"""Test TCGdex API for specific cards"""

import json
import sys
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'fetcher' / 'lib'))
from tcgdex_client import TCGdexClient

# Test cards that showed warnings
test_cards = [
    ("me02.5", "Erika's Vileplume ex"),
    ("me02.5", "Mega Meganium ex"),
    ("me02.5", "Lillie's Clefairy ex"),
    ("me02.5", "Team Rocket's Mewtwo ex"),
]

client = TCGdexClient(language='en')

print("Testing TCGdex API for problem cards:\n")

for set_id, card_name in test_cards:
    print(f"Searching for: {card_name} in {set_id}")
    
    # Get set data
    set_data = client.get_set(set_id)
    if not set_data:
        print(f"  ❌ Could not fetch set {set_id}\n")
        continue
    
    # Find card by name
    cards = set_data.get('cards', [])
    matching_card = None
    
    for card in cards:
        if card.get('name') == card_name:
            matching_card = card
            break
    
    if not matching_card:
        print(f"  ⚠️  Card not found in set\n")
        continue
    
    # Get full card details
    card_id = matching_card.get('id')
    full_card = client.get_card(card_id)
    
    if not full_card:
        print(f"  ❌ Failed to fetch full card details\n")
        continue
    
    # Check dexId
    dex_id = full_card.get('dexId', [])
    category = full_card.get('category')
    
    print(f"  ID: {card_id}")
    print(f"  Category: {category}")
    print(f"  dexId: {dex_id}")
    print(f"  ✅ Found\n")

print("\n=== Testing me02.5 set overview ===")
set_data = client.get_set('me02.5')
if set_data:
    cards = set_data.get('cards', [])
    ex_cards = [c for c in cards if c.get('name', '').endswith(' ex')]
    
    print(f"Total cards in me02.5: {len(cards)}")
    print(f"Cards ending with ' ex': {len(ex_cards)}")
    print(f"\nAll ex cards:")
    for card in ex_cards:
        print(f"  - {card.get('name')}")
