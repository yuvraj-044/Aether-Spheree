# 🔮 Aether Sphere

A real-time 3D particle sphere (3,000 particles) that reacts to your hand gestures using webcam tracking and MediaPipe.

---

## ⚡ Quick Start

### 1. Web Version (Recommended)
Run the built-in launcher:
```bash
python3 app.py
```
*Opens `http://127.0.0.1:8080/index1.html` automatically in your browser.*

### 2. Native Python Window
```bash
pip install -r requirements.txt
python3 app.py --native
```

---

## 🖐️ Gesture Controls

| Gesture | Action |
|---|---|
| **Single Hand** | Moves and tilts the 3D sphere smoothly |
| **Pinch & Hold** | Charges the plasma energy ring |
| **Release Pinch** | Triggers cosmic particle explosion & smooth reform |
| **Two Hands** | Spread apart to expand sphere, bring together to shrink |
| **Finger Count (0–5)** | Shifts particle color (Crimson → Cyan → Emerald → Amber → Violet → Aurora) |
| **Mouse / Touch** | Fallback control: click-and-drag to orbit, scroll wheel to resize |

---

## ✨ Features

- **Single Self-Contained File**: Everything in [index1.html](file:///Users/yuvii/Documents/My%20Projects/fun/index1.html) (Three.js + MediaPipe).
- **Ultra-Smooth Damping**: Exponential lerp physics eliminate webcam jitter.
- **Minimal Dark Luxury UI**: Serif typography (*Playfair Display* / *Cinzel*).
- **Webcam Backdrop Button**: Toggle mirrored camera feed behind particles.
- **Synthesized Audio**: Web Audio API sci-fi charge and explosion sound effects.
