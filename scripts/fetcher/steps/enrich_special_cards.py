"""
Enrich special cards (trainers, stadiums, etc.) with generic type images.
"""
import json
import os
from typing import Dict, Any
from .base import BaseStep


class EnrichSpecialCardsStep(BaseStep):
    """Enrich trainer/special cards with generic type images."""
    
    def execute(self, context: 'PipelineContext', params: Dict[str, Any]) -> 'PipelineContext':
        """
        Enrich trainer/special cards with generic type images.
        
        Args:
            context: Pipeline context
            params: Parameters dict containing:
                - images_dir: Directory containing special card images
        
        Reads from context.data['tcg_set_source']
        Writes enriched data back to context.data['tcg_set_source']
        
        Returns:
            Updated pipeline context
        """
        images_dir = params.get('images_dir')
        
        if not images_dir:
            return {'status': 'error', 'message': 'Missing required parameter: images_dir'}
        
        print(f"🎨 Enriching special cards with type images")
        
        # Load cards from context
        tcg_data = context.data.get('tcg_set_source')
        if not tcg_data:
            raise ValueError("No TCG set data found in context. Make sure fetch_tcgdex_set ran before this step.")
        
        cards = tcg_data.get('cards', [])
        print(f"📋 Found {len(cards)} cards")
        
        # Map trainer types to image files
        type_to_image = {
            'Supporter': os.path.join(images_dir, 'supporter.png'),
            'Item': os.path.join(images_dir, 'item.png'),
            'Stadium': os.path.join(images_dir, 'stadium.png'),
            'Tool': os.path.join(images_dir, 'tool.png'),
            'Energy': os.path.join(images_dir, 'energy.png'),
        }
        
        # Verify images exist
        for trainer_type, image_path in type_to_image.items():
            if not os.path.exists(image_path):
                print(f"⚠️  Warning: Image not found for {trainer_type}: {image_path}")
        
        # Enrich cards
        enriched_count = 0
        
        for card in cards:
            # Only process trainer/energy cards (non-Pokemon)
            if card.get('card_type') == 'trainer':
                trainer_type = card.get('trainer_type', 'Trainer')
                
                # Map to image
                image_path = type_to_image.get(trainer_type)
                if image_path and os.path.exists(image_path):
                    card['special_card_image'] = image_path
                    enriched_count += 1
        
        print(f"✅ Enriched {enriched_count} special cards with type images")
        
        # Update data in context
        tcg_data['cards'] = cards
        context.data['tcg_set_source'] = tcg_data
        
        return context
