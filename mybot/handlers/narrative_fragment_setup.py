from handlers.narrative_fragment_handler import register_narrative_fragment_handlers

def register_all_handlers(dp):
    """Register all narrative fragment handlers with the dispatcher."""
    register_narrative_fragment_handlers(dp)