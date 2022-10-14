#!/usr/bin/env python
import requests
import hashlib


class NetSchoolAPI:
    def __init__(self, url):

        # Set global vars
        self.url = self._urlformat(url)
        self.schools = []

        # Create new requests session
        self.session = requests.Session()

        # Get version info and NSSESSIONID cookie
        self.info = self.session.get(f"{self.url}/webapi/logindata").json()

    def getSchoolList(self, force=False):
        """Get school info list"""

        # Get school list from url if list is empty or force flag
        if self.schools == [] or force:

            # Get school list from url
            self.schools = self.session.get(
                f"{self.url}/webapi/addresses/schools"
            ).json()

        # Return school list
        return self.schools

    def login(self, username, password, school_name):
        """Log into user account"""

        # Make sure that we have school info
        self.getSchoolList()

        # Init payload
        payload = {"LoginType": 1, "un": username}

        # Iterate through schools
        for school in self.schools:

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
        authdata = self.session.post(f"{self.url}/webapi/auth/getdata").json()

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
        return self.session.post(
            f"{self.url}/webapi/login", data=payload, headers={"referer": self.url}
        ).json()

    def logout(self):
        """Log out of user session"""

        return self.session.post(f"{self.url}/webapi/auth/logout")

    @staticmethod
    def _formaturl(url):
        """Format url"""
        url = url.rstrip("/")

        # Remove http prefix
        if url.startswith("http://"):
            url = url.removeprefix("http://")

        # Set https prefix
        if not url.startswith("https://"):
            url = f"https://{url}"

        return url
