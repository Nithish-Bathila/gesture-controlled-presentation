"""
Main Entry Point
Gesture detection with system tray integration.
Show/Hide Preview and About menu items.
"""
import os
import sys
import threading
import time
import cv2
import pystray
from pystray import MenuItem as item
from gesture_detector import GestureDetector
import controller
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


running = True
show_preview_window = False
gesture_detector = GestureDetector()
cap = None  # Global VideoCapture

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def gesture_loop():
    """
    Background gesture detection loop.
    """
    global running, cap, show_preview_window

    while running:
        if cap is None:
            time.sleep(0.1)
            continue

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        # Detect gesture
        gesture = gesture_detector.detect_gesture(frame)

        if controller.is_powerpoint_open():
            if gesture == 'start_slideshow':
                controller.start_slideshow()
            elif gesture == 'end_slideshow':
                controller.end_slideshow()
            elif gesture == 'next_slide':
                controller.next_slide()
            elif gesture == 'prev_slide':
                controller.prev_slide()

        # Show preview if enabled
        if show_preview_window:
            cv2.namedWindow("Gesture Control Preview", cv2.WINDOW_NORMAL)
            cv2.imshow("Gesture Control Preview", frame)
            # Check if window was closed using the close button
            if cv2.getWindowProperty("Gesture Control Preview", cv2.WND_PROP_VISIBLE) < 1:
                hide_camera_preview()
        else:
            cv2.destroyAllWindows()

        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()

def show_camera_preview(icon, item):
    """
    Enables preview window flag.
    """
    global show_preview_window
    show_preview_window = True
    update_tray_menu(icon)

def hide_camera_preview(icon=None, item=None):
    """
    Disables preview window flag.
    """
    global show_preview_window
    show_preview_window = False
    update_tray_menu(icon)

def show_about():
    """
    Shows About window.
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("About Gesture Control",
                        "Gesture-Controlled PowerPoint Navigation\n"
                        "Version 1.7\n\n"
                        "Developed by Nithish\n"
                        "Uses OpenCV, MediaPipe, pywin32, pystray")
    root.destroy()

def quit_app(icon, item):
    """
    Exit callback.
    """
    global running
    running = False
    icon.stop()

def update_tray_menu(icon):
    """
    Updates tray menu to toggle Show/Hide Preview option dynamically.
    """
    menu = (
        item('Hide Preview', lambda: hide_camera_preview(icon)) if show_preview_window else
        item('Show Preview', lambda: show_camera_preview(icon, None)),
        item('Gesture Reference', lambda: threading.Thread(target=show_gesture_reference, daemon=True).start()),
        item('About', lambda: threading.Thread(target=show_about, daemon=True).start()),
        item('Exit', quit_app)
    )
    icon.menu = pystray.Menu(*menu)
    icon.update_menu()


def show_gesture_reference():
    window = tk.Tk()
    window.title("Gesture Reference")
    window.resizable(False, False)  # Make window non-resizable

    img = Image.open(resource_path("gestures.png"))
    tk_img = ImageTk.PhotoImage(img)

    label = tk.Label(window, image=tk_img)
    label.image = tk_img  # Keep reference
    label.pack()

    window.mainloop()


def setup_tray():
    """
    Initializes system tray icon and menu.
    """
    icon_image = Image.open(resource_path('icon.png'))
    icon = pystray.Icon("GestureControl", icon_image, "Gesture Control")

    # Initial menu setup
    update_tray_menu(icon)

    icon.run()


def main():
    """
    Starts VideoCapture, gesture detection thread, and tray icon.
    """
    global cap
    cap = cv2.VideoCapture(0)

    gesture_thread = threading.Thread(target=gesture_loop, daemon=True)
    gesture_thread.start()

    setup_tray()

if __name__ == "__main__":
    main()