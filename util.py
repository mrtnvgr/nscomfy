from html import escape as html_escape


def formatDate(string: str):
    # YYYY-MM-DD -> DD-MM-YYYY
    date = string.split("-")
    return "-".join(date[::-1])


def normalizeHTMLText(text):
    return html_escape(text, quote=True)
