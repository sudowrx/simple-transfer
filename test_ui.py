#!/usr/bin/env python3
import tkinter as tk

root = tk.Tk()
root.title("Test UI")
root.geometry("400x200")

label = tk.Label(root, text="TEST: Status panel should work", font=("Arial", 12, "bold"), fg="red")
label.pack(pady=50)

progress_frame = tk.Frame(root, bg="#cccccc", width=200, height=20)
progress_frame.pack(pady=10)
progress_frame.pack_propagate(False)

progress_fill = tk.Frame(progress_frame, bg="red", width=100, height=20)
progress_fill.pack(side=tk.LEFT, fill=tk.Y)
progress_fill.pack_propagate(False)

speed_label = tk.Label(root, text="速度: 2.5 MB/s", font=("Arial", 10, "bold"), fg="blue")
speed_label.pack()

root.mainloop()