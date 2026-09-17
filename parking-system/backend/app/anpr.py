"""Number-plate read hook.

Today this is simulated: the dashboard (or POST /simulate/anpr) supplies a
plate string. When a camera is wired later, replace `read_plate` with
OpenCV localization + Tesseract/OpenALPR OCR. The check-in API still only
needs the plate string, so allocation and billing stay unchanged.
"""
import random
import string


def fake_plate() -> str:
    """Stand-in for a camera frame → OCR result."""
    state = random.choice(["RJ", "MH", "DL", "KA", "TN"])
    district = f"{random.randint(1, 99):02d}"
    series = "".join(random.choices(string.ascii_uppercase, k=2))
    number = f"{random.randint(1, 9999):04d}"
    return f"{state}{district}{series}{number}"


def read_plate(image_bytes=None) -> str:
    """Future hardware entry point. Simulation ignores image bytes."""
    _ = image_bytes
    return fake_plate()
