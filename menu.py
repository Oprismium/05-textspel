import tkinter as tk
from tkinter import messagebox

def start_game():
    messagebox.showinfo("Start Game", "The campaign begins. Steel thy resolve.")

def open_options():
    messagebox.showinfo("Options", "Here lie the lesser configurations.")

def quit_game():
    root.destroy()

# Create main window
root = tk.Tk()
root.title("Undercooked Two - This smell like poo")
root.geometry("640x480")
root.resizable(False, False)

# Title label
title = tk.Label(
    root,
    text="Undercooked Two - This smell like poo",
    font=("Times New Roman", 14, "bold")
)
title.pack(pady=20)

# Buttons
start_button = tk.Button(
    root,
    text="Start Game",
    width=20,
    command=start_game
)
start_button.pack(pady=5)

options_button = tk.Button(
    root,
    text="Options",
    width=20,
    command=open_options
)
options_button.pack(pady=5)

quit_button = tk.Button(
    root,
    text="Quit",
    width=20,
    command=quit_game
)
quit_button.pack(pady=20)

# Enter the eternal watch
root.mainloop()
