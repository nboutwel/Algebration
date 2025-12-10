import tkinter as tk
import sounddevice as sd
from sympy import preview
from vosk import Model, KaldiRecognizer
import json
import queue
import threading
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from sympy import latex
import matplotlib.pyplot as plt
from PIL import ImageTk, Image

# Voice Model
MODEL_PATH = "vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)
q = queue.Queue()
listening = False

def callback(indata, frames, time, status):
    if status:
        print(status)
    if listening:  # only queue audio while listening
        q.put(bytes(indata))

def listen_thread():
    global listening
    recognizer = KaldiRecognizer(model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while listening:
            try:
                data = q.get(timeout=0.1)
                recognizer.AcceptWaveform(data)
            except queue.Empty:
                pass

        # Once the button is released, process the final result
        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "")
        update_console(text)
        process_command(text)


# UI Initialization
root = tk.Tk()
root.title("Thing")
root.geometry("1100x800")

### Set up boundaries
# Main window
main_pane = tk.PanedWindow(root, orient="horizontal", sashwidth=5)
main_pane.pack(fill="both", expand=True)
# Menu window
window_menu = tk.Frame(main_pane, bg="lightblue", relief="ridge", borderwidth=2)
main_pane.add(window_menu, minsize=300)
# Display window
right_pane = tk.PanedWindow(main_pane, orient="vertical", sashwidth=5)
main_pane.add(right_pane, minsize=200)
window_display = tk.Frame(right_pane, bg="lightyellow", relief="ridge", borderwidth=2)
right_pane.add(window_display, minsize=200)
# Command window
window_command = tk.Frame(right_pane, bg="gray", relief="ridge", borderwidth=2)
right_pane.add(window_command, minsize=10)
# Additional Settings
right_pane.paneconfig(window_display, stretch="always")
right_pane.paneconfig(window_command, stretch="always")


def set_default_sizes():
    main_pane.sash_place(0, 150, 0)
    right_pane.sash_place(0, 0, 400)


### Setup Menu
setting_width = 50
command_title_label = tk.Label(window_menu, text="Command List:", font=('Times New Roman', 25, 'bold'))
command_title_label.pack(pady=10)
command_set_label = tk.Label(window_menu, text="* Set(expression)", font=('Times New Roman', 20, 'bold'), anchor="w", width=setting_width)
command_set_label.pack()
command_simplify_label = tk.Label(window_menu, text="* Simplify", font=('Times New Roman', 20, 'bold'), anchor="w", width=setting_width)
command_simplify_label.pack()
command_divide_label = tk.Label(window_menu, text="* Divide by #", font=('Times New Roman', 20, 'bold'), anchor="w", width=setting_width)
command_divide_label.pack()
command_multiply_label = tk.Label(window_menu, text="* Multiply by #", font=('Times New Roman', 20, 'bold'), anchor="w", width=setting_width)
command_multiply_label.pack()
command_add_label = tk.Label(window_menu, text="* Add #", font=('Times New Roman', 20, 'bold'), anchor="w", width=setting_width)
command_add_label.pack()
command_subtract_label = tk.Label(window_menu, text="* Subtract #", font=('Times New Roman', 20, 'bold'), anchor="w", width=setting_width)
command_subtract_label.pack()

### Setup Display
def render():
    global expression
    plt.figure(figsize=(0.01, 0.01))
    plt.text(0.5, 0.5, f"${latex(expression)}$", fontsize=16, ha="center", va="center")
    plt.axis("off")
    plt.savefig("eq.png", dpi=300, bbox_inches='tight', transparent=True)
    plt.close()
    return Image.open("eq.png")

expression = parse_expr("x**2 == 4", evaluate=False)
img = ImageTk.PhotoImage(render())
equation_image = tk.Label(window_display, image=img, font=('Times New Roman', 15, 'bold'))
equation_image.pack(pady=10)


def update_display():
    img = ImageTk.PhotoImage(render())
    equation_image.configure(image=img)

### Setup Command Line

def start_listening(event=None):
    global listening
    listening = True
    threading.Thread(target=listen_thread, daemon=True).start()
    print("Start!")

def stop_listening(event=None):
    print("Stop!")
    global listening
    listening = False

input_frame = tk.Frame(window_command)
input_frame.pack(fill="both", expand=True)
mic_button = tk.Button(input_frame, text="🎙️")
mic_button.pack(side="left")
mic_button.bind("<ButtonPress-1>", start_listening)
mic_button.bind("<ButtonRelease-1>", stop_listening)
entry = tk.Entry(input_frame, bg="gray20", fg="white", insertbackground="white")
entry.pack(fill="x")
display_frame = tk.Frame(window_command)
display_frame.pack(fill="both", expand=True)
display = tk.Text(display_frame, height=10, state="disabled", bg="lightgray", fg="black", wrap="word")
scrollbar = tk.Scrollbar(display_frame, orient="vertical", command=display.yview)
scrollbar.pack(side="right", fill="y")
display.pack(side="left", fill="both", expand=True)
display.config(yscrollcommand=scrollbar.set)

def convert(s):
    with open('conversions.json') as json_data:
        conversions = json.load(json_data)
        for con in conversions:
            rep = conversions.get(con)
            s = s.replace(con, rep)
    return s


def process_command(cmd):
    global expression
    cmd = convert(cmd)
    print(cmd)
    left = False
    right = False
    if cmd[-7:] == "on left":
        cmd = cmd[:-8]
        left = True
    elif cmd[-4:] == "left":
        cmd = cmd[:-5]
        left = True
    elif cmd[-8:] == "on right":
        cmd = cmd[:-9]
        right = True
    elif cmd[-5:] == "right":
        cmd = cmd[:-6]
        right = True
    if (cmd[:3] == "set"):
        print("setting!")
        arg = cmd[4:-1]
        try:
            expression = parse_expr(arg, evaluate=False)
        except:
            update_console("Invalid expression!")

    elif (cmd[:8] == "simplify"):
        print("simplifying!")
        expression = sp.simplify(expression)

    elif (cmd[:9] == "divide by" or cmd[:6] == "divide"):
        print("dividing!")
        if (cmd[:9] == "divide by"):
            arg = cmd[10:]
        else:
            arg = cmd[7:]
        try:
            fac = parse_expr(arg, evaluate=False)
            if left:
                expression = sp.Eq(expression.lhs / fac, expression.rhs)
            elif right:
                expression = sp.Eq(expression.lhs, expression.rhs / fac)
            else:
                expression = sp.Eq(expression.lhs / fac, expression.rhs / fac)
        except:
            update_console("Invalid factor!")


    elif (cmd[:11] == "multiply by" or cmd[:8] == "multiply"):
        print("multiplying!")
        if (cmd[:11] == "multiply by"):
            arg = cmd[12:]
        else:
            arg = cmd[9:]
        try:
            fac = parse_expr(arg, evaluate=False)
            if left:
                expression = sp.Eq(expression.lhs / fac, expression.rhs)
            elif right:
                expression = sp.Eq(expression.lhs, expression.rhs / fac)
            else:
                expression = sp.Eq(expression.lhs / fac, expression.rhs / fac)
        except:
            update_console("Invalid factor!")


    elif (cmd[:3] == "add"):
        print("adding!")
        arg = cmd[4:]
        try:
            fac = parse_expr(arg, evaluate=False)
            if left:
                expression = sp.Eq(expression.lhs / fac, expression.rhs)
            elif right:
                expression = sp.Eq(expression.lhs, expression.rhs / fac)
            else:
                expression = sp.Eq(expression.lhs / fac, expression.rhs / fac)
        except:
            update_console("Invalid factor!")


    elif (cmd[:8] == "subtract"):
        print("subtracting!")
        arg = cmd[9:]
        try:
            fac = parse_expr(arg, evaluate=False)
            if left:
                expression = sp.Eq(expression.lhs / fac, expression.rhs)
            elif right:
                expression = sp.Eq(expression.lhs, expression.rhs / fac)
            else:
                expression = sp.Eq(expression.lhs / fac, expression.rhs / fac)
        except:
            update_console("Invalid factor!")

    else:
        update_console("Unrecognized command!")


    update_display()


def update_console(txt):
    display.configure(state="normal")
    display.insert("end", f"> {txt}\n")
    display.configure(state="disabled")
    display.see("end")
def on_enter(event):
    user_input = entry.get()
    entry.delete(0, "end")
    update_console(user_input)
    process_command(user_input)


entry.bind("<Return>", on_enter)


### Beginning of Main loop
if __name__ == '__main__':
    root.after(100, set_default_sizes)
    root.mainloop()

