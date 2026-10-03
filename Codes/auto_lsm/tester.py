import tkinter as tk
from tkinter import ttk, messagebox

def submit():
    messagebox.showinfo("Submitted", f"Wavelength: {wl_entry.get()} nm")

root = tk.Tk()
root.title("Parameter Entry")
root.geometry("320x200")

ttk.Label(root, text="Wavelength (nm):").pack(pady=5)
wl_entry = ttk.Entry(root)
wl_entry.insert(0, "1550")
wl_entry.pack()

ttk.Button(root, text="Save & Run", command=submit).pack(pady=20)

root.mainloop()