from keyboards.account_selection import AccountSelection
from keyboards.main_menu import MainMenu
from keyboards.diary import Diary
from keyboards.settings import Settings
from keyboards.settings_account import SettingsAccount
from keyboards.info import Info


KEYBOARDS = {
    "account_selection": AccountSelection,
    "mm": MainMenu,
    "diary": Diary,
    "settings": Settings,
    "settings_account": SettingsAccount,
    "info": Info,
}
