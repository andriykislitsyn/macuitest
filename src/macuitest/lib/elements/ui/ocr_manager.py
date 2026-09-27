"""Read and find text on screen with Apple Vision."""

import functools
import os
import re
from typing import Optional
from typing import Sequence

import Quartz
import Vision

from macuitest.config.constants import Region
from macuitest.config.settings import settings
from macuitest.lib.core import wait_condition
from macuitest.lib.elements.screen_element import default_region
from macuitest.lib.elements.ui.monitor import monitor

_FAST = Vision.VNRequestTextRecognitionLevelFast
_ACCURATE = Vision.VNRequestTextRecognitionLevelAccurate
# Vision misses short words such as "OK" in 1x captures and reads nearly all of them at 2x.
_MIN_SCALE = 2
# Vision reads typographic punctuation as ASCII, while labels copied from macOS keep it.
_PUNCTUATION = {
    "…": r"(?:…|\.\.\.)",
    **dict.fromkeys("'‘’", "['‘’]"),
    **dict.fromkeys('"“”', '["“”]'),
    **dict.fromkeys("-–—", "[-–—]"),
}


class OCRManager:
    """Screen text reader backed by Apple Vision."""

    def __init__(self, languages: Optional[Sequence[str]] = None):
        """Create a reader for `languages`, as Vision language codes such as "en-US" or "uk-UA".

        Without `languages`, the reader follows `settings.ocr.languages` at every lookup.

        Raises:
            TypeError: `languages` is a single string.
            ValueError: Vision can't read one of `languages`.
        """
        if isinstance(languages, str):
            raise TypeError(f"Pass languages as a sequence, such as ({languages!r},)")
        self.__languages = None if languages is None else tuple(languages)
        if self.__languages is not None:
            _levels(self.__languages, "languages")

    @property
    def languages(self) -> tuple[str, ...]:
        """The languages this reader recognizes."""
        return tuple(settings.ocr.languages) if self.__languages is None else self.__languages

    def find_text(self, text: str, region: Optional[Region] = None) -> list[Region]:
        """Return the box of every match of `text` in reading order, in global points.

        A match ignores case, treats any run of whitespace as one space, and must start and end
        on word boundaries. Typographic and ASCII punctuation match each other, such as "…" and
        "...". `region` defaults to `settings.screen`, then to every display, each
        captured separately. When every language supports fast mode, a fast pass runs first, and
        the accurate pass runs only if it finds nothing.

        Raises:
            ValueError: `text` is blank, or `region` is empty.
            RuntimeError: Vision fails to read the capture.
        """
        pattern = _pattern(text)
        origin = "settings.ocr.languages" if self.__languages is None else "languages"
        levels = _levels(self.languages, origin)
        captures = [(area, _capture(area)) for area in _search_regions(region)]
        for level in levels:
            boxes = [
                box
                for area, image in captures
                for box in self.__matches(pattern, image, area, level)
            ]
            if boxes:
                return _reading_order(boxes)
        return []

    def recognize(self, region: Region) -> str:
        """Return the text in `region`, one line per text line Vision reads, top to bottom.

        Raises:
            RuntimeError: Vision fails to read the capture.
        """
        observations = self._read(_capture(region), _ACCURATE)
        top_down = sorted(observations, key=lambda o: -o.boundingBox().origin.y)
        return os.linesep.join(o.topCandidates_(1)[0].string() for o in top_down)

    def wait_text(self, text: str, where: Region, timeout: int = 10) -> bool:
        """Return whether `text` appears in `where` within `timeout` seconds.

        Raises:
            ValueError: `text` is blank.
            RuntimeError: Vision fails to read the capture.
        """
        return bool(wait_condition(lambda: self.find_text(text, where), timeout=timeout))

    def _read(self, image, level) -> list:
        """Return Vision's text observations for the CGImage `image`."""
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(level)
        request.setRecognitionLanguages_(list(self.languages))
        # Language correction rewrites identifiers and doubles recognition time.
        request.setUsesLanguageCorrection_(False)
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(image, {})
        ok, error = handler.performRequests_error_([request], None)
        if not ok:
            raise RuntimeError(f"Vision text recognition failed: {error.localizedDescription()}")
        return list(request.results() or [])

    def __matches(self, pattern: re.Pattern, image, region: Region, level) -> list[Region]:
        boxes = []
        for observation in self._read(image, level):
            candidate = observation.topCandidates_(1)[0]
            line = candidate.string()
            for match in pattern.finditer(line):
                word, _ = candidate.boundingBoxForRange_error_(
                    _utf16_range(line, match.start(), match.end()), None
                )
                # Vision can fail to place a range inside the line, so fall back to the whole line.
                box = observation.boundingBox() if word is None else word.boundingBox()
                boxes.append(_to_region(box, region))
        return boxes


def _pattern(text: str) -> re.Pattern:
    words = text.split()
    if not words:
        raise ValueError("Text to find is blank")
    return re.compile(r"(?<!\w)" + r"\s+".join(map(_word, words)) + r"(?!\w)", re.IGNORECASE)


def _word(word: str) -> str:
    word = word.replace("...", "…")
    return "".join(_PUNCTUATION.get(char) or re.escape(char) for char in word)


def _reading_order(boxes: list[Region]) -> list[Region]:
    """Sort `boxes` top to bottom, and boxes on one line left to right.

    A box joins the current line when its top is within half the height of that line's first box.
    """
    lines: list[list[Region]] = []
    for box in sorted(boxes, key=lambda box: box.y1):
        first = lines[-1][0] if lines else None
        if first is not None and box.y1 - first.y1 < (first.y2 - first.y1) / 2:
            lines[-1].append(box)
        else:
            lines.append([box])
    return [box for line in lines for box in sorted(line, key=lambda box: box.x1)]


def _search_regions(region: Optional[Region]) -> list[Region]:
    region = region or default_region()
    # Vision downsamples a capture spanning every display so far that small text is lost.
    return [region] if region else monitor.displays


def _capture(region: Region):
    """Capture `region` at `_MIN_SCALE` pixels per point or more."""
    image = monitor.capture(region)
    scale = Quartz.CGImageGetWidth(image) / (region.x2 - region.x1)
    return image if scale >= _MIN_SCALE else _scaled(image, _MIN_SCALE / scale)


def _scaled(image, factor: float):
    width = round(Quartz.CGImageGetWidth(image) * factor)
    height = round(Quartz.CGImageGetHeight(image) * factor)
    context = Quartz.CGBitmapContextCreate(
        None,
        width,
        height,
        8,
        0,
        Quartz.CGColorSpaceCreateDeviceRGB(),
        Quartz.kCGImageAlphaPremultipliedLast,
    )
    Quartz.CGContextSetInterpolationQuality(context, Quartz.kCGInterpolationHigh)
    Quartz.CGContextDrawImage(context, Quartz.CGRectMake(0, 0, width, height), image)
    return Quartz.CGBitmapContextCreateImage(context)


def _to_region(box, region: Region) -> Region:
    """Map a Vision box, normalized with a bottom-left origin, to global points in `region`."""
    width, height = region.x2 - region.x1, region.y2 - region.y1
    return Region(
        x1=region.x1 + box.origin.x * width,
        y1=region.y1 + (1 - box.origin.y - box.size.height) * height,
        x2=region.x1 + (box.origin.x + box.size.width) * width,
        y2=region.y1 + (1 - box.origin.y) * height,
    )


def _utf16_range(text: str, start: int, end: int) -> tuple[int, int]:
    """Return `text[start:end]` as an NSRange (location, length), which counts UTF-16 units."""
    location = len(text[:start].encode("utf-16-le")) // 2
    return location, len(text[start:end].encode("utf-16-le")) // 2


@functools.cache
def _levels(languages: tuple[str, ...], origin: str) -> tuple:
    """Return the recognition levels to try for `languages`, fast first when it can read them.

    Raises:
        ValueError: Vision can't read one of `languages`, which came from `origin`.
    """
    unsupported = sorted(set(languages) - set(_supported(_ACCURATE)))
    if unsupported:
        raise ValueError(
            f"Vision can't read {unsupported} from {origin}. Supported: {_supported(_ACCURATE)}"
        )
    # Fast mode reads fewer languages, and returns nothing rather than an error for the rest.
    fast = (_FAST,) if set(languages) <= set(_supported(_FAST)) else ()
    return (*fast, _ACCURATE)


@functools.cache
def _supported(level) -> tuple[str, ...]:
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(level)
    languages, _ = request.supportedRecognitionLanguagesAndReturnError_(None)
    return tuple(languages)


ocr_manager = OCRManager()
