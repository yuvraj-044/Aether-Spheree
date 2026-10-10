#!/usr/bin/env python3
"""
Aether Sphere — Real-Time 3D Particle Sphere with MediaPipe Hand Tracking
Supports both:
1. Web Mode (Default): Runs a local high-performance server and launches the responsive 3D WebGL app.
2. Native Python Mode (--native): Runs an OpenCV + MediaPipe 3D particle simulation directly in a Python desktop window.
"""

import sys
import os
import math
import time
import argparse
import urllib.request
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

def ensure_model_file():
    if not os.path.exists(MODEL_PATH):
        print(f"[+] Downloading MediaPipe hand_landmarker model to {MODEL_PATH}...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("[+] Model downloaded successfully.")
        except Exception as e:
            print(f"[!] Warning: Could not download model: {e}")

def run_web_server(port=8080):
    """
    Spins up a lightweight local HTTP server to satisfy browser webcam security restrictions.
    Automatically launches the user's default web browser.
    """
    os.chdir(BASE_DIR)
    
    class CustomHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} -> {args[1]}\n")

    server_address = ('127.0.0.1', port)
    try:
        httpd = HTTPServer(server_address, CustomHandler)
    except OSError:
        port = 8888
        server_address = ('127.0.0.1', port)
        httpd = HTTPServer(server_address, CustomHandler)

    url = f"http://127.0.0.1:{port}/index1.html"
    print("\n" + "=" * 60)
    print(" 🔮 AETHER SPHERE — 3D PARTICLE GESTURE RUNNER")
    print("=" * 60)
    print(f" • Local Web URL : {url}")
    print(" • Features      : 3,000 Particles, MediaPipe Hands, Smooth Lerp")
    print(" • Hand Controls : Single hand move/rot, Pinch explode, 2-Hand scale, Finger colors")
    print("=" * 60)
    print(" Opening browser now... (Press Ctrl+C to stop server)\n")

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped by user.")
        httpd.server_close()

def run_native_python_sphere():
    """
    Standalone Native Python 3D Particle Sphere using OpenCV and MediaPipe (Tasks / Solutions).
    Renders 3,000 3D particles projected onto the webcam feed in real-time.
    """
    try:
        import cv2
        import numpy as np
        import mediapipe as mp
        
    except ImportError:
        print("\n[!] Native Python mode requires 'opencv-python' and 'mediapipe'.")
        print("    Install them using: pip install -r requirements.txt")
        print("    Or launch the WebGL application directly: python3 app.py\n")
        sys.exit(1)

    print("\n[+] Initializing Native Python 3D Particle Engine with MediaPipe Hands...")

    detector_type = "none"
    detector = None

    # Check whether mediapipe has legacy solutions or new tasks API
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
        detector_type = "legacy"
        mp_hands = mp.solutions.hands
        detector = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55
        )
    else:
        # Use MediaPipe 1.x tasks API
        try:
            ensure_model_file()
            BaseOptions = mp.tasks.BaseOptions
            HandLandmarker = mp.tasks.vision.HandLandmarker
            HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode

            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=VisionRunningMode.IMAGE,
                num_hands=2
            )
            detector = HandLandmarker.create_from_options(options)
            detector_type = "tasks"
        except Exception as e:
            print(f"[!] Notice: MediaPipe Tasks init notice: {e}")
            detector_type = "none"

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Error: Could not access webcam. Falling back to Web mode.")
        run_web_server()
        return

    # Generate 3,000 3D Sphere Particles (Fibonacci lattice)
    PARTICLE_COUNT = 3000
    SPHERE_RADIUS = 160.0
    phi_ratio = math.pi * (3.0 - math.sqrt(5.0))
    
    home_particles = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)
    velocities = np.zeros((PARTICLE_COUNT, 3), dtype=np.float32)

    for i in range(PARTICLE_COUNT):
        y = 1.0 - (i / float(PARTICLE_COUNT - 1)) * 2.0
        radius_at_y = math.sqrt(max(0.0, 1.0 - y * y))
        theta = phi_ratio * i
        
        home_particles[i, 0] = math.cos(theta) * radius_at_y * SPHERE_RADIUS
        home_particles[i, 1] = y * SPHERE_RADIUS
        home_particles[i, 2] = math.sin(theta) * radius_at_y * SPHERE_RADIUS

    current_particles = np.copy(home_particles)

    # State variables
    sphere_center = np.array([320.0, 240.0, 0.0], dtype=np.float32)
    target_center = np.array([320.0, 240.0, 0.0], dtype=np.float32)
    rot_x, rot_y = 0.0, 0.0
    target_rot_x, target_rot_y = 0.0, 0.0
    sphere_scale = 1.0
    target_scale = 1.0
    
    charge_level = 0.0
    is_pinching = False
    is_exploded = False
    explosion_time = 0

    PALETTE = [
        (86, 30, 255),    # 0: Crimson
        (255, 240, 0),    # 1: Cyan
        (136, 255, 0),    # 2: Emerald
        (3, 183, 255),    # 3: Amber
        (255, 0, 170),    # 4: Violet
        (250, 245, 240)   # 5: Aurora Diamond
    ]
    current_color = np.array([255.0, 240.0, 0.0], dtype=np.float32)
    target_color = np.array([255.0, 240.0, 0.0], dtype=np.float32)

    show_backdrop = True
    prev_time = time.time()

    cv2.namedWindow("Aether Sphere — Native Python", cv2.WINDOW_NORMAL)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()
        dt = min(0.05, now - prev_time)
        prev_time = now

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        extracted_hands = []

        if detector_type == "legacy" and detector:
            results = detector.process(rgb_frame)
            if results.multi_hand_landmarks:
                for hand in results.multi_hand_landmarks:
                    extracted_hands.append([(lm.x, lm.y) for lm in hand.landmark])
        elif detector_type == "tasks" and detector:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = detector.detect(mp_image)
            if detection_result.hand_landmarks:
                for hand in detection_result.hand_landmarks:
                    extracted_hands.append([(lm.x, lm.y) for lm in hand])

        hand_count = len(extracted_hands)

        if hand_count == 1:
            hand = extracted_hands[0]
            cx = sum(p[0] for p in hand) / len(hand)
            cy = sum(p[1] for p in hand) / len(hand)
            target_center[0] = cx * w
            target_center[1] = cy * h

            target_rot_y = (cx - 0.5) * math.pi * 1.5
            target_rot_x = (cy - 0.5) * math.pi * 1.5

            # Pinch (Thumb 4, Index 8)
            t_pt = hand[4]
            i_pt = hand[8]
            p_dist = math.sqrt((t_pt[0] - i_pt[0])**2 + (t_pt[1] - i_pt[1])**2)

            if p_dist < 0.06:
                is_pinching = True
                charge_level = min(1.0, charge_level + dt * 1.5)
            else:
                if is_pinching and charge_level >= 0.8:
                    is_exploded = True
                    explosion_time = now
                    velocities = (np.random.rand(PARTICLE_COUNT, 3).astype(np.float32) - 0.5) * 550.0
                is_pinching = False
                charge_level = max(0.0, charge_level - dt * 2.0)

            # Finger count
            wrist = hand[0]
            extended = 0
            for tip_idx, pip_idx in [(8, 6), (12, 10), (16, 14), (20, 18)]:
                d_tip = math.sqrt((hand[tip_idx][0] - wrist[0])**2 + (hand[tip_idx][1] - wrist[1])**2)
                d_pip = math.sqrt((hand[pip_idx][0] - wrist[0])**2 + (hand[pip_idx][1] - wrist[1])**2)
                if d_tip > d_pip * 1.15:
                    extended += 1
            
            # Thumb
            d_th = math.sqrt((hand[4][0] - hand[17][0])**2 + (hand[4][1] - hand[17][1])**2)
            d_ip = math.sqrt((hand[3][0] - hand[17][0])**2 + (hand[3][1] - hand[17][1])**2)
            if d_th > d_ip * 1.12:
                extended += 1

            extended = min(5, max(0, extended))
            target_color = np.array(PALETTE[extended], dtype=np.float32)

        elif hand_count >= 2:
            h1 = extracted_hands[0]
            h2 = extracted_hands[1]
            c1x = sum(p[0] for p in h1) / len(h1) * w
            c1y = sum(p[1] for p in h1) / len(h1) * h
            c2x = sum(p[0] for p in h2) / len(h2) * w
            c2y = sum(p[1] for p in h2) / len(h2) * h

            h_dist = math.sqrt((c1x - c2x)**2 + (c1y - c2y)**2)
            target_scale = max(0.4, min(3.0, h_dist / 220.0))
            target_center[0] = (c1x + c2x) / 2.0
            target_center[1] = (c1y + c2y) / 2.0

        # Exponential Smoothing
        sphere_center += (target_center - sphere_center) * 0.1
        sphere_scale += (target_scale - sphere_scale) * 0.1
        rot_x += (target_rot_x - rot_x) * 0.1
        rot_y += (target_rot_y - rot_y) * 0.1
        current_color += (target_color - current_color) * 0.08

        # Output Canvas
        if show_backdrop:
            canvas = (frame * 0.35).astype(np.uint8)
        else:
            canvas = np.zeros((h, w, 3), dtype=np.uint8)

        # 3D Rotation Matrix
        cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)
        cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
        Rx = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]], dtype=np.float32)
        Ry = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]], dtype=np.float32)
        R = np.dot(Ry, Rx)

        color_bgr = tuple(map(int, current_color))

        if is_exploded:
            current_particles += velocities * dt
            velocities *= 0.94
            current_particles += (home_particles * sphere_scale - current_particles) * 0.06
            if now - explosion_time > 1.8:
                is_exploded = False
        elif charge_level > 0.05:
            jitter = (np.random.rand(PARTICLE_COUNT, 3).astype(np.float32) - 0.5) * (charge_level**2 * 18.0)
            target_pts = home_particles * sphere_scale * (1.0 - charge_level * 0.18) + jitter
            current_particles += (target_pts - current_particles) * 0.25
        else:
            target_pts = home_particles * sphere_scale
            current_particles += (target_pts - current_particles) * 0.12

        # Rotate particles
        rotated = np.dot(current_particles, R.T)

        # 3D Perspective Projection
        FOCAL = 600.0
        z_projected = rotated[:, 2] + 700.0
        valid_mask = z_projected > 50.0

        xs = (rotated[:, 0] * FOCAL / z_projected + sphere_center[0]).astype(np.int32)
        ys = (rotated[:, 1] * FOCAL / z_projected + sphere_center[1]).astype(np.int32)

        in_bounds = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h) & valid_mask
        canvas[ys[in_bounds], xs[in_bounds]] = color_bgr

        # Draw Charge Ring
        if charge_level > 0.02:
            cx_int, cy_int = int(sphere_center[0]), int(sphere_center[1])
            radius = int(85 * sphere_scale)
            cv2.circle(canvas, (cx_int, cy_int), radius, (50, 50, 50), 2)
            angle_end = int(360 * charge_level)
            cv2.ellipse(canvas, (cx_int, cy_int), (radius, radius), -90, 0, angle_end, (0, 240, 255), 4)
            cv2.putText(canvas, f"{int(charge_level*100)}%", (cx_int - 20, cy_int + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # UI Overlay
        cv2.putText(canvas, "AETHER SPHERE (PYTHON DESKTOP)", (30, 45), 
                    cv2.FONT_HERSHEY_TRIPLEX, 0.8, (255, 255, 255), 1)
        cv2.putText(canvas, f"Tracking: {hand_count} Hands | 'B' toggle backdrop | 'Q' quit", 
                    (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        cv2.imshow("Aether Sphere — Native Python", canvas)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('b'):
            show_backdrop = not show_backdrop

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aether Sphere 3D Interactive Controller")
    parser.add_argument("--native", action="store_true", help="Launch Native OpenCV/MediaPipe desktop window")
    parser.add_argument("--port", type=int, default=8080, help="Web server port (default: 8080)")
    args = parser.parse_args()

    if args.native:
        run_native_python_sphere()
    else:
        run_web_server(port=args.port)
