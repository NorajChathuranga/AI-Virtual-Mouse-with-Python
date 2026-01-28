
# 🖱️ AI Virtual Mouse

A touch-free virtual mouse that controls your computer using hand gestures. Built with **Python**, **OpenCV**, and **MediaPipe**, this application runs efficiently in the background with a System Tray menu for easy control.

## ✨ Features

* **Hand Tracking:** Uses AI to detect hand landmarks in real-time.
* **Cursor Control:** Move your index finger to move the mouse.
* **Gestures:**
* **Left Click:** Pinch Index Finger + Thumb.
* **Right Click:** Pinch Middle Finger + Thumb.


* **System Tray Integration:** Minimizes to the taskbar (Hidden Icons).
* **Privacy Friendly:** Toggle the camera or mouse tracking on/off via the menu.
* **Portable:** Can be compiled into a single `.exe` file (no Python required).

## 🎮 Controls

| Gesture | Action |
| --- | --- |
| **Index Finger Up** | **Move Cursor** (Navigation) |
| **Pinch Index + Thumb** | **Left Click** |
| **Pinch Middle + Thumb** | **Right Click** |

> **Tip:** Keep your hand about 1–2 feet away from the webcam for best accuracy.

## 📥 How to Run (Executable Version)

If you have the `AI_Mouse.exe` file:

1. Double-click `AI_Mouse.exe`.
2. Wait 5–10 seconds for the application to initialize.
3. Look for the **Blue Dot Icon** in your System Tray (bottom right of taskbar, inside the `^` menu).
4. **Right-click** the icon to access settings:
* `Enable Mouse`: Toggle mouse control.
* `Show Camera`: Toggle the visual feedback window.
* `Quit`: Close the application.



## 🛠️ How to Run (Source Code)

If you are a developer and want to run the raw Python script:

### 1. Install Dependencies

```bash
pip install -r requirements.txt

```

### 2. Run the Script

```bash
python ai_mouse.py

```

## 🏗️ How to Build the EXE (For Developers)

To convert this Python script into a standalone `.exe` software that anyone can use:

1. Install PyInstaller:
```bash
pip install pyinstaller

```


2. Run the build command (This includes all MediaPipe data):
```bash
pyinstaller --noconsole --onefile --collect-all mediapipe --hidden-import pystray --hidden-import PIL ai_mouse.py

```


3. The final application will be located in the `dist/` folder.

## ⚙️ Configuration

You can modify the sensitivity variables at the top of `ai_mouse.py`:

* `smoothening`: Higher value = smoother cursor, but slightly more delay.
* `frameR`: The "padding" around the camera frame (increase if you can't reach the screen edges).
* `click_cooldown`: Prevents accidental double-clicks.

## 📝 License

This project is open-source. Feel free to modify and distribute.

