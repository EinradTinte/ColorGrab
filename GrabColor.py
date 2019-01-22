
# To start the virtual env
activate_this = 'D:\\Projects\\Coding\\Python\\Environments\\Tool_GrabColor\\Scripts\\activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

from PIL import ImageGrab, ImageTk, Image
import tkinter
from tkinter import font
from pynput.mouse import Listener, Button, Controller
from _thread import start_new_thread
import pyperclip

mouse = Controller()

w_screen = 1920
h_screen = 1080

w_preview = 180
h_preview = 50
offset_prev = 10

w_magn = 180
h_magn = 120
offsetX_magn = offset_prev
offsetY_magn = offset_prev + h_preview
zoom = 7
cropX = (w_magn / zoom) // 2
cropY = (h_magn / zoom) // 2

border_size = 2
border_color = 'red'


def rgb2hex(r, g, b):
    """
    Turns RGB-Color into HEX-Color
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def invertColor(hexcolor):
    table = str.maketrans('0123456789abcdef', 'fedcba9876543210')
    return '#' + hexcolor[1:].lower().translate(table).upper()


def key_left(event):
    mouse.move(-1, 0)


def key_up(event):
    mouse.move(0, -1)


def key_right(event):
    mouse.move(1, 0)


def key_down(event):
    mouse.move(0, 1)


root = tkinter.Tk()
root.config(cursor="tcross")
root.overrideredirect(1)

root.bind("<Left>", key_left)
root.bind("<Up>", key_up)
root.bind("<Right>", key_right)
root.bind("<Down>", key_down)
# root.bind("<Button>", button_click_exit_mainloop)

# capture desktop and reformat that picture
img_raw = ImageGrab.grab()
img_show = ImageTk.PhotoImage(img_raw)
# img_zoomed = img_show.resize()
img = img_raw.convert('RGBA')
img_magnifier = ImageTk.PhotoImage(img_raw.crop((- cropX, - cropY, +cropX, + cropY)).resize((w_magn, h_magn), Image.NEAREST))


canvas = tkinter.Canvas(root, width=w_screen, height=h_screen, highlightthickness=0)
canvas.pack()

widget = tkinter.Canvas(root, width=w_preview + 2 * border_size,
                        height=h_preview + h_magn + 2 * border_size, highlightthickness=0)
widget.pack()

window = canvas.create_window(0, 0, anchor='nw', window=widget)

# creating widgets
desktop = canvas.create_image(0, 0, anchor="nw", image=img_show)

border = widget.create_rectangle((border_size // 2), (border_size // 2), w_preview + (border_size + 1),
                                h_preview + h_magn + (border_size + 1), outline=border_color, width=border_size)
magnifier = widget.create_image(border_size, border_size, anchor='nw', image=img_magnifier)
pixelborder = widget.create_rectangle((border_size // 2) + (w_magn // 2), (border_size // 2) + (h_magn // 2),
                                (border_size // 2) + (w_magn // 2) + zoom + 1, (border_size // 2) + (h_magn // 2) + zoom + 1, outline='red')
preview = widget.create_rectangle(border_size, h_magn + border_size, w_preview + border_size, h_magn + h_preview + border_size, width=0)
hexcode = widget.create_text(w_preview // 2, h_magn + (h_preview // 2), font=font.Font(size=-(h_preview // 2)))


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
    try:
        rgba = img.getpixel((x, y))
    except:
        print((x, y))
    color = rgb2hex(rgba[0], rgba[1], rgba[2])

    if (y - (offset_prev + h_preview + h_magn)) > 0:
        canvas.itemconfig(window, anchor='sw')
    else:
        canvas.itemconfig(window, anchor='nw')
    # TODO: offset widgets when out of screen

    # reposition widgets
    # canvas.coords(preview, (x + offset_prev, y - offset_prev * yinv, x + (w_preview + offset_prev), y - (h_preview + offset_prev) * yinv))
    # canvas.coords(magnifier, (x + offsetX_magn, y - offsetY_magn * yinv))
    # prevcoords = canvas.coords(preview)
    # canvas.coords(hexcode, (prevcoords[0] + w_preview // 2, prevcoords[1] + h_preview // 2))
    # widget.config(offset="{:},{:}".format(x + offset_prev, y - offset_prev * yinv))
    canvas.coords(window, (x + offset_prev, y + offset_prev))

    # changes values
    widget.itemconfig(magnifier, image=img_magnifier)
    widget.itemconfig(preview, fill=color)
    widget.itemconfig(hexcode, fill=invertColor(color), text=color)


def helper():
    with Listener(on_move=on_move, on_click=on_click) as listener:
        listener.join()


start_new_thread(helper, ())
root.mainloop()
