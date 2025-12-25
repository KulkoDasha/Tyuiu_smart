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
                           SupportInlineButtons)

from .moderator_keyboard import (AdminPanelInlineButtons,
                                 RegisterNewUserInlineButtons,
                                 ProcessingUserApplicationInlineButtons,
                                 ModeratorSupportInlineButtons)

from .set_menu import(set_main_menu)

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
    "set_main_menu"]