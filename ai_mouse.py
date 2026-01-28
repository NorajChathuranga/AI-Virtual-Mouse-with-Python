import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import threading
import pystray
from PIL import Image, ImageDraw
import sys
import ctypes
import subprocess

# --- Global Flags for Control ---
mouse_active = True
show_camera = True
app_running = True

# --- Configuration ---
wCam, hCam = 640, 480
frameR = 100
smoothening = 6
click_cooldown = 0.35
pinch_threshold = 26
pinch_release = 36
pinch_frames_required = 3
move_deadzone_px = 6
ema_alpha = 0.35

# --- Function to Create a Simple Icon (so you don't need an image file) ---
def create_icon_image():
    # Generate a 64x64 blue image with a white dot
    width = 64
    height = 64
    color1 = (0, 100, 255)
    color2 = (255, 255, 255)
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill=color2)
    return image

# --- The CV Logic (Runs in a separate thread) ---
def run_mouse_logic():
    global mouse_active, show_camera, app_running

    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    mpHands = mp.solutions.hands
    hands = mpHands.Hands(max_num_hands=1, model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mpDraw = mp.solutions.drawing_utils
    wScr, hScr = pyautogui.size()
    
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    pTime = 0
    plocX, plocY = 0, 0
    
    last_left_click = 0
    last_right_click = 0
    left_pinch_frames = 0
    right_pinch_frames = 0
    
    while app_running:
        # If camera logic is paused, sleep to save CPU
        if not mouse_active and not show_camera:
            time.sleep(0.5)
            # Ensure window is closed if paused
            try: cv2.destroyWindow("AI Mouse")
            except: pass
            continue

        success, img = cap.read()
        if not success:
            continue
            
        img = cv2.flip(img, 1)

        # Only process hand landmarks if mouse is active
        if mouse_active:
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)

            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    lmList = []
                    h, w, c = img.shape
                    for id, lm in enumerate(handLms.landmark):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        lmList.append([id, cx, cy])

                    if len(lmList) != 0:
                        x1, y1 = lmList[8][1:]
                        x2, y2 = lmList[12][1:]
                        x4, y4 = lmList[4][1:]
                        x6, y6 = lmList[6][1:]
                        x10, y10 = lmList[10][1:]

                        fingers = [0, 0]
                        if lmList[8][2] < lmList[6][2]: fingers[0] = 1
                        if lmList[12][2] < lmList[10][2]: fingers[1] = 1

                        # Move
                        if fingers[0] == 1 and fingers[1] == 0:
                            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
                            
                            targetX = plocX + (x3 - plocX) / smoothening
                            targetY = plocY + (y3 - plocY) / smoothening
                            
                            if np.hypot(targetX - plocX, targetY - plocY) >= move_deadzone_px:
                                clocX = plocX * (1 - ema_alpha) + targetX * ema_alpha
                                clocY = plocY * (1 - ema_alpha) + targetY * ema_alpha
                                pyautogui.moveTo(clocX, clocY)
                                plocX, plocY = clocX, clocY

                        # Clicks logic (Left & Right)
                        now = time.time()
                        # ... (Same pinch logic as previous code) ...
                        length_L = np.hypot(x1 - x4, y1 - y4)
                        if length_L < pinch_threshold and fingers[0] == 1: left_pinch_frames += 1
                        elif length_L > pinch_release: left_pinch_frames = 0
                        
                        if left_pinch_frames >= pinch_frames_required and (now - last_left_click) > click_cooldown:
                            cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                            pyautogui.click()
                            last_left_click = now
                            left_pinch_frames = 0
                        
                        length_R = np.hypot(x2 - x4, y2 - y4)
                        if length_R < pinch_threshold and fingers[1] == 1: right_pinch_frames += 1
                        elif length_R > pinch_release: right_pinch_frames = 0

                        if right_pinch_frames >= pinch_frames_required and (now - last_right_click) > click_cooldown:
                            cv2.circle(img, (x2, y2), 15, (0, 0, 255), cv2.FILLED)
                            pyautogui.rightClick()
                            last_right_click = now
                            right_pinch_frames = 0

                    mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
                    cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

        # Show/Hide Window Logic
        if show_camera:
            cv2.imshow("AI Mouse", img)
            cv2.waitKey(1)
        else:
            try: cv2.destroyWindow("AI Mouse")
            except: pass
            
    cap.release()
    cv2.destroyAllWindows()

# --- System Tray Menu Functions ---
def toggle_mouse(icon, item):
    global mouse_active
    mouse_active = not mouse_active

def toggle_camera(icon, item):
    global show_camera
    show_camera = not show_camera

def quit_app(icon, item):
    global app_running
    app_running = False
    icon.stop()

def uninstall_info(icon, item):
    # Standard "Uninstall" for portable exes is just deleting the file
    msg = "This is a portable application.\n\nTo uninstall, simply Quit the app and DELETE this .exe file.\n\nWould you like to open the file location now?"
    response = ctypes.windll.user32.MessageBoxW(0, msg, "Uninstall Info", 4) # 4 = Yes/No
    if response == 6: # Yes
        subprocess.Popen(f'explorer /select,"{sys.executable}"')

# --- Main Execution ---
if __name__ == "__main__":
    # Start CV Thread
    t = threading.Thread(target=run_mouse_logic)
    t.daemon = True
    t.start()

    # Start System Tray Icon
    icon = pystray.Icon("AI Mouse")
    icon.menu = pystray.Menu(
        pystray.MenuItem("Enable Mouse", toggle_mouse, checked=lambda item: mouse_active),
        pystray.MenuItem("Show Camera", toggle_camera, checked=lambda item: show_camera),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("How to Uninstall", uninstall_info),
        pystray.MenuItem("Quit", quit_app)
    )
    icon.icon = create_icon_image()
    icon.title = "AI Virtual Mouse"
    
    print("Application running in System Tray.")
    icon.run()