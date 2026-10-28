from pathlib import Path

from pico2d import load_image


class Grass:
    def __init__(self):
        image_path = Path(__file__).resolve().with_name('grass.png')
        self.image = load_image(str(image_path))

    def draw(self):
        self.image.draw(400, 30)

    def update(self):
        pass