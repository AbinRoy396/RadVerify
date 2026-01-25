from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    base = Path("data/images")
    base.mkdir(parents=True, exist_ok=True)

    flat = np.full((256, 256, 3), 180, dtype=np.uint8)
    cv2.imwrite(str(base / "flat_reference.png"), flat)

    patterned = np.zeros((256, 256, 3), dtype=np.uint8)
    for y in range(256):
        value = 40 if (y // 8) % 2 == 0 else 210
        patterned[y, :, :] = value
    cv2.circle(patterned, (128, 128), 50, (255, 255, 255), 2)
    cv2.imwrite(str(base / "patterned_reference.png"), patterned)


if __name__ == "__main__":
    main()
