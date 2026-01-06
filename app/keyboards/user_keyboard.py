from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Bot

from ..lexicon import LEXICON_USER_KEYBOARD

class MenuKeyboard:
    """
    Клавиатура для меню пользователя
    """

    @staticmethod
    def get_keyboard_menu():
        button_submit_application= KeyboardButton(text=LEXICON_USER_KEYBOARD["submit_application"])
        button_my_tyuiu_coins= KeyboardButton(text=LEXICON_USER_KEYBOARD["my_tyuiu_coins"])
        button_catalog_of_rewards= KeyboardButton(text=LEXICON_USER_KEYBOARD["catalog_of_rewards"])
        button_agreement_of_contest= KeyboardButton(text=LEXICON_USER_KEYBOARD["agreement_of_contest"])
        button_support= KeyboardButton(text=LEXICON_USER_KEYBOARD["support"])

        builder = ReplyKeyboardBuilder()
        builder.add(button_submit_application, button_my_tyuiu_coins, button_catalog_of_rewards,
                    button_agreement_of_contest, button_support)
        
        builder.adjust(1, 2, 2) 
        
        return builder.as_markup(resize_keyboard=True)
    
class AgreementInlineButtons:
    """
    Инлайн-кнопки согласия
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["read_the_agreement"],callback_data="read_the_agreement")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["give_agreement"], callback_data="give_agreement")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["refuse_agreement"], callback_data= "refuse_agreement")]
                                ])
        
        return keyboard


class ChoiceOfInstituteInlineButtons:
    """
    Инлайн кнопки выбора института обучения
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["institute_of_architecture_and_design"], callback_data="institute_of_architecture_and_design")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["civil_engineering_institute"], callback_data="civil_engineering_institute")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["higher_school_of_engineering"], callback_data="higher_school_of_engineering")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["higher_school_of_digital_technologies"], callback_data="higher_school_of_digital_technologies")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["oil_and_gas_institute"], callback_data="oil_and_gas_institute")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["institute_of_service_and_industry_management"], callback_data="institute_of_service_and_industry_management")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["institute_of_technology"], callback_data="institute_of_technology")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["institute_of_correspondence_and_distance_education"], callback_data="institute_of_correspondence_and_distance_education")],
                                ])        
                
        return keyboard
    
class DirectionOfActivitiesInlineButtons:
    """
    Инлайн кнопки выбора направления внеучебного направления
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_social_design"], callback_data="topic_social_design")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_research_technologies"], callback_data="topic_research_technologies")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_search_rescue_military"], callback_data="topic_search_rescue_military")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_entrepreneurship"], callback_data="topic_entrepreneurship")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_patriotism_history"], callback_data="topic_patriotism_history")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_intellectual_games"], callback_data="topic_intellectual_games")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_tiu_competence_center"], callback_data="topic_tiu_competence_center")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_scenic_creativity"], callback_data="topic_scenic_creativity")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_applied_creativity"], callback_data="topic_applied_creativity")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_media_communications"], callback_data="topic_media_communications")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_volunteering"], callback_data="topic_volunteering")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_ecology_nature"], callback_data="topic_ecology_nature")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_sport"], callback_data="topic_sport")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_tourism_travel"], callback_data="topic_tourism_travel")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_digital_sport"], callback_data="topic_digital_sport")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_student_units"], callback_data  ="topic_student_units")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_united_student_council"], callback_data="topic_united_student_council")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["topic_headman"], callback_data="topic_headman")]
                                ])        
                
        return keyboard
    
class ChoiceOfRoleInlineButtons:
    """
    Инлайн кнопки выбора роли участника в мероприятии
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_spectator"], callback_data="role_spectator")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_participant"], callback_data="role_participant")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_finalist"], callback_data="role_finalist")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_winner"], callback_data="role_winner")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_volunteer"], callback_data="role_volunteer")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_coorganizer"], callback_data="role_coorganizer")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_organizer"], callback_data="role_organizer")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_mentor"], callback_data="role_mentor")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_speaker"], callback_data="role_speaker")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["role_leader"], callback_data="role_leader")]
                            ])        
                
        return keyboard

class ApplicationConfirmationInlineButtons:
    """
    Инлайн-кнопки подтверждения заявки
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["confirm_application"], callback_data="confirm_application")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_application"], callback_data= "edit_application")]
                                ])
        
        return keyboard
    
class ChangeOfApplicationInlineButtons:
    """
    Инлайн-кнопки изменения заявки
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_direction_of_activities"],callback_data="edit_direction_of_activities")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_event_name"], callback_data="edit_event_name")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_event_date"], callback_data="edit_event_date")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_event_location"], callback_data="edit_event_location")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_role"], callback_data= "edit_role")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["edit_confirmation_material"], callback_data= "edit_confirmation_material")]
                                ])
        
        return keyboard

class RewardsChoiceInlineButtons:
    """
    Инлайн-кнопки получения поощрений (ПОЗЖЕ СДЕЛАТЬ ДИНАМИЧЕСКИМИ: возможность добавления определённых подарков)
    """
    
    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["item_pencil"], callback_data="item_pencil")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["item_sticker_pack"], callback_data="item_stickerpack")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["item_notebook"], callback_data="item_notebook")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["item_shopper"], callback_data="item_shopper")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["item_sweatshirt"], callback_data="item_sweatshirt")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["item_olympia_course"], callback_data="item_olympia_course")]
                            ])
        
        return keyboard


class ChangeRegistrationFormInlineButtons:
    """
    Инлайн кнопки для изменения анкеты
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["full_name"], callback_data="full_name")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["institute"], callback_data="institute")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["direction"], callback_data="direction")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["course"], callback_data="course")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["group"], callback_data="group")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["start_year"], callback_data="start_year")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["end_year"], callback_data="end_year")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["phone_number"], callback_data="phone_number")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["email"], callback_data="email")]
                            ])        
                
        return keyboard

class ConfirmRegistrationFormInlineButtons:
    """
    Инлайн-кнопки подтверждения заявки
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["save_registration_form"], callback_data="save_registration_form")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["change_registration_form"], callback_data= "change_registration_form")]
                                ])
        
        return keyboard

class SupportInlineButtons:
    """
    Инлайн-клавиатура поддержки
    """
    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["support_write_moderator_of_the_direct"], callback_data="write_moderator_of_the_direct")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["support_feedback"], callback_data="feedback")],
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["support_error"], callback_data= "error")]
                                ])
        
        return keyboard

class ReRegister:
    """
    Инлайн-кнопка для перепрохождения регистрации
    """

    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["re_register"], callback_data= "re_register")]
                                ])
        
        return keyboard

class AddMaterial:
    """
    Кнопки для добавления дополнительных материалов в заявку 
    """
    
    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["add_more_material"], callback_data="add_more_material")],
            [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["finish_application"], callback_data="finish_application")]
        ])
        
        return keyboard

class AddMaterialConfirm:
    """
    Кнопки для завершения заявки
    """
    
    @staticmethod
    def get_inline_keyboard():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_USER_KEYBOARD["finish_application"], callback_data="finish_application")]
        ])
        
        return keyboard

