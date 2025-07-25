import re
from typing import Union

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None
try:
    from youtubesearchpython.__future__ import VideosSearch
except ImportError:
    try:
        from youtube_search import YoutubeSearch as VideosSearch
    except ImportError:
        VideosSearch = None


class RessoAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/m.resso.com\/)(.*)$"
        self.base = "https://m.resso.com/"

    async def valid(self, link: str):
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def track(self, url, playid: Union[bool, str] = None):
        if playid:
            url = self.base + url
            
        if not AIOHTTP_AVAILABLE or not BS4_AVAILABLE:
            return False  # لا يمكن معالجة Resso بدون aiohttp أو bs4
            
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False
                html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("meta"):
            if tag.get("property", None) == "og:title":
                title = tag.get("content", None)
            if tag.get("property", None) == "og:description":
                des = tag.get("content", None)
                try:
                    des = des.split("·")[0]
                except:
                    pass
        if des == "":
            return
        results = VideosSearch(title, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            ytlink = result["link"]
            vidid = result["id"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": ytlink,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid
