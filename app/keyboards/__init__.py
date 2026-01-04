from .user_keyboard import (MenuKeyboard,
                           AgreementInlineButtons,
                           ChoiceOfInstituteInlineButtons,
                           DirectionOfActivitiesInlineButtons,
                           ApplicationConfirmationInlineButtons,
                           ChangeOfApplicationInlineButtons,
                           ChoiceOfRoleInlineButtons,
                           RewardsChoiceInlineButtons,
                           ChangeRegistrationFormInlineButtons,
                           ConfirmRegistrationFormInlineButtons,
                           ReRegister,
                           SupportInlineButtons,
                           AddMaterial,
                           AddMaterialConfirm)

from .moderator_keyboard import (AdminPanelInlineButtons,
                                 RegisterNewUserInlineButtons,
                                 ProcessingUserApplicationInlineButtons,
                                 ModeratorSupportInlineButtons,
                                 ModeratorCloseRewards)

from .set_menu import(set_main_menu)

from .item_catalog_keyboard import(ItemKeyboard,
                                  show_item_details,
                                  show_purchase_confirmation,
                                  ITEM_DETAILS)

__all__ = [
    "MenuKeyboard",
    "AgreementInlineButtons",
    "ChoiceOfInstituteInlineButtons",
    "DirectionOfActivitiesInlineButtons",
    "ApplicationConfirmationInlineButtons",
    "ChangeOfApplicationInlineButtons",
    "ChoiceOfRoleInlineButtons",
    "RewardsChoiceInlineButtons",
    "ChangeRegistrationFormInlineButtons",
    "ConfirmRegistrationFormInlineButtons",
    "SupportInlineButtons",
    "AdminPanelInlineButtons",
    "RegisterNewUserInlineButtons",
    "ProcessingUserApplicationInlineButtons",
    "ReRegister",
    "ModeratorSupportInlineButtons",
    "set_main_menu",
    "ItemKeyboard",
    "show_item_details",
    "show_purchase_confirmation",
    "ITEM_DETAILS",
    "ModeratorCloseRewards",
    "AddMaterial",
    "AddMaterialConfirm"]