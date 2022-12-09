from html import escape as html_escape
from unicodedata import lookup as unilookup
from datetime import datetime, timedelta


def formatDate(string: str):
    string = string.removesuffix("T00:00:00")
    # YYYY-MM-DD -> DD.MM.YYYY
    date = string.split("-")
    return ".".join(date[::-1])


def convertDate(string: str):
    """Convert from XX.XX.XXXX -> {weekday}, {day} {month}"""
    dt = datetime.fromisoformat(string)
    newstring = dt.strftime("%A, %d %B")

    translations = {
        # Дни недели
        "Sunday": "Воскресенье",
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Monday": "Суббота",
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

    for name, key in translations.items():
        newstring = newstring.replace(name, key)

    return newstring


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


def detectEmptyTask(task):
    # This function filters tasks like "не задано."
    task = task.lower()
    task = task.rstrip(" ")
    task = task.removesuffix(".")
    task = task.strip("-")
    if task in ["не задано", "не указана"]:
        return True


def shortenSubjectName(subject):
    subjects = {
        "Основы безопасности жизнедеятельности": "ОБЖ",
        "Информатика и ИКТ": "Информатика",
    }

    if subject in subjects:
        return subjects[subject]
    else:
        return subject


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
