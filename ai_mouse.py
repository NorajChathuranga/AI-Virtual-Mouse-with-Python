import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# --- Configuration ---
wCam, hCam = 640, 480       # Camera resolution
frameR = 100                # Frame Reduction (padding) to make reaching screen edges easier
smoothening = 5             # Lower value = snappier movement
process_every_n = 2         # Process every Nth frame to reduce CPU load
click_cooldown = 0.2        # Seconds between clicks

# --- Setup ---
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cv2.setUseOptimized(True)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

pTime = 0
plocX, plocY = 0, 0         # Previous locations
clocX, clocY = 0, 0         # Current locations

mpHands = mp.solutions.hands
hands = mpHands.Hands(
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mpDraw = mp.solutions.drawing_utils
wScr, hScr = pyautogui.size() # Get actual screen size

print("Virtual Mouse Started...")
print("1. Index Finger Up: Move Cursor")
print("2. Pinch Index + Thumb: Left Click")
print("3. Pinch Middle + Thumb: Right Click")

frame_idx = 0
last_left_click = 0.0
last_right_click = 0.0

while True:
    # 1. Find hand Landmarks
    success, img = cap.read()
    if not success:
        break
    
    # Flip the image horizontally for natural interaction
    img = cv2.flip(img, 1)
    frame_idx += 1
    if frame_idx % process_every_n != 0:
        cv2.imshow("AI Mouse", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    
    # 2. Get the tip of the Index and Middle fingers
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lmList = []
            h, w, c = img.shape
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
            
            # ID 4 = Thumb Tip
            # ID 8 = Index Finger Tip
            # ID 12 = Middle Finger Tip
            if len(lmList) != 0:
                x1, y1 = lmList[8][1:]   # Index Tip
                x2, y2 = lmList[12][1:]  # Middle Tip
                x4, y4 = lmList[4][1:]   # Thumb Tip

                # 3. Check which fingers are up
                # (Simple check: is tip above the middle joint?)
                fingers = []
                # Index
                if lmList[8][2] < lmList[6][2]: fingers.append(1)
                else: fingers.append(0)
                # Middle
                if lmList[12][2] < lmList[10][2]: fingers.append(1)
                else: fingers.append(0)

                # --- MOUSE MOVEMENT (Index Finger Up) ---
                # Only move if Index is up
                if fingers[0] == 1:
                    # Convert Coordinates (Interpolation)
                    # Maps the small camera box to the full screen size
                    x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                    y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                    # Smoothen Values
                    clocX = plocX + (x3 - plocX) / smoothening
                    clocY = plocY + (y3 - plocY) / smoothening

                    # Move Mouse
                    pyautogui.moveTo(clocX, clocY)
                    plocX, plocY = clocX, clocY

                # --- LEFT CLICK (Index + Thumb Pinch) ---
                # Calculate distance between Index tip and Thumb tip
                length_L = np.hypot(x1 - x4, y1 - y4)
                
                if length_L < 30 and (time.time() - last_left_click) > click_cooldown:
                    cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()
                    last_left_click = time.time()

                # --- RIGHT CLICK (Middle + Thumb Pinch) ---
                length_R = np.hypot(x2 - x4, y2 - y4)
                if length_R < 30 and (time.time() - last_right_click) > click_cooldown:
                    cv2.circle(img, (x2, y2), 15, (0, 0, 255), cv2.FILLED)
                    pyautogui.rightClick()
                    last_right_click = time.time()

            # Draw Landmarks
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            # Draw the active movement boundary box
            cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
            (255, 0, 255), 2)

    # Frame Rate display
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

    # Show Display
    cv2.imshow("AI Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()