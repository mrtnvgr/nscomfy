from callbacks.changeAccountStudent import ChangeAccountStudent
from callbacks.downloadAttachment import DownloadAttachment
from callbacks.getBirthdays import GetBirthdays
from callbacks.getDiary import GetDiary
from callbacks.getFullSchoolInfo import GetFullSchoolInfo
from callbacks.showSetting import ShowSetting
from callbacks.toggleSetting import ToggleSetting

CALLBACKS = {
    "/downloadAttachment": DownloadAttachment,
    "/getFullSchoolInfo": GetFullSchoolInfo,
    "/getDiary": GetDiary,
    "/changeAccountStudent": ChangeAccountStudent,
    "/getBirthdays": GetBirthdays,
    "/showSetting": ShowSetting,
    "/toggleSetting": ToggleSetting,
}
