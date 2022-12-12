from callbacks.downloadAttachment import DownloadAttachment
from callbacks.getFullSchoolInfo import GetFullSchoolInfo
from callbacks.getDiary import GetDiary
from callbacks.changeAccountStudent import ChangeAccountStudent
from callbacks.getBirthdays import GetBirthdays
from callbacks.showSetting import ShowSetting

CALLBACKS = {
    "/downloadAttachment": DownloadAttachment,
    "/getFullSchoolInfo": GetFullSchoolInfo,
    "/getDiary": GetDiary,
    "/changeAccountStudent": ChangeAccountStudent,
    "/getBirthdays": GetBirthdays,
    "/showSetting": ShowSetting,
}
