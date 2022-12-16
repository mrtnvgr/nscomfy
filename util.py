import calendar
from datetime import datetime, timedelta
from html import escape as html_escape
from unicodedata import lookup as unilookup

SETTINGS_SCHEMA = {
    "general.shorten_subjects": {
        "name": "Сокращать названия предметов",
        "group": "Общее",
        "path": 'user["settings"]["general"]["shorten_subjects"]',
        "description": "Сокращать названия предметов",
        "default_value": True,
    },
    "diary.show_subject_time": {
        "name": "Показывать время уроков",
        "group": "Дневник",
        "path": 'user["settings"]["diary"]["show_subject_time"]',
        "description": "Показывать время уроков",
        "default_value": True,
    },
    "diary.show_subject_number": {
        "name": "Показывать номера уроков",
        "group": "Дневник",
        "path": 'user["settings"]["diary"]["show_subject_number"]',
        "description": "Показывать номера уроков",
        "default_value": False,
    },
    "term_marks.round_marks": {
        "name": "Округлять оценки",
        "group": "Оценки",
        "path": 'user["settings"]["term_marks"]["round_marks"]',
        "description": "Округлять оценки за четверть"
        "\n(Не округлённые оценки будут рядом в скобках)",
        "default_value": True,
    },
}

SHORTENED_SUBJECTS = {
    "Основы безопасности жизнедеятельности": "ОБЖ",
    "Информатика и ИКТ": "Информатика",
    "Изобразительное искусство": "ИЗО",
}

SETTINGS_SCHEMA["general.shorten_subjects"]["description"] += "\n\nСокращения:"
for full, short in SHORTENED_SUBJECTS.items():
    SETTINGS_SCHEMA["general.shorten_subjects"]["description"] += f"\n{full} -> {short}"


def formatDate(string: str):
    string = string.removesuffix("T00:00:00")
    # YYYY-MM-DD -> DD.MM.YYYY
    date = string.split("-")
    return ".".join(date[::-1])


def getMonthName(monthId):
    month_name = calendar.month_name[int(monthId)]

    translations = {
        "December": "Декабрь",
        "January": "Январь",
        "February": "Февраль",
        "March": "Март",
        "April": "Апрель",
        "May": "Май",
        "June": "Июнь",
        "July": "Июль",
        "August": "Август",
        "September": "Сентябрь",
        "October": "Октябрь",
        "November": "Ноябрь",
    }

    return translate(translations, month_name)


def humanizeDate(string: str):
    """Convert from XX.XX.XXXX -> {weekday}, {day} {month}"""
    dt = datetime.fromisoformat(string)
    newstring = dt.strftime("%A, %d %B")

    translations = {
        # Дни недели
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
        # Месяца
        "December": "Декабря",
        "January": "Января",
        "February": "Февраля",
        "March": "Марта",
        "April": "Апреля",
        "May": "Мая",
        "June": "Июня",
        "July": "Июля",
        "August": "Августа",
        "September": "Сентября",
        "October": "Октября",
        "November": "Ноября",
    }

    return translate(translations, newstring)


def translate(translations: dict, string: str):
    for name, key in translations.items():
        string = string.replace(name, key)
    return string


def normalizeHTMLText(text):
    return html_escape(text, quote=True)


def mark_to_sign(mark):
    emojis = {
        1: "1\uf30f\u20e3",
        2: "2\ufe0f\u20e3",
        3: "3\ufe0f\u20e3",
        4: "4\ufe0f\u20e3",
        5: "5\ufe0f\u20e3",
        None: getEmoji("HEAVY EXCLAMATION MARK SYMBOL"),
    }

    if mark in emojis:
        return emojis[mark]
    else:
        return str(mark)


def getEmoji(name):
    return unilookup(name)


def getSwitchEmoji(boolean):
    true = "HEAVY CHECK MARK"
    false = "CROSS MARK"
    return unilookup(true) if boolean else unilookup(false)


def detectEmptyTask(task):
    # This function filters tasks like "не задано."
    task = task.lower()
    task = task.rstrip(" ")
    task = task.removesuffix(".")
    task = task.strip("-")
    if task in ["не задано", "не указана"]:
        return True


def shortenSubjectName(subject):

    original_subject = subject

    # NOTE: названия могут содержать англиские буквы похожие на русские.
    similar_letters = {
        "A": "А",
        "a": "а",
        "B": "В",
        "e": "е",
        "E": "Е",
        "K": "К",
        "c": "с",
        "C": "С",
        "T": "Т",
        "X": "Х",
        "x": "х",
    }

    for key, value in similar_letters.items():
        subject = subject.replace(key, value)

    if subject in SHORTENED_SUBJECTS:
        return SHORTENED_SUBJECTS[subject]
    else:
        return original_subject


def checkAccountName(name):
    if name in ["Назад", "Добавить аккаунт"]:
        return
    if len(name) >= 128:
        return
    return True


def getTomorrowDelta(day):
    # Monday => Tuesday
    # Friday => Monday
    if day.weekday() > 3:
        return timedelta(days=7 - day.weekday())
    else:
        return timedelta(days=1)


def getYesterdayDelta(day):
    # Sunday => Friday
    if day.weekday() > 4:
        return timedelta(days=day.weekday() - 4)
    elif day.weekday() == 0:
        return timedelta(days=3)
    else:
        return timedelta(days=1)


def getRole(role):

    # Convert numeric roles to strings
    # NOTE: возможно это делается не так
    nums = {
        0: "Teacher",
        1: "Student",
        2: "Parent",
    }

    role = nums.get(role, role)

    # Translate english roles to russian
    translations = {
        "Teacher": "Учитель",
        "Student": "Ученик",
        "Parent": "Родитель",
    }

    return translations.get(role, role)
