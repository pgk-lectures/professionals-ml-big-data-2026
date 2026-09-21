from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from common import AUG_DIR, MAPS_DIR


def save(name, image):
    image = np.clip(image, 0, 1)
    plt.imsave(AUG_DIR / name, image)


def main():
    for path in sorted(MAPS_DIR.glob("*.png")):
        image = plt.imread(path)

        save(f"{path.stem}_rot90.png", np.rot90(image))
        save(f"{path.stem}_shift.png", np.roll(image, shift=(20, 30), axis=(0, 1)))

        bright = image.copy()
        bright[..., :3] = bright[..., :3] * 1.15
        save(f"{path.stem}_bright.png", bright)

        print(f"[OK] аугментация {path.name}")


if __name__ == "__main__":
    main()
