from .user_keyboard import (MenuKeyboard,
                           AgreementInlineButtons,
                           ChoiceOfInstituteInlineButtons,
                           DirectionOfActivitiesInlineButtons,
                           ApplicationConfirmationInlineButtons,
                           ChangeOfApplicationInlineButtons,
                           ChoiceOfRoleInlineButtons,
                           ChangeRegistrationFormInlineButtons,
                           ConfirmRegistrationFormInlineButtons,
                           ReRegister,
                           SupportInlineButtons,
                           AddMaterial,
                           AddMaterialConfirm,
                           SelectingRewardInlineButtons,
                           ConfirmationRewardInlineButtons,
                           AboutTheCompetition,
                           MyTiukoins,
                           RecallTheAgreement)

from .moderator_keyboard import (RegisterNewUserInlineButtons,
                                 ProcessingUserApplicationInlineButtons,
                                 ModeratorSupportInlineButtons,
                                 ModeratorCloseRewards)

from .set_menu import(set_main_menu)

from .item_catalog_keyboard import(catalog_of_rewards)

__all__ = [
    "MenuKeyboard",
    "AgreementInlineButtons",
    "ChoiceOfInstituteInlineButtons",
    "DirectionOfActivitiesInlineButtons",
    "ApplicationConfirmationInlineButtons",
    "ChangeOfApplicationInlineButtons",
    "ChoiceOfRoleInlineButtons",
    "SelectingRewardInlineButtons",
    "ChangeRegistrationFormInlineButtons",
    "ConfirmRegistrationFormInlineButtons",
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
    "RecallTheAgreement"]