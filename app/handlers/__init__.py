from .admin import admin_router
from .moderator import moderator_router
from .other import other_router
from .user import user_router

__all__=["admin_router",
         "moderator_router",
         "other_router",
         "user_router",]