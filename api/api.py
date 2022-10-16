#!/usr/bin/env python
import requests
import hashlib

from errors import *


class NetSchoolAPI:
    def __init__(self, url):

        self._url = self._format_url(url)
        self._schools = []

        # Reset login variables
        self._reset_logindata()

        self._session_headers = {"referer": self._url}

        # Create new requests session
        self._session = requests.Session()

        # Get version info and NSSESSIONID cookie
        self.info = self.request(f"logindata").json()

    def getSchoolList(self, force=False):
        """Get school info list"""

        # Get school list from url if list is empty or force flag
        if self._schools == [] or force:

            # Get school list from url
            self._schools = self.request("addresses/schools").json()

        # Return school list
        return self._schools

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
        authdata = self.request("auth/getdata", method="POST").json()

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
        login_response = self.request("login", method="POST", data=payload).json()

        # Check if we logged in successfully
        if "at" not in login_response:
            raise LoginError(login_response["message"])

        # Add at to headers for request access
        self._session_headers["at"] = login_response["at"]

        # Save current login data for auto-relogin
        self._login_data = (username, password, school_name)

        # Get student id
        diary_info = self.request("student/diary/init").json()
        student = diary_info["students"][diary_info["currentStudentId"]]
        self._student_id = student["studentId"]

        # Get year id
        year_info = self.request("years/current").json()
        self._year_id = year_info["id"]

        return login_response

    def request(self, url, method="GET", headers={}, **kwargs):
        """Session request wrapper"""

        # Check if url is relative
        if not url.startswith(self._url):
            url = f"{self._url}/webapi/{url}"

        # Update request headers
        headers = self._session_headers | headers

        # Make a request
        response = self._session.request(method, url, headers=headers, **kwargs)

        # If access denied
        if response.status_code == 500:

            # Check if we have stored login data
            if self._login_data:

                # Try to login again
                self.login(*self._login_data)

                # Retry request
                return self.request(url, method, headers, **kwargs)
            else:

                raise RequestError(
                    "login before using requests that need authorization"
                )

        return response

    def logout(self):
        """Log out of user session"""

        # Reset login variables
        self._reset_logindata()

        return self.request("auth/logout", method="POST")

    def _reset_logindata(self):
        """Reset login data variables"""
        self._login_data = None
        self._student_id = None
        self._year_id = None

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
