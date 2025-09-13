@@ .. @@
 from .auction_service import AuctionService
 from .user_service import UserService
 from .lore_piece_service import LorePieceService
+from .shop_service import ShopService
 from .scheduler import channel_request_scheduler, vip_subscription_scheduler, vip_membership_scheduler

 __all__ = [
@@ .. @@
     "AuctionService",
     "UserService",
     "LorePieceService",
+    "ShopService",
 ]