
# To start the virtual env
activate_this = 'D:\\Projects\\Coding\\Python\\Environments\\Tool_GrabColor\\Scripts\\activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

from PIL import ImageGrab, ImageTk, Image
import tkinter
from tkinter import font
from pynput.mouse import Listener, Button
from _thread import start_new_thread
import pyperclip

w_screen = 1920
h_screen = 1080

w_preview = 180
h_preview = 50
offset_prev = 10

w_magn = 180
h_magn = 120
offsetX_magn = offset_prev
offsetY_magn = offset_prev + h_preview
zoom = 6
cropX = (w_magn / zoom) // 2
cropY = (h_magn / zoom) // 2


def rgb2hex(r, g, b):
    """
    Turns RGB-Color into HEX-Color
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def invertColor(hexcolor):
    table = str.maketrans('0123456789abcdef', 'fedcba9876543210')
    return '#' + hexcolor[1:].lower().translate(table).upper()


root = tkinter.Tk()
root.config(cursor="tcross")
root.overrideredirect(1)
# root.bind("<Button>", button_click_exit_mainloop)

# capture desktop and reformat that picture
img_raw = ImageGrab.grab()
img_show = ImageTk.PhotoImage(img_raw)
# img_zoomed = img_show.resize()
img = img_raw.convert('RGBA')
img_magnifier = ImageTk.PhotoImage(img_raw.crop((- cropX, - cropY, +cropX, + cropY)).resize((w_magn, h_magn), Image.NEAREST))


canvas = tkinter.Canvas(root, width=w_screen, height=h_screen, highlightthickness=0)
canvas.pack()

# creating widgets
desktop = canvas.create_image(0, 0, anchor="nw", image=img_show)
magnifier = canvas.create_image(100, 100, anchor='sw', image=img_magnifier)
preview = canvas.create_rectangle(0, 0, w_preview, h_preview)
hexcode = canvas.create_text(w_preview // 2, h_preview // 2, font=font.Font(size=-(h_preview // 2)))


def on_click(x, y, button, pressed):
    # copy hexcode to clipboard and close program
    if button == Button.left and pressed:
        pyperclip.copy(canvas.itemcget(hexcode, 'text'))
        root.destroy()


def on_move(x, y):
    # cropping and magnifing image
    global img_magnifier  # otherwise img_magnifier is a local variable and gets garbage collected
    img_magnifier = ImageTk.PhotoImage(img_raw.crop((x - cropX, y - cropY, x + cropX, y + cropY)).resize((w_magn, h_magn), Image.NEAREST))

    # get color under cursor
    rgba = img.getpixel((x, y))
    color = rgb2hex(rgba[0], rgba[1], rgba[2])

    if (y - (offset_prev + h_preview + h_magn)) < 0:
        yinv = -1
    else:
        yinv = 1
    # TODO: offset widgets when out of screen

    # reposition widgets
    canvas.coords(preview, (x + offset_prev, y - offset_prev * yinv, x + (w_preview + offset_prev), y - (h_preview + offset_prev) * yinv))
    canvas.coords(magnifier, (x + offsetX_magn, y - offsetY_magn * yinv))
    prevcoords = canvas.coords(preview)
    canvas.coords(hexcode, (prevcoords[0] + w_preview // 2, prevcoords[1] + h_preview // 2))

    # changes values
    canvas.itemconfig(magnifier, image=img_magnifier)
    canvas.itemconfig(preview, fill=color)
    canvas.itemconfig(hexcode, fill=invertColor(color), text=color)


def helper():
    with Listener(on_move=on_move, on_click=on_click) as listener:
        listener.join()


start_new_thread(helper, ())
root.mainloop()
