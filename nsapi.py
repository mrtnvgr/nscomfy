#!/usr/bin/env python

import hashlib
import logging
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import Optional

import requests
from requests.exceptions import ConnectionError, InvalidURL

from errors import *


class NetSchoolAPI:
    def __init__(self, user_id: int, url: str):

        self.user_id = user_id

        self._url = self._format_url(url)
        self._schools = []
        self._districts = []

        # Reset login variables
        self._reset_logindata()

        # Create headers
        self._session_headers = {"referer": self._url}

        # Create new requests session
        self._session = requests.Session()

        # Get version info and NSSESSIONID cookie
        try:
            ns_info = self.request("logindata", relogin=False, retry=False)
            if ns_info.status_code == 503:
                raise TechnicalMaintenanceError
            self.ns_info = ns_info.json()
        except (ConnectionError, InvalidURL):
            raise InvalidUrlError("given url is invalid")
        except JSONDecodeError:
            raise NotANetSchoolError("given url isn't a net school url")

    def getSchoolList(self, force=False):
        """Get school info list"""

        # Get school list from url if list is empty or force flag
        if self._schools == [] or force:

            # Get school list from url
            self._schools = self.request("addresses/schools").json()

        # Return school list
        return self._schools

    def getMunicipalityDistrictList(self, force=False):
        """Get districts list"""

        if self._districts == [] or force:

            self._districts = self.request(
                "loginform", params={"LASTNAME": "sid"}
            ).json()["items"]

        # Return list
        return self._districts

    def getSchoolInfo(self):
        """Get full school information"""

        return self.request(f"schools/{self._school_id}/card").json()

    def getAccountInfo(self):
        """Get account information"""

        return self.request("mysettings").json()

    def getBirthdays(self, monthId):
        """Get birthdays information"""

        params = {
            "classId": "-1",
            "month": monthId,
            "roles": "0",
        }

        return self.request("schedule/month/birthdays", params=params).json()

    def getBirthdayFilters(self):
        """Get birthday filters"""

        return self.request("schedule/month/filterpanel?month=").json()

    def getMarksReportFilters(self):
        """Get marks report filters"""

        return self.request("reports/studenttotal").json()

    def getUserPhoto(self):
        """Get user photo"""

        params = {
            "ver": self.ns_info.get("version"),
            "at": self._session_headers.get("at"),
            "userId": self.student_info.get("id"),
        }

        return self.request("users/photo", params=params).content

    def getDiary(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ):
        """Get diary info"""

        if not start:
            # Start = Monday
            start = datetime.today() - timedelta(days=datetime.today().weekday())

        if not end:
            end = start + timedelta(days=5)

        for date in [start, end]:
            if type(date) is not str:
                date = date.isoformat()

        response = self.request(
            "student/diary",
            params={
                "studentId": self.student_info["id"],
                "yearId": self._year_id,
                "weekStart": start,
                "weekEnd": end,
            },
        ).json()

        return response

    def getDiaryAttachments(self, assignId):
        """Get diary attachments"""

        if type(assignId) is not list:
            assignId = [assignId]

        response = self.request(
            "student/diary/get-attachments",
            params={"studentId": self.student_info["id"]},
            json={"assignId": assignId},
            method="POST",
        ).json()

        if not response:
            return {}

        return {
            assignment["assignmentId"]: assignment["attachments"]
            for assignment in response
        }

    def getAttachmentUrl(self, attachmentId):
        ver = self.ns_info.get("version", "")
        userId = self.student_info.get("id", "")
        at = self._session_headers.get("at", "")
        url = f"attachments/{attachmentId}"
        url += f"?ver={ver}&at={at}&userId={userId}"
        return url

    def getOverdueTasks(self):
        """Get overdue tasks"""

        response = self.request(
            "student/diary/pastMandatory",
            params={"studentId": self.student_info["id"], "yearId": self._year_id},
        ).json()

        # Add task type info
        for index, task in enumerate(response):

            # Get type id value
            typeId = task["typeId"]
            # Get type value from assignment types
            typeName = self._assignment_types[typeId]
            # Append value to task
            response[index]["type"] = typeName

        return response

    def getAssignmentTypeId(self, name):

        for a_id in self._assignment_types:

            value = self._assignment_types[a_id]

            if value == name:

                return a_id

    def login(self, username, password, school_name):
        """Log into user account"""

        # Make sure that we have school info
        self.getSchoolList()

        # Init payload
        payload = {"LoginType": 1, "un": username}

        # Iterate through schools
        for school in self._schools:

            # Check school name
            if school["name"] == school_name:

                self._school_id = school["id"]

                # Add school info to payload
                payload["cid"] = school["countryId"]
                payload["sid"] = school["stateId"]
                payload["pid"] = school["municipalityDistrictId"]
                payload["cn"] = school["cityId"]
                payload["sft"] = school["funcType"]
                payload["scid"] = school["id"]

        if "scid" not in payload:
            raise SchoolNotFoundError(school_name)

        # Get auth data (var, lt, salt)
        authdata = self.request("auth/getdata", method="POST", relogin=False).json()

        # Pop salt from auth data
        salt = authdata.pop("salt")

        # Encode password
        encoded_password = (
            hashlib.md5(password.encode("windows-1251")).hexdigest().encode()
        )

        # Add pw and pw2 keys to payload
        payload["pw2"] = hashlib.md5(salt.encode() + encoded_password).hexdigest()
        payload["pw"] = payload["pw2"][: len(password)]

        # Add lt and ver to payload
        payload.update(authdata)

        # Log in
        login_response = self.request(
            "login", method="POST", data=payload, relogin=False
        ).json()

        # Check if we logged in successfully
        if "at" not in login_response:
            raise LoginError(login_response["message"])

        # Add at to headers for request access
        self._session_headers["at"] = login_response["at"]

        # Check if we have a supported role
        mysettings = self.request("mysettings").json()
        roles = mysettings["roles"]
        if not ("Student" in roles or "Parent" in roles):
            raise UnsupportedRoleError(roles)

        # Save current login data for auto-relogin
        self._login_data = (username, password, school_name)

        # Get students
        self._students = self.request("context/students").json()
        if not self._students:
            self._students = [login_response["accountInfo"]["user"]]

        # Get year id
        year_info = self.request("years/current").json()
        self._year_id = year_info["id"]

        # Get year dates
        self._year_start = year_info["startDate"].split("T")[0]
        self._year_end = year_info["endDate"].split("T")[0]

        # Get assignment types
        assignment_types = self.request(
            "grade/assignment/types", params={"all": False}
        ).json()
        self._assignment_types = {
            assignment["id"]: assignment["name"] for assignment in assignment_types
        }

        # Get active sessions count
        # self._active_sessions = self.request("context/activeSessions").json()

        # Get unreaded mail messages count
        self._unreaded_mail_messages = self.request("mail/messages/unreaded").json()

        return login_response

    def setStudent(self, student_name):
        """Set api student"""

        for student in self._students:
            if student["name"] == student_name:
                self.student_info = student
                break

        if not self.student_info:
            raise UnknownStudentError(f'this account doesn\'t have "{student_name}"')

    def request(
        self, url, method="GET", headers={}, relogin=True, retry=True, **kwargs
    ):
        """Session request wrapper"""

        # Check if url is relative
        if not url.startswith(self._url):
            url = f"{self._url}/webapi/{url}"

        # Update request headers
        rheaders = self._session_headers | headers

        # Make a request
        try:
            response = self._session.request(method, url, headers=rheaders, **kwargs)
        except Exception:
            if retry:
                # Retry request
                return self.request(url, method, headers, relogin=False, **kwargs)
            else:
                raise

        status_code = response.status_code

        # If access denied and we are logged in, try to relogin
        if status_code == 500 and relogin:

            # Check if we have stored login data
            if self._login_data:

                rurl = self._getMethodNameFromUrl(url)
                logging.debug(f"[NS] {self.user_id}: {rurl} RELOGIN")

                # Try to login again
                self.login(*self._login_data)

                # Retry request
                return self.request(url, method, headers, relogin=False, **kwargs)
            else:

                raise RequestError(
                    "login before using requests that need authorization"
                )

        rurl = self._getMethodNameFromUrl(url)
        logging.debug(f"[NS] {self.user_id}: {rurl} {status_code} relogin={relogin}")

        return response

    def logout(self):
        """Log out of user session"""

        # Reset login variables
        self._reset_logindata()

        return self.request("auth/logout", method="POST")

    def _reset_logindata(self):
        """Reset login data variables"""
        self._login_data = ()

        self.ns_info = {}

        self._students = []
        self.student_info = {}

        self._year_id = None
        self._year_start = None
        self._year_end = None

        self._school_id = None

        # self._active_sessions = None
        self._unreaded_mail_messages = None

    def _getMethodNameFromUrl(self, url):
        """.../method?somestuff=... -> method"""
        url = url.removeprefix(f"{self._url}/webapi/")
        url = url.split("?")[0]
        return url

    @staticmethod
    def _format_url(url):
        """Format url"""
        url = url.rstrip("/")

        # Remove http prefix
        if url.startswith("http://"):
            url = url.removeprefix("http://")

        # Set https prefix
        if not url.startswith("https://"):
            url = f"https://{url}"

        return url
