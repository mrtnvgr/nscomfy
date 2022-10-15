#!/usr/bin/env python
import requests
import hashlib


class NetSchoolAPI:
    def __init__(self, url):

        # Set global vars
        self._url = self._format_url(url)
        self._schools = []

        # Create new requests session
        self.session = requests.Session()

        # Get version info and NSSESSIONID cookie
        self.info = self.request(f"{self._url}/webapi/logindata").json()

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
        return self.request("login", method="POST", data=payload).json()

    def request(self, url, method="GET", headers={}, **kwargs):
        """Session request wrapper"""

        # Check if url is relative
        if not url.startswith(self._url):
            url = f"{self._url}/webapi/{url}"

        # Add request headers
        headers["referer"] = self._url

        return self.session.request(method, url, headers=headers, **kwargs)

    def logout(self):
        """Log out of user session"""

        return self.request("auth/logout", method="POST")

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
