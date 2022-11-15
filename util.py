from html import escape as html_escape
from unicodedata import lookup as unilookup
from time import time as curtime


def get_timestamp():
    return int(curtime())


def formatDate(string: str):
    # YYYY-MM-DD -> DD.MM.YYYY
    date = string.split("-")
    return ".".join(date[::-1])


def normalizeHTMLText(text):
    return html_escape(text, quote=True)


def mark_to_sign(mark):
    emojis = {
        1: "1\uf30f\u20e3",
        2: "2\ufe0f\u20e3",
        3: "3\ufe0f\u20e3",
        4: "4\ufe0f\u20e3",
        5: "5\ufe0f\u20e3",
        None: unilookup("HEAVY EXCLAMATION MARK SYMBOL"),
    }

    if mark in emojis:
        return emojis[mark]
    else:
        return str(mark)


def detectEmptyTask(task):
    # This function filters tasks like "не задано."
    task = task.lower()
    task = task.rstrip(" ")
    task = task.removesuffix(".")
    if task == "не задано":
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
