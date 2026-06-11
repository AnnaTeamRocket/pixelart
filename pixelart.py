import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import ctypes

# Win32 Constants
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
GWL_EXSTYLE = -20

def set_click_through(hwnd, enabled=True):
    # Retrieve the extended style
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if enabled:
        style = style | WS_EX_LAYERED | WS_EX_TRANSPARENT
    else:
        style = style & ~WS_EX_TRANSPARENT
    # Apply the new style
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

class OverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Overlay Controller")
        self.root.geometry("300x550")
        
        self.overlay = None
        self.is_click_through = False
        self.mode = "Overlay"
        self.is_drag_enabled = True
        self.image_path = tk.StringVar()
        
        self.scale_val = tk.IntVar(value=1)
        self.opacity = tk.DoubleVar(value=0.7)
        
        tk.Button(root, text="Select Image", command=self.load_image).pack(pady=5)
        
        tk.Label(root, text="Scale Factor (-5 to 4):").pack()
        self.scale_slider = tk.Scale(root, from_=-5, to=4, orient="horizontal", variable=self.scale_val)
        self.scale_slider.pack()
        
        tk.Label(root, text="Opacity:").pack()
        tk.Scale(root, from_=0.1, to=1.0, resolution=0.1, orient="horizontal", 
                 variable=self.opacity, command=self.update_opacity).pack()
        
        self.mode_label = tk.Label(root, text="Current Drag Mode: Overlay")
        self.mode_label.pack(pady=5)
        tk.Button(root, text="Switch to Drag Image", command=lambda: self.set_mode("Image")).pack()
        tk.Button(root, text="Switch to Drag Overlay", command=lambda: self.set_mode("Overlay")).pack()
        
        self.lock_drag_btn = tk.Button(root, text="Dragging: Enabled", command=self.toggle_drag_lock)
        self.lock_drag_btn.pack(pady=5)
        
        self.toggle_btn = tk.Button(root, text="Enable Overlay", command=self.toggle_overlay)
        self.toggle_btn.pack(pady=5)

        self.ct_btn = tk.Button(root, text="Toggle Click-Through: OFF", command=self.toggle_ct_mode)
        self.ct_btn.pack(pady=5)

    def toggle_ct_mode(self):
        if self.overlay and self.overlay.winfo_exists():
            self.is_click_through = not self.is_click_through
            # Use the robust handle retrieval that works for you
            hwnd = ctypes.windll.user32.GetParent(self.overlay.winfo_id()) or self.overlay.winfo_id()
            set_click_through(hwnd, self.is_click_through)
            status = "ON" if self.is_click_through else "OFF"
            self.ct_btn.config(text=f"Toggle Click-Through: {status}")

    def set_mode(self, mode):
        self.mode = mode
        self.mode_label.config(text=f"Current Drag Mode: {mode}")

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg")])
        if path: self.image_path.set(path)

    def update_opacity(self, val):
        if self.overlay: self.overlay.attributes("-alpha", float(val))

    def toggle_drag_lock(self):
        self.is_drag_enabled = not self.is_drag_enabled
        status = "Enabled" if self.is_drag_enabled else "Disabled"
        self.lock_drag_btn.config(text=f"Dragging: {status}")

    def get_calculated_scale(self):
        s = self.scale_val.get()
        if s >= 1: return s
        if s <= -1: return 1 / abs(s)
        return 1

    def start_move(self, event):
        if self.is_drag_enabled:
            self.drag_data = {"x": event.x, "y": event.y}

    def do_move(self, event):
        if self.is_drag_enabled and self.overlay and self.img_label:
            if self.mode == "Overlay":
                new_x = self.overlay.winfo_x() + (event.x - self.drag_data["x"])
                new_y = self.overlay.winfo_y() + (event.y - self.drag_data["y"])
                self.overlay.geometry(f"+{new_x}+{new_y}")
            else:
                new_x = self.img_label.winfo_x() + (event.x - self.drag_data["x"])
                new_y = self.img_label.winfo_y() + (event.y - self.drag_data["y"])
                self.img_label.place(x=new_x, y=new_y)

    def toggle_overlay(self):
        if self.overlay is None or not self.overlay.winfo_exists():
            path = self.image_path.get()
            if not path: return
            
            self.overlay = tk.Toplevel(self.root)
            self.overlay.overrideredirect(True)
            self.overlay.attributes("-topmost", True)
            self.overlay.attributes("-alpha", self.opacity.get())
            self.overlay.geometry("256x256")
            
            raw_img = Image.open(path)
            scale = self.get_calculated_scale()
            w = max(1, int(raw_img.width * scale))
            h = max(1, int(raw_img.height * scale))
            
            img = raw_img.resize((w, h), Image.Resampling.NEAREST)
            self.tk_img = ImageTk.PhotoImage(img)
            
            self.container = tk.Frame(self.overlay, width=256, height=256, bg="white")
            self.container.pack(fill="both", expand=True)
            self.img_label = tk.Label(self.container, image=self.tk_img, bg="white")
            self.img_label.place(x=0, y=0)
            
            self.img_label.bind("<ButtonPress-1>", self.start_move)
            self.img_label.bind("<B1-Motion>", self.do_move)
            
            self.toggle_btn.config(text="Disable Overlay")
            self.is_click_through = False
            self.ct_btn.config(text="Toggle Click-Through: OFF")
        else:
            self.overlay.destroy()
            self.overlay = None
            self.toggle_btn.config(text="Enable Overlay")

if __name__ == "__main__":
    root = tk.Tk()
    app = OverlayApp(root)
    root.mainloop()