from callbacks.downloadAttachment import DownloadAttachment
from callbacks.getFullSchoolInfo import GetFullSchoolInfo
from callbacks.getDiary import GetDiary

CALLBACKS = {
    "/downloadAttachment": DownloadAttachment,
    "/getFullSchoolInfo": GetFullSchoolInfo,
    "/getDiary": GetDiary,
}
