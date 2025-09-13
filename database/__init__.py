@@ .. @@
 from .models import User
 from .narrative_models import UserNarrativeState
+from .shop_models import ShopItem, UserPurchase, UserInventory, ShopCategory, ShopDiscount
 from .emotional_models import (
     UserEmotionalProfile,
     EmotionalInteraction, 
     ConversationMemory,
     EmotionalTrigger,
     EmotionalAnalysisSession,
     ArchetypeClassification,
     EmotionalState,
     InteractionType
 )

 __all__ = [
     'User', 
     'UserNarrativeState',
+    'ShopItem',
+    'UserPurchase', 
+    'UserInventory',
+    'ShopCategory',
+    'ShopDiscount',
     'UserEmotionalProfile',
     'EmotionalInteraction',
     'ConversationMemory', 
     'EmotionalTrigger',
     'EmotionalAnalysisSession',
     'ArchetypeClassification',
     'EmotionalState',
     'InteractionType'
 ]