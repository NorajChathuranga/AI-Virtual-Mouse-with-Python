# AI Virtual Mouse (Python)

A lightweight, real-time virtual mouse that uses a webcam and hand gestures to move the cursor and perform left/right clicks.

## Features
- Smooth cursor control with jitter suppression.
- Gesture-based left click (index + thumb pinch).
- Gesture-based right click (middle + thumb pinch).
- Optimized for low-latency tracking.

## Requirements
- Python 3.8+
- Webcam

## Install
Install dependencies:

- opencv-python
- mediapipe
- pyautogui
- numpy

## Run
Open a terminal in the project folder and run:
python ai_mouse.py

## Controls
- Index finger up (middle down): Move cursor
- Pinch index + thumb: Left click
- Pinch middle + thumb: Right click
- Press `q` to quit

## Tuning Tips
If movement is too shaky or corners are hard to reach, adjust these values in [ai_mouse.py](ai_mouse.py):
- `frameR` (padding)
- `smoothening`
- `move_deadzone_px`
- `ema_alpha`
- `pinch_threshold`

## Short Description
Gesture-controlled mouse that turns your hand into a precise, low-latency pointer with click gestures.