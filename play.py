"""Play the portrait edition of A Festival of Light."""

from functools import lru_cache
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageTk

import diwali_ramayana_movie as movie
import diwali_ramayana_record_v3 as portrait


SIZE = (1080, 1920)
DURATION = portrait.DURATION
PREVIEW_FPS = 30
ART_TOP = 396
ART_SIZE = (SIZE[0], round(portrait.H * SIZE[0] / portrait.W))
INK = (4, 6, 12)
GOLD = (245, 199, 121)
PAPER = (237, 230, 216)


@lru_cache(maxsize=None)
def title_font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", size)
    except OSError:
        return movie.mono(size)


def centered(draw, text, y, font, fill):
    draw.text((SIZE[0] // 2, y), text, font=font, fill=fill, anchor="mt",
              stroke_width=2, stroke_fill=INK)


class Reel:
    def __init__(self):
        self.scene = portrait.Ramayana()
        self.plate = Image.new("RGB", SIZE, INK)
        draw = ImageDraw.Draw(self.plate)
        centered(draw, "D I W A L I", 214, movie.mono(30), GOLD)
        centered(draw, "A Festival of Light", 254, title_font(58), GOLD)

    def frame(self, time):
        art = self.scene.frame(time).resize(ART_SIZE, Image.Resampling.LANCZOS)
        frame = self.plate.copy()
        frame.paste(art, (0, ART_TOP))
        label = movie.chapter(time).replace("Ayodhya Lights Up for Rama", "Ayodhya Lights Up for Lord Rama")
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
