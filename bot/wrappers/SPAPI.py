from urllib.parse import quote

import aiohttp

class APIException(Exception):
    "Base Exception for all API stuff"

class NoResult(APIException):
    "Raised when no results are returned"

class APIError(APIException):
    "Internal API error"

class Ratelimited(APIException):
    "Wait a bit more"

GOOGLE_FAVICON = "https://static1.anpoimages.com/wordpress/wp-content/uploads/2015/10/nexus2cee_Search-Thumb.png"

class SPAPIWrapper:
    def __init__(self):
        self.BASE_URL = "https://apiv2.spapi.ga"
        self.session = aiohttp.ClientSession()

    async def gsearch(self, q : str, image_search=False):
        if image_search:
            endpoint = f"/fun/imagesearch?search={q}&num=5"
            url = self.BASE_URL + endpoint
        else:
            endpoint = f'fun/gsearch?search={q}'
            url = self.BASE_URL + endpoint
            