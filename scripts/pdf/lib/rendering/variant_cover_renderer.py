"""
DEPRECATED: VariantCoverRenderer wrapper has been removed.

Use UnifiedCoverRenderer directly:

    from scripts.lib.rendering import UnifiedCoverRenderer
    
    renderer = UnifiedCoverRenderer(language='de')
    renderer.render_cover(canvas, pokemon_list, cover_data=variant_dict, color='#FF6600')

This file is kept for reference only and will be removed in a future version.
"""

raise ImportError(
    "VariantCoverRenderer wrapper has been deprecated and removed. "
    "Use UnifiedCoverRenderer directly instead:\n\n"
    "    from scripts.lib.rendering import UnifiedCoverRenderer\n"
    "    renderer = UnifiedCoverRenderer(language='de')\n"
    "    renderer.render_cover(canvas, pokemon_list, cover_data=variant_dict, color='#FF6600')"
)
