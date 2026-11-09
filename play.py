"""Play the portrait edition of A Festival of Light."""

from functools import lru_cache
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageTk

import diwali_ramayana_movie as movie
import diwali_ramayana_record_v3 as portrait


SIZE = (1080, 1920)
INTRO_DURATION = 2
DURATION = INTRO_DURATION + movie.DURATION
PREVIEW_FPS = 30
ART_TOP = 396
ART_SIZE = (SIZE[0], round(portrait.H * SIZE[0] / portrait.W))
INK = (4, 6, 12)
GOLD = (245, 199, 121)
PAPER = (237, 230, 216)
INTRO_BRIGHTNESS = tuple(round(value + .16 * value * (1 - value / 255)) for value in range(256)) * 3


@lru_cache(maxsize=None)
def title_font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", size)
    except OSError:
        return movie.mono(size)


def centered(draw, text, y, font, fill):
    draw.text((SIZE[0] // 2, y), text, font=font, fill=fill, anchor="mt",
              stroke_width=2, stroke_fill=INK)


def smooth(progress):
    progress = max(0, min(1, progress))
    return progress * progress * (3 - 2 * progress)


def intro_mask():
    width, height = ART_SIZE
    strip = Image.new("L", (1, height))
    strip.putdata([round(255 * smooth(y / 78) * smooth((height - 1 - y) / 112))
                   for y in range(height)])
    return strip.resize((width, height))


class Reel:
    def __init__(self):
        self.intro_scene = movie.Ramayana()
        self.scene = portrait.Ramayana()
        self.intro_mask = intro_mask()
        self.plate = Image.new("RGB", SIZE, INK)
        draw = ImageDraw.Draw(self.plate)
        centered(draw, "D I W A L I", 214, movie.mono(30), GOLD)
        centered(draw, "A Festival of Light", 254, title_font(58), GOLD)

    def intro(self, time):
        progress = smooth(time / INTRO_DURATION)
        source = self.intro_scene.frame(4.03 + .12 * progress)
        width = 610 - 85 * progress
        height = width * ART_SIZE[1] / ART_SIZE[0]
        left, top = 960 - width / 2, 475 - height / 2
        crop = (left, top, left + width, top + height)
        art = source.resize(ART_SIZE, Image.Resampling.LANCZOS, box=crop).point(INTRO_BRIGHTNESS)
        frame = Image.new("RGB", SIZE, INK)
        frame.paste(art, (0, 400), self.intro_mask)
        draw = ImageDraw.Draw(frame)
        centered(draw, "I animated the", 214, title_font(70), PAPER)
        centered(draw, "Ramayana in Python", 303, title_font(76), GOLD)
        return frame

    def frame(self, time):
        if time < INTRO_DURATION:
            return self.intro(time)

        story_time = time - INTRO_DURATION
        art = self.scene.frame(story_time).resize(ART_SIZE, Image.Resampling.LANCZOS)
        frame = self.plate.copy()
        frame.paste(art, (0, ART_TOP))
        label = movie.chapter(story_time).replace("Ayodhya Lights Up for Rama", "Ayodhya Lights Up for Lord Rama")
        if label:
            centered(ImageDraw.Draw(frame), label, 338, title_font(34), PAPER)
        return frame


def main():
    window = tk.Tk()
    window.title("Diwali · A Festival of Light")
    window.resizable(False, False)
    size = portrait.fit_size(min(540, max(1, window.winfo_screenwidth() - 32)),
                             min(960, max(1, window.winfo_screenheight() - 100)),
                             SIZE[0] / SIZE[1])
    screen = tk.Canvas(window, width=size[0], height=size[1], highlightthickness=0)
    screen.pack()
    image_id = screen.create_image(0, 0, anchor="nw")
    reel = Reel()
    photo = None
    current_frame = -1
    started = time.perf_counter()
    last_frame = round(DURATION * PREVIEW_FPS) - 1

    def restart(_event):
        nonlocal started
        started = time.perf_counter()

    def tick():
        nonlocal current_frame, photo
        now = time.perf_counter()
        index = min(last_frame, int((now - started) * PREVIEW_FPS))
        if index != current_frame:
            picture = reel.frame(index / PREVIEW_FPS).resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(picture, master=window)
            screen.itemconfigure(image_id, image=photo)
            current_frame = index
        spent = time.perf_counter() - now
        window.after(max(1, round(1000 * (1 / PREVIEW_FPS - spent))), tick)

    window.bind("<KeyPress-r>", restart)
    window.bind("<KeyPress-R>", restart)
    window.bind("<Escape>", lambda _event: window.destroy())
    window.after_idle(tick)
    window.mainloop()


if __name__ == "__main__":
    main()
