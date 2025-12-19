import pyautogui
import os
import webbrowser
import subprocess
import pyperclip
import time

class vegaHands:
    def __init__(self):
        pyautogui.FAILSAFE = True 

    def type_text(self, text):
        """Types text using clipboard (Best for game chat/non-English)"""
        try:
            # Short delay to ensure game window is focused
            time.sleep(0.2) 
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return f"Typed: {text}"
        except Exception as e:
            return f"Typing failed: {e}"

    def execute_command(self, command_text):
        cmd = command_text.lower().strip()
        
        # --- SMART WEB SEARCH ---
        if "search" in cmd and "youtube" in cmd:
            term = cmd.split("search")[-1].split("on")[0].split("from")[0].strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={term}")
            return f"Searching YouTube for {term}"

        elif "search" in cmd:
            term = cmd.replace("search", "").replace("google", "").replace("on", "").replace("for", "").strip()
            if term:
                webbrowser.open(f"https://www.google.com/search?q={term}")
                return f"Searching Google for {term}"

        # --- APP LAUNCHERS ---
        if "calculator" in cmd:
            os.system("calc")
            return "Calculator opened."
        elif "open google" in cmd:
            webbrowser.open("https://www.google.com")
            return "Google opened."
        elif "open youtube" in cmd:
            webbrowser.open("https://www.youtube.com")
            return "YouTube opened."
        elif "file explorer" in cmd or "open files" in cmd:
            subprocess.Popen(r'explorer /select,"C:\"')
            return "File Explorer opened."

        # --- SYSTEM CONTROLS ---
        elif "volume up" in cmd:
            pyautogui.press("volumeup", presses=5)
            return "Volume Up"
        elif "volume down" in cmd:
            pyautogui.press("volumedown", presses=5)
            return "Volume Down"
        elif "mute" in cmd:
            pyautogui.press("volumemute")
            return "Muted"
        elif "minimize" in cmd or "hide windows" in cmd:
            pyautogui.hotkey('win', 'd') 
            return "Desktop revealed"
            
        return None