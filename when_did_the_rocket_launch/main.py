import io
import os
from typing import List, NamedTuple, Text
from urllib.parse import quote, urljoin

from httpx import Client
from PIL import Image

API_BASE = os.getenv("API_BASE", "https://framex-dev.wadrid.net/api/")
VIDEO_NAME = os.getenv(
    "VIDEO_NAME", "Falcon Heavy Test Flight (Hosted Webcast)-wbSwFU6tY1c"
)


class Size(NamedTuple):
    """
    Represents a size
    """

    width: int
    height: int


class Color(NamedTuple):
    """
    8-bit components of a color
    """

    r: int
    g: int
    b: int


class Video(NamedTuple):
    """
    That's a video from the API
    """

    name: Text
    width: int
    height: int
    frames: int
    frame_rate: List[int]
    url: Text
    first_frame: Text
    last_frame: Text


DISPLAY_SIZE = Size(int(480 * 1.5), int(270 * 1.5))


def bisect(n, setter, frames=None, launched=None):
    """
    Runs a bisection.

    - `n` is the number of elements to be bisected
    - `mapper` is a callable that will transform an integer from "0" to "n"
      into a value that can be tested
    - `tester` returns true if the value is within the "right" range
    """
    first_call = frames is None

    if n < 1:
        raise ValueError("Cannot bisect an empty array")

    left, right = frames if not first_call else [0, n-1]

    if left + 1 < right:
        current_mid = int((left + right) / 2)

        if not first_call:
            if launched:
                right = current_mid
            else:
                left = current_mid

        new_mid = int((left + right) / 2)
        setter(new_mid)
        return [left, right], new_mid

    else:
        return [], right


class Frame:
    """
    Wrapper around frame data to help drawing it on the screen
    """

    def __init__(self, data):
        self.data = data
        # self.image = None


def get_image(data):
    pil_img = Image.open(io.BytesIO(data))
    pil_img.thumbnail(DISPLAY_SIZE)
    return {
        'image': pil_img,
        'data': data
    }


class FrameX:
    """
    Utility class to access the FrameX API
    """

    BASE_URL = API_BASE

    def __init__(self):
        self.client = Client(timeout=30)

    def video(self, video: Text) -> Video:
        """
        Fetches information about a video
        """

        r = self.client.get(urljoin(self.BASE_URL, f"video/{quote(video)}/"))
        r.raise_for_status()
        return Video(**r.json())

    def video_frame(self, video: Text, frame: int) -> bytes:
        """
        Fetches the JPEG data of a single frame
        """

        r = self.client.get(
            urljoin(self.BASE_URL, f'video/{quote(video)}/frame/{quote(f"{frame}")}/')
        )
        r.raise_for_status()
        return r.content


class FrameXBisector:
    """
    Helps to manage the display of images from the launch
    """

    BASE_URL = API_BASE

    def __init__(self, name):
        self.api = FrameX()
        self.video = self.api.video(name)
        self._index = 0
        self.frame = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, v):
        """
        When a new index is written, download the new frame
        """
        self._index = v

    @property
    def count(self):
        return self.video.frames

    def blit(self, index):
        """
        Returns current picture.
        """
        return get_image(self.api.video_frame(self.video.name, index))


def execute(bisector=None, launched=False, frames=None):
    """
    Runs a bisection algorithm on the frames of the video, the goal is
    to figure at which exact frame the rocket takes off.

    Images are displayed using pygame, but the interactivity happens in
    the terminal as it is much easier to do.
    """
    found = False
    image = None

    bisector = bisector if bisector is not None else FrameXBisector(VIDEO_NAME)

    def setter(n):
        print(f"{n} - did the rocket launch yet?")
        bisector.index = n

    frames_range, index = bisect(bisector.count, setter, frames, launched)

    if len(frames_range) == 0:
        # if its 0 then it finished
        setter(index)
        found = True
        print(f"Found! Take-off = {index}")
    else:
        image = bisector.blit(index)

    return bisector, frames_range, image, found, index
