
# To start the virtual env
activate_this = 'D:\\Projects\\Coding\\Python\\Environments\\Tool_GrabColor\\Scripts\\activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

from PIL import ImageGrab, ImageTk, Image
import tkinter
from tkinter import font
from pynput.mouse import Listener, Button, Controller
from _thread import start_new_thread
import pyperclip

"""
    Takes a screenshot from your desktop and lets you grab the hexcode of selected color to store in clipboard.

    The widget displays the currently selected color as well as its hexcode and a magnifier for better selection.

    --- Controls ---

    - Move Cursor:
        Move cursor to select pixel(s).
    - Left Click:
        Save currently displayed hexcode to clipboard and terminate program.
    - Right Click:
        Change sample size of pixels to determine selected color.
        (At the current version this simply takes the average color of all pixels.)
    - Scroll:
        Increase/Decrease magnification.
    - Arrow Keys:
        Move cursor 1 pixel in respective direction
"""

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

cursor_sizes = [1, 3, 5, 7]
cursor_size = 0


def rgb2hex(r, g, b):
    """
    Turns RGB-Color into HEX-Color
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def hex2rgb(hex):
    return tuple(int(hex[i:i + 2], 16) for i in (1, 3, 5))


def invertColor(hexcolor):
    table = str.maketrans('0123456789abcdef', 'fedcba9876543210')
    return '#' + hexcolor[1:].lower().translate(table).upper()


def getBrightness(r, g, b):
    return ((r * 299) + (g * 587) + (b * 114)) / 1000


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
# img = img_raw.convert('RGBA')
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


def mergeColors(colors):
    """ Returns the average of a rgb list. """
    r = sum(i for i, h, j in colors) // len(colors)
    g = sum(h for i, h, j in colors) // len(colors)
    b = sum(j for i, h, j in colors) // len(colors)
    return tuple((r, g, b))


def getColor(x, y):
    """ Returns the hex color under the cursor position. Takes sample size into account. """
    colors = []
    hlp = cursor_sizes[cursor_size] // 2
    for i in range(cursor_sizes[cursor_size]):
        for j in range(cursor_sizes[cursor_size]):
            if 0 <= x < borders[0] and 0 <= y < borders[1]:
                colors.append(img_raw.getpixel((x - hlp + i, y - hlp + j)))
    return rgb2hex(*mergeColors(colors))


def on_click(x, y, button, pressed):
    """
    On left click copies hexcode to clipboard and closes program.
    On right click changes the sample size.
    """
    if button == Button.left and pressed:
        pyperclip.copy(widget.itemcget(hexcode, 'text'))
        root.destroy()
    if button == Button.right and pressed:
        global cursor_size
        cursor_size += 1
        if cursor_size >= len(cursor_sizes):
            cursor_size = 0
        hlp = cursor_sizes[cursor_size] // 2
        # resize pixelborder
        widget.coords(pixelborder, ((border_size // 2) + (w_magn // 2) - (zoom * hlp), (border_size // 2) + (h_magn // 2) - (zoom * hlp),
                    (border_size // 2) + (w_magn // 2) + (zoom * (hlp + 1)) + 1, (border_size // 2) + (h_magn // 2) + (zoom * (hlp + 1)) + 1))
        # updates widget
        on_move(x, y)


def on_scroll(x, y, dx, dy):
    """ Scroll to zoom. """
    global zoom, max_zoom, cropX, cropY

    if dy < 0 and zoom > 2:
        zoom -= 1
    if dy > 0 and zoom < max_zoom:
        zoom += 1

    # update everything zoom affects
    cropX = (w_magn / zoom) // 2
    cropY = (h_magn / zoom) // 2
    # updates widget
    on_move(x, y)
    hlp = cursor_sizes[cursor_size] // 2
    widget.coords(pixelborder, ((border_size // 2) + (w_magn // 2) - (zoom * hlp), (border_size // 2) + (h_magn // 2) - (zoom * hlp),
                (border_size // 2) + (w_magn // 2) + (zoom * (hlp + 1)) + 1, (border_size // 2) + (h_magn // 2) + (zoom * (hlp + 1)) + 1))
    


def on_move(x, y):
    """
    Updates the widget and moves it along with cursor.
    """
    global img_magnifier
    # to keep from crashing when cursor is out of bounds, position has to be checked
    if 0 <= x < borders[0] and 0 <= y < borders[1]:
        # cropping and magnifing image
        new_img_magnifier = ImageTk.PhotoImage(img_raw.crop((x - cropX, y - cropY, x + cropX, y + cropY)).resize((w_magn, h_magn), Image.NEAREST))

        # get color under cursor
        color = getColor(x, y)

        if (y + (offset_prev + h_preview + h_magn)) > borders[1]:
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
        widget.itemconfig(magnifier, image=new_img_magnifier)
        img_magnifier = new_img_magnifier
        widget.itemconfig(preview, fill=color)
        # adjusts text color to preview color brightness
        if getBrightness(*hex2rgb(color)) > 123:
            textcolor = 'black'
        else:
            textcolor = 'white'
        widget.itemconfig(hexcode, fill=textcolor, text=color)


# listener and mainloop() can't be run in same thread
def helper():
    with Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()


start_new_thread(helper, ())
root.after(1, mouse.move, 0, 1)  # to correctly place widget right from the start
root.mainloop()
