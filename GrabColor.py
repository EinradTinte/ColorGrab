
# To start the virtual env
activate_this = 'D:\\Projects\\Coding\\Python\\Environments\\Tool_GrabColor\\Scripts\\activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

from PIL import ImageGrab, ImageTk, Image
import tkinter
from tkinter import font
from pynput.mouse import Listener, Button, Controller
from _thread import start_new_thread
import pyperclip

# TODO: multi monitor support
# FIXME: pynput seems to fail when tskmangr (or sth alike?) has the focus

mouse = Controller()

# color preview
w_preview = 180
h_preview = 50

offset_prev = 10  # widget offset from cursor

# magnifier window
w_magn = 180
h_magn = 120
offsetX_magn = offset_prev
offsetY_magn = offset_prev + h_preview
zoom = 6
max_zoom = 12
# image scope that gets magnified
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
root.overrideredirect(1)  # makes window fullscreen and on top

root.bind("<Left>", key_left)
root.bind("<Up>", key_up)
root.bind("<Right>", key_right)
root.bind("<Down>", key_down)

# capture desktop and reformat that picture
img_raw = ImageGrab.grab()
img_show = ImageTk.PhotoImage(img_raw)
img = img_raw.convert('RGBA')
img_magnifier = ImageTk.PhotoImage(img_raw.crop((- cropX, - cropY, +cropX, + cropY)).resize((w_magn, h_magn), Image.NEAREST))
borders = img_raw.size

canvas = tkinter.Canvas(root, width=borders[0], height=borders[1], highlightthickness=0)
canvas.pack()

widget = tkinter.Canvas(root, width=w_preview + 2 * border_size,
                        height=h_preview + h_magn + 2 * border_size, highlightthickness=0)
widget.pack()

window = canvas.create_window(0, 0, anchor='nw', window=widget)

# screenshot to maneuver over
desktop = canvas.create_image(0, 0, anchor="nw", image=img_show)
# red border around widget
border = widget.create_rectangle((border_size // 2), (border_size // 2), w_preview + (border_size + 1),
            h_preview + h_magn + (border_size + 1), outline=border_color, width=border_size)
# zooms into cursor position
magnifier = widget.create_image(border_size, border_size, anchor='nw', image=img_magnifier)
# marks pixel under cursor
pixelborder = widget.create_rectangle((border_size // 2) + (w_magn // 2), (border_size // 2) + (h_magn // 2),
            (border_size // 2) + (w_magn // 2) + zoom + 1, (border_size // 2) + (h_magn // 2) + zoom + 1, outline='red')
# shows a preview of the choosen color
preview = widget.create_rectangle(border_size, h_magn + border_size, w_preview + border_size, h_magn + h_preview + border_size, width=0)
# displays hexcode of choosen color in preview window
hexcode = widget.create_text(w_preview // 2, h_magn + (h_preview // 2), font=font.Font(size=-(h_preview // 2)))


def on_click(x, y, button, pressed):
    """ On left click copies hexcode to clipboard and closes program. """
    if button == Button.left and pressed:
        pyperclip.copy(canvas.itemcget(hexcode, 'text'))
        root.destroy()


def on_scroll(x, y, dx, dy):
    """ Scroll to zoom """
    global zoom, max_zoom, cropX, cropY

    if dy < 0 and zoom > 2:
        zoom -= 1
    if dy > 0 and zoom < max_zoom:
        zoom += 1

    # update everything zoom affects
    cropX = (w_magn / zoom) // 2
    cropY = (h_magn / zoom) // 2
    on_move(x, y)  # updates screen
    widget.coords(pixelborder, ((border_size // 2) + (w_magn // 2), (border_size // 2) + (h_magn // 2),
                (border_size // 2) + (w_magn // 2) + zoom + 1, (border_size // 2) + (h_magn // 2) + zoom + 1))


def on_move(x, y):
    """
    Updates the widget and moves it along with cursor.
    """
    global borders, img_magnifier
    # to keep from crashing when cursor is out of bounds, position has to be checked
    if x >= 0 and x < borders[0] and y >= 0 and y < borders[1]:
        # cropping and magnifing image
        img_magnifier = ImageTk.PhotoImage(img_raw.crop((x - cropX, y - cropY, x + cropX, y + cropY)).resize((w_magn, h_magn), Image.NEAREST))

        # get color under cursor
        rgba = img.getpixel((x, y))
        color = rgb2hex(rgba[0], rgba[1], rgba[2])

        if (y - (offset_prev + h_preview + h_magn)) > 0:
            ns = 's'
            yinv = -1
        else:
            ns = 'n'
            yinv = 1
        if (x + (offset_prev + h_preview + h_magn)) > borders[0]:
            we = 'e'
            xinv = -1
        else:
            we = 'w'
            xinv = 1

        # repositions widget if not fully visible
        canvas.itemconfig(window, anchor=ns + we)
        canvas.coords(window, (x + offset_prev * xinv, y + offset_prev * yinv))

        # changes values
        widget.itemconfig(magnifier, image=img_magnifier)
        widget.itemconfig(preview, fill=color)
        widget.itemconfig(hexcode, fill=invertColor(color), text=color)


# listener and mainloop() can't be run in same thread
def helper():
    with Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()


start_new_thread(helper, ())
root.after(1, mouse.move, 0, 1)  # to correctly place widget right from the start
root.mainloop()
