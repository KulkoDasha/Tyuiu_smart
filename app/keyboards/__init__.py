from .user_keyboard import (MenuKeyboard,
                           AgreementInlineButtons,
                           ApplicationConfirmationInlineButtons,
                           ChangeOfApplicationInlineButtons,
                           ChoiceOfRoleInlineButtons,
                           ReRegister,
                           SupportInlineButtons,
                           AddMaterial,
                           AddMaterialConfirm,
                           SelectingRewardInlineButtons,
                           ConfirmationRewardInlineButtons,
                           AboutTheCompetition,
                           MyTiukoins,
                           RecallTheAgreement,
                           DirectionOfActivitiesInlineButtons)

from .moderator_keyboard import (RegisterNewUserInlineButtons,
                                 ProcessingUserApplicationInlineButtons,
                                 ModeratorSupportInlineButtons,
                                 ModeratorCloseRewards)

from .set_menu import(set_main_menu)

from .item_catalog_keyboard import(catalog_of_rewards)

__all__ = [
    "MenuKeyboard",
    "AgreementInlineButtons",
    "ApplicationConfirmationInlineButtons",
    "ChangeOfApplicationInlineButtons",
    "ChoiceOfRoleInlineButtons",
    "SelectingRewardInlineButtons",
    "SupportInlineButtons",
    "RegisterNewUserInlineButtons",
    "ProcessingUserApplicationInlineButtons",
    "ReRegister",
    "ModeratorSupportInlineButtons",
    "set_main_menu",
    "catalog_of_rewards",
    "ModeratorCloseRewards",
    "AddMaterial",
    "AddMaterialConfirm",
    "ConfirmationRewardInlineButtons",
    "AboutTheCompetition",
    "MyTiukoins",
    "RecallTheAgreement",
    "DirectionOfActivitiesInlineButtons"]