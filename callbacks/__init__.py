from callbacks.changeAccountStudent import ChangeAccountStudent
from callbacks.deleteAccount import DeleteAccount
from callbacks.deleteThisMessage import DeleteThisMessage
from callbacks.downloadAttachment import DownloadAttachment
from callbacks.getBirthdays import GetBirthdays
from callbacks.getDiary import GetDiary
from callbacks.getDiaryTests import GetDiaryTests
from callbacks.getFullSchoolInfo import GetFullSchoolInfo
from callbacks.showSetting import ShowSetting
from callbacks.toggleSetting import ToggleSetting

CALLBACKS = {
    "/downloadAttachment": DownloadAttachment,
    "/getFullSchoolInfo": GetFullSchoolInfo,
    "/getDiary": GetDiary,
    "/getDiaryTests": GetDiaryTests,
    "/changeAccountStudent": ChangeAccountStudent,
    "/getBirthdays": GetBirthdays,
    "/showSetting": ShowSetting,
    "/toggleSetting": ToggleSetting,
    "/deleteThisMessage": DeleteThisMessage,
    "/deleteAccount": DeleteAccount,
}
