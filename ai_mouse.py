import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# --- Configuration ---
wCam, hCam = 640, 480       # Camera resolution
frameR = 60                 # Frame Reduction (padding)
smoothening = 6             # Lower value = snappier, Higher = smoother
process_every_n = 1         # Set to 1 for smoothest tracking, 2+ for better performance
click_cooldown = 0.35       # Seconds between clicks
pinch_threshold = 26        # Lower = harder to click (pixels)
pinch_release = 36          # Hysteresis release threshold
pinch_frames_required = 3   # Stable frames needed before click
min_pinch_interval = 0.25   # Minimum seconds between pinch checks
move_deadzone_px = 6        # Ignore tiny hand shakes (pixels)
ema_alpha = 0.35            # Exponential smoothing factor (0-1)

# --- Setup ---
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Low latency buffer
cv2.setUseOptimized(True)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False  # Set to True if you want corner-safe-stop

pTime = 0
plocX, plocY = 0, 0         # Previous locations
clocX, clocY = 0, 0         # Current locations

mpHands = mp.solutions.hands
hands = mpHands.Hands(
    max_num_hands=1,
    model_complexity=0,     # 0 = Lite (Fast), 1 = Full (Accurate)
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mpDraw = mp.solutions.drawing_utils
wScr, hScr = pyautogui.size()

print("Virtual Mouse Started...")
print("1. Index Finger Up: Move Cursor")
print("2. Pinch Index + Thumb: Left Click")
print("3. Pinch Middle + Thumb: Right Click")
print("Press 'q' to exit.")

frame_idx = 0
last_left_click = 0.0
last_right_click = 0.0
left_pinch_frames = 0
right_pinch_frames = 0
last_pinch_check = 0.0

while True:
    success, img = cap.read()
    if not success:
        break
    
    img = cv2.flip(img, 1)
    frame_idx += 1

    # Skip processing for performance (if process_every_n > 1)
    if frame_idx % process_every_n != 0:
        cv2.imshow("AI Mouse", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

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
                x1, y1 = lmList[8][1:]   # Index Tip
                x2, y2 = lmList[12][1:]  # Middle Tip
                x4, y4 = lmList[4][1:]   # Thumb Tip
                x6, y6 = lmList[6][1:]   # Index PIP
                x10, y10 = lmList[10][1:] # Middle PIP

                # Check Fingers Up
                fingers = []
                # Index (8) above PIP (6)
                if lmList[8][2] < lmList[6][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
                # Middle (12) above PIP (10)
                if lmList[12][2] < lmList[10][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
                
                # --- MOUSE MOVEMENT (Index Up) ---
                if fingers[0] == 1 and fingers[1] == 0:
                    # Interpolate coordinates
                    x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                    y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                    # Smoothen (EMA + deadzone)
                    targetX = plocX + (x3 - plocX) / smoothening
                    targetY = plocY + (y3 - plocY) / smoothening
                    dist = np.hypot(targetX - plocX, targetY - plocY)
                    if dist >= move_deadzone_px:
                        clocX = plocX * (1 - ema_alpha) + targetX * ema_alpha
                        clocY = plocY * (1 - ema_alpha) + targetY * ema_alpha
                        pyautogui.moveTo(clocX, clocY)
                        plocX, plocY = clocX, clocY

                # --- CLICKS (Distance Check with stability & hysteresis) ---
                now = time.time()
                if (now - last_pinch_check) > min_pinch_interval:
                    last_pinch_check = now

                    # Left Click (Index + Thumb)
                    length_L = np.hypot(x1 - x4, y1 - y4)
                    if length_L < pinch_threshold and fingers[0] == 1 and fingers[1] == 0:
                        left_pinch_frames += 1
                    elif length_L > pinch_release:
                        left_pinch_frames = 0

                    if left_pinch_frames >= pinch_frames_required and (now - last_left_click) > click_cooldown:
                        cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                        pyautogui.click()
                        last_left_click = now
                        left_pinch_frames = 0

                    # Right Click (Middle + Thumb)
                    length_R = np.hypot(x2 - x4, y2 - y4)
                    if length_R < pinch_threshold and fingers[1] == 1 and fingers[0] == 0:
                        right_pinch_frames += 1
                    elif length_R > pinch_release:
                        right_pinch_frames = 0

                    if right_pinch_frames >= pinch_frames_required and (now - last_right_click) > click_cooldown:
                        cv2.circle(img, (x2, y2), 15, (0, 0, 255), cv2.FILLED)
                        pyautogui.rightClick()
                        last_right_click = now
                        right_pinch_frames = 0

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
            cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

    # Calculate FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime
    cv2.putText(img, f"FPS: {int(fps)}", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    cv2.imshow("AI Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()