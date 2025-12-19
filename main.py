# -*- coding: utf-8 -*-
import sys
import threading
import asyncio
import os
import time
import math
import json
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw
import pystray
from dotenv import load_dotenv

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame
import edge_tts

from core.brain import MagicBrain
from core.hands import vegaHands
from RealtimeSTT import AudioToTextRecorder

# --- CONFIG ---
load_dotenv() 
API_KEY = os.getenv("GROQ_API_KEY")

SETTINGS = {
    "name": "VEGA",
    "voice": "en-US-ChristopherNeural",
    "ai_model": "llama-3.1-8b-instant",       # Default Text
    "vision_model": "llama-3.2-11b-vision-preview", # Default Vision
    "device": "cpu",
    "stt_model": "medium.en"
}

if os.path.exists("settings.json"):
    try:
        with open("settings.json", "r") as f:
            data = json.load(f)
            SETTINGS["voice"] = data.get("voice_name", SETTINGS["voice"])
            SETTINGS["ai_model"] = data.get("ai_model", SETTINGS["ai_model"])
            SETTINGS["vision_model"] = data.get("vision_model", SETTINGS["vision_model"])
            SETTINGS["name"] = data.get("assistant_name", SETTINGS["name"])
            SETTINGS["device"] = data.get("device", SETTINGS["device"])
            SETTINGS["stt_model"] = data.get("stt_model", SETTINGS["stt_model"])
    except: pass

OUTPUT_FILE = "response.mp3"

# --- VISUALIZER ---
class NeuralMap(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, bg="#050505", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.num_particles = 60
        self.particles = []
        self.rotation_speed = 0.02
        self.current_color = "#00E5FF" 
        self.init_particles()
        self.animate()

    def init_particles(self):
        for i in range(self.num_particles):
            phi = math.acos(-1 + (2 * i) / self.num_particles)
            theta = math.sqrt(self.num_particles * math.pi) * phi
            r = 100 
            x = r * math.cos(theta) * math.sin(phi)
            y = r * math.sin(theta) * math.sin(phi)
            z = r * math.cos(phi)
            self.particles.append([x, y, z])

    def set_state(self, state):
        if state == "IDLE":
            self.rotation_speed, self.current_color = 0.02, "#00E5FF"
        elif state == "LISTENING":
            self.rotation_speed, self.current_color = 0.01, "#00FF00"
        elif state == "THINKING":
            self.rotation_speed, self.current_color = 0.15, "#FFD700"
        elif state == "SPEAKING":
            self.rotation_speed, self.current_color = 0.05, "#FF3333"
        elif state == "SLEEP":
            self.rotation_speed, self.current_color = 0.002, "#333333"

    def animate(self):
        if not self.winfo_viewable():
            self.after(500, self.animate)
            return
        self.canvas.delete("all")
        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()
        cx, cy = self.width // 2, self.height // 2
        cos_a = math.cos(self.rotation_speed)
        sin_a = math.sin(self.rotation_speed)
        transformed = []
        for i, p in enumerate(self.particles):
            x, y, z = p
            new_x = x * cos_a - z * sin_a
            new_z = x * sin_a + z * cos_a
            self.particles[i] = [new_x, y, new_z]
            scale = 300 / (300 + new_z + 200)
            px, py = cx + new_x * scale, cy + y * scale
            transformed.append((px, py))
            size = 2 * scale
            self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=self.current_color, outline="")
        for i in range(len(transformed)):
            for j in range(i + 1, len(transformed)):
                x1, y1 = transformed[i]
                x2, y2 = transformed[j]
                if (x1-x2)**2 + (y1-y2)**2 < 2500:
                    self.canvas.create_line(x1, y1, x2, y2, fill=self.current_color, width=1)
        self.after(30, self.animate)

# --- MAIN APP ---
class AssistantGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{SETTINGS['name']} // SYSTEM INTERFACE")
        self.geometry("1000x650") # Slightly wider for settings
        ctk.set_appearance_mode("Dark")
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Title
        ctk.CTkLabel(self.sidebar, text=SETTINGS['name'], font=("Impact", 24)).pack(pady=(30, 20))
        
        # Sleep Button
        self.sleep_btn = ctk.CTkButton(
            self.sidebar, 
            text="SLEEP MODE", 
            fg_color="#4B0082",
            hover_color="#300052",
            command=self.toggle_sleep
        )
        self.sleep_btn.pack(pady=10, padx=20)

        # --- MODEL SETTINGS (DROPDOWNS) ---
        ctk.CTkLabel(self.sidebar, text="AI MODEL (TEXT)", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        self.text_model_var = ctk.StringVar(value=SETTINGS["ai_model"])
        self.text_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=[
                "llama-3.1-8b-instant", 
                "llama-3.3-70b-versatile",
                "meta-llama/llama-3.2-90b-vision-preview" 
            ],
            variable=self.text_model_var,
            command=self.change_text_model
        )
        self.text_dropdown.pack(pady=5, padx=20)

        ctk.CTkLabel(self.sidebar, text="VISION MODEL (EYES)", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        self.vision_model_var = ctk.StringVar(value=SETTINGS["vision_model"])
        self.vision_dropdown = ctk.CTkOptionMenu(
            self.sidebar,
            values=[
                "llama-3.2-11b-vision-preview",
                "llama-3.2-90b-vision-preview",
                "llama-3.2-11b-vision-preview"
            ],
            variable=self.vision_model_var,
            command=self.change_vision_model
        )
        self.vision_dropdown.pack(pady=5, padx=20)

        # Status Label
        self.cpu_label = ctk.CTkLabel(self.sidebar, text="SYSTEM: ONLINE")
        self.cpu_label.pack(side="bottom", pady=10)

        # --- MAIN AREA ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.neural_map = NeuralMap(self.main_area)
        self.neural_map.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.chat_box = ctk.CTkTextbox(self.main_area, height=150, font=("Consolas", 14), state="disabled")
        self.chat_box.grid(row=1, column=0, sticky="ew")
        self.status_bar = ctk.CTkLabel(self.main_area, text="INITIALIZING...", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew")

        # INIT BACKEND
        self.brain = MagicBrain(api_key=API_KEY)
        self.hands = vegaHands()
        pygame.mixer.init()
        self.is_running = True
        self.is_sleeping = False 
        self.recorder = None
        
        threading.Thread(target=self.bg_listener, daemon=True).start()
        threading.Thread(target=self.init_tray_icon, daemon=True).start()

    # --- NEW SETTINGS LOGIC ---
    def save_settings(self):
        """Saves current dropdown choices to JSON"""
        data = {}
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
            except: pass
        
        data["ai_model"] = self.text_model_var.get()
        data["vision_model"] = self.vision_model_var.get()
        
        with open("settings.json", "w") as f:
            json.dump(data, f, indent=4)

    def change_text_model(self, choice):
        self.log("SYS", f"Switched Brain to: {choice}")
        self.brain.set_models(text_model=choice)
        self.save_settings()

    def change_vision_model(self, choice):
        self.log("SYS", f"Switched Eyes to: {choice}")
        self.brain.set_models(vision_model=choice)
        self.save_settings()

    # --- EXISTING LOGIC ---
    def toggle_sleep(self):
        if self.is_sleeping:
            self.is_sleeping = False
            self.sleep_btn.configure(text="SLEEP MODE", fg_color="#4B0082")
            self.log("SYS", "SYSTEMS WAKING UP...")
            self.set_status("ONLINE", "IDLE")
            self.speak("Systems online.")
        else:
            self.is_sleeping = True
            self.sleep_btn.configure(text="WAKE UP", fg_color="#006400")
            self.log("SYS", "ENTERING SLEEP MODE...")
            self.set_status("SLEEPING (Say 'Hello Vega' or 'Hei Vega')", "SLEEP")
            self.speak("Going to sleep.")

    def set_timer(self, seconds, message):
        def timer_done():
            if self.is_running:
                self.log("TIMER", f"REMINDER: {message}")
                self.speak(f"Excuse me. Reminder: {message}")
        self.log("SYS", f"Timer set for {seconds}s: {message}")
        threading.Timer(float(seconds), timer_done).start()

    def graceful_shutdown(self):
        self.log("SYS", "SHUTDOWN SEQUENCE...")
        self.is_running = False
        if pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except: pass
        if self.recorder:
            try: self.recorder.shutdown()
            except: pass
        print(">>> GOODBYE.")
        self.quit()
        os._exit(0)

    def init_tray_icon(self):
        image = Image.new('RGB', (64, 64), color = (0, 0, 0))
        d = ImageDraw.Draw(image)
        d.ellipse((10, 10, 54, 54), fill=(0, 229, 255)) 

        def show_window(icon, item):
            self.after(0, self.deiconify)

        def toggle_sleep_tray(icon, item):
            self.after(0, self.toggle_sleep)

        def quit_app(icon, item):
            icon.stop()
            self.graceful_shutdown()

        menu = pystray.Menu(
            pystray.MenuItem('Open Interface', show_window),
            pystray.MenuItem('Toggle Sleep/Wake', toggle_sleep_tray),
            pystray.MenuItem('Force Quit', quit_app)
        )
        self.tray_icon = pystray.Icon(SETTINGS['name'], image, SETTINGS['name'], menu)
        self.tray_icon.run()

    def minimize_to_tray(self):
        self.withdraw()

    def log(self, sender, text):
        try:
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", f"[{sender}]: {text}\n")
            self.chat_box.see("end")
            self.chat_box.configure(state="disabled")
        except: pass

    def set_status(self, text, state="IDLE"):
        try:
            self.status_bar.configure(text=f">> {text}")
            self.neural_map.set_state(state)
        except: pass

    def process(self, text):
        if not text: return
        clean_text = text.lower().replace(".", "").replace("!", "").replace("?", "").replace(",", "").strip()

        # --- 1. SLEEP MODE ---
        if self.is_sleeping:
            wake_word_found = False
            triggers = ["hello vega", "hei vega", "hey vega", "hi vega", "wake up"]
            used_trigger = ""
            for t in triggers:
                if t in clean_text:
                    wake_word_found = True
                    used_trigger = t
                    break
            if not wake_word_found: return 
            
            command_only = clean_text.replace(used_trigger, "").strip()
            if len(command_only) < 2:
                self.after(0, self.toggle_sleep)
                return
            else:
                self.log("SYS", "ONE-SHOT COMMAND DETECTED...")
                text = command_only

        # --- 2. GO TO SLEEP ---
        if clean_text in ["go to sleep", "sleep mode", "mene nukkumaan", "lepotila"]:
            self.after(0, self.toggle_sleep)
            return

        self.log("YOU", text)
        self.set_status("PROCESSING...", "THINKING")

        # --- 3. STOP ---
        if clean_text in ["stop", "shh", "quiet", "silence", "hiljaa", "dur"]:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self.log("SYS", "AUDIO INTERRUPTED.")
                self.set_status("INTERRUPTED", "LISTENING")
            return

        # --- 4. QUIT ---
        if clean_text in ["quit", "exit"]:
            self.speak("Shutting down systems.")
            self.after(3000, self.graceful_shutdown)
            return

        # --- 5. HANDS ---
        response_action = self.hands.execute_command(text)
        if response_action:
            self.log("SYS", response_action)
            if self.is_sleeping: self.set_status("SLEEPING...", "SLEEP")
            else: self.set_status("EXECUTED", "IDLE")
            return

        # --- 6. VISION ---
        img_path = None
        triggers = ["look", "see", "screen", "katso", "nayta", "näytä"]
        if any(x in clean_text for x in triggers):
            import pyautogui
            img_path = "capture.jpg"
            pyautogui.screenshot().save(img_path)
            text += " (Analyze this)"

        # --- 7. BRAIN ---
        response = self.brain.think(text, image_path=img_path)

        # TAGS
        if "[TYPE:" in response:
            try:
                start = response.find("[TYPE:") + 6
                end = response.find("]", start)
                text_to_type = response[start:end].strip()
                self.hands.type_text(text_to_type)
                speech_text = response.replace(f"[TYPE: {text_to_type}]", "").replace(f"[TYPE:{text_to_type}]", "")
                self.log(SETTINGS['name'], f"[TYPING]: {text_to_type}")
                self.speak(speech_text)
                return
            except: pass
            
        if "[TIMER:" in response:
            try:
                start = response.find("[TIMER:") + 7
                end = response.find("]", start)
                content = response[start:end].split(",")
                seconds = content[0].strip()
                message = content[1].strip() if len(content) > 1 else "Timer done"
                self.set_timer(seconds, message)
                speech_text = response.replace(f"[TIMER: {seconds}, {message}]", "").replace(f"[TIMER:{seconds},{message}]", "")
                self.speak(speech_text)
                return
            except: pass

        self.log(SETTINGS['name'], response)
        self.speak(response)

    def speak(self, text):
        self.set_status("SPEAKING...", "SPEAKING")
        try: pygame.mixer.music.unload()
        except: pass

        try:
            asyncio.run(self._gen_audio(text))
        except PermissionError:
            time.sleep(0.2)
            try:
                if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
                asyncio.run(self._gen_audio(text))
            except: return

        try:
            pygame.mixer.music.load(OUTPUT_FILE)
            pygame.mixer.music.play()
            threading.Thread(target=self._monitor_playback, daemon=True).start()
        except Exception as e:
            self.log("SYS", f"Playback Error: {e}")

    def _monitor_playback(self):
        while pygame.mixer.music.get_busy() and self.is_running:
            time.sleep(0.1)
        
        if self.is_sleeping:
            self.set_status("SLEEPING (Say 'Hello Vega')", "SLEEP")
        else:
            self.set_status("LISTENING...", "LISTENING")
            
        try: pygame.mixer.music.unload()
        except: pass

    async def _gen_audio(self, text):
        communicate = edge_tts.Communicate(text, SETTINGS["voice"])
        await communicate.save(OUTPUT_FILE)

    def bg_listener(self):
        print(f">>> INITIALIZING EARS ({SETTINGS['stt_model']}) ON: {SETTINGS['device'].upper()}")
        try:
            self.recorder = AudioToTextRecorder(
                spinner=False, 
                model=SETTINGS['stt_model'], 
                language="en",
                device=SETTINGS['device'], 
                compute_type="int8"
            )
        except Exception as e:
            self.log("SYS", f"Mic Error: {e}")
            return

        self.set_status("ONLINE (LISTENING)", "LISTENING")
        while self.is_running:
            try:
                text = self.recorder.text()
                if text and len(text) > 1:
                    self.process(text)
            except:
                if not self.is_running: break
                time.sleep(0.5)

if __name__ == "__main__":
    app = AssistantGUI()
    app.mainloop()