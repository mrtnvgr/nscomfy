from callbacks.downloadAttachment import DownloadAttachment
from callbacks.getFullSchoolInfo import GetFullSchoolInfo
from callbacks.getDiary import GetDiary
from callbacks.changeAccountStudent import ChangeAccountStudent

CALLBACKS = {
    "/downloadAttachment": DownloadAttachment,
    "/getFullSchoolInfo": GetFullSchoolInfo,
    "/getDiary": GetDiary,
    "/changeAccountStudent": ChangeAccountStudent,
}
