from html import escape as html_escape


def formatDate(string: str):
    # YYYY-MM-DD -> DD.MM.YYYY
    date = string.split("-")
    return ".".join(date[::-1])


def normalizeHTMLText(text):
    return html_escape(text, quote=True)


def mark_to_sign(mark):
    emojis = {
        1: "\u0031\ufe0f\u20e3",
        2: "\u0032\ufe0f\u20e3",
        3: "\u0033\ufe0f\u20e3",
        4: "\u0034\ufe0f\u20e3",
        5: "\u0035\ufe0f\u20e3",
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
