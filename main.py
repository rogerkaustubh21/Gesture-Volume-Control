import cv2
import mediapipe as mp
import numpy as np
import time
from math import hypot
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialising camera, hands, system audio, timer and position
cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands

hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volMin, volMax = volume.GetVolumeRange()[:2]

start = None

pos = False

while True:
    
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Finding hand
    results = hands.process(imgRGB)
    landmarks = []

    if results.multi_hand_landmarks:
        for handlandmark in results.multi_hand_landmarks:
            
            # Extract Landmark
            for id, lm in enumerate(handlandmark.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmarks.append([id, cx, cy])
                
            # Draw Landmarks
            mpDraw.draw_landmarks(img, handlandmark, mpHands.HAND_CONNECTIONS)

        if landmarks:
            # Find Thumb Tip
            x1, y1 = landmarks[4][1], landmarks[4][2]
            # Find Index Finger Tip
            x2, y2 = landmarks[8][1], landmarks[8][2]

            # Draw a circle on thumb
            cv2.circle(img, (x1, y1), 15, (255, 0, 0), cv2.FILLED)
            
            # Draw a circle on index finger
            cv2.circle(img, (x2, y2), 15, (255, 0, 0), cv2.FILLED)
            
            # Draw a line connecting the thumb and index finger
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)

            # Calculate euclidean distance between thumb and index finger
            
            length = hypot(x2 - x1, y2 - y1)
            
            # Mapping to volume range
            vol_level = np.interp(length, [15, 220], [volMin, volMax])
            
            # Setting volume accordingly
            volume.SetMasterVolumeLevel(vol_level, None)
            
            # Check if hand is in a position for 10 seconds
            if length < 15:
                if not pos:
                    pos = True
                    start = time.time()
                else:
                    if time.time() - start >= 10 :
                        final_vol = volume.GetMasterVolumeLevelScalar()
                        print(f'Final Volume: {final_vol}')
            else:
                pos = False

    # Display the image with annotations
    cv2.imshow('Image', img)

    # Break and exit when 'x' is pressed
    if cv2.waitKey(1) & 0xff == ord('x'):
        break

cap.release()
cv2.destroyAllWindows()
