from urllib.parse import unquote_plus

from callbacks.callback import Callback


class DownloadAttachment(Callback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, _, button_data):
        resp = self.master.tg_api.sendMessage(self.user_id, "Подождите...")
        message_id = resp["message_id"]

        if not self.master.ns.checkSession(self.user_id):
            self.master.editButtons(
                self.user_id,
                message_id,
                "Перед тем как скачать вложение, войдите в аккаунт.",
                [],
            )
            return True

        api = self.master.ns.sessions[self.user_id]

        studentId = api.student_info["id"]

        if str(studentId) != button_data[0]:
            self.master.editButtons(
                self.user_id,
                message_id,
                "Текущий аккаунт не имеет доступа к этому вложению."
                "\nВойдите в подходящий аккаунт или запросите кнопку еще раз.",
                [],
            )
            return True

        assignmentId = button_data[1]
        # Для получения доступа к вложению запрашиваем список вложений задания
        api.getDiaryAttachments(assignmentId)

        attachmentId = button_data[2]

        attachmentUrl = api.getAttachmentUrl(attachmentId)
        attachment = api.request(attachmentUrl)
        attachmentData = attachment.content
        attachmentSize = int(attachment.headers.get("content-length", 0))
        attachmentType = attachment.headers.get("content-type", "")

        attachmentName = attachment.headers.get("filename", "unknown")
        attachmentName = unquote_plus(attachmentName)

        maxSize = 1000000
        if attachmentType.startswith("image/"):
            maxSize *= 10
        else:
            maxSize *= 50

        if attachmentSize > maxSize:
            self.master.editButtons(
                self.user_id,
                message_id,
                "Размер файла слишком большой, мы не можем отправить вам файл."
                "\nВ будущем, это будет исправлено.",
                [],
            )
            return True

        self.master.tg_api.deleteMessage(self.user_id, message_id)

        self.master.tg_api.sendFile(self.user_id, attachmentName, attachmentData)

        return True
