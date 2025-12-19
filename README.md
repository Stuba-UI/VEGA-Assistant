# VEGA Assistant (Voice Enhanced Generative Assistant)

VEGA is a local, voice-activated AI assistant designed for desktop control, gaming, and real-time information retrieval. It serves as a privacy-focused "Jarvis-like" companion that operates primarily on your CPU (with optional GPU acceleration) and interfaces with the Groq API for lightning-fast intelligence.

## ⚡ Features

* **Dual-Core Brain:** Automatically switches between `Llama-3.1-8b` (Speed) and `Llama-3.2-11b-Vision` (Sight) based on context.
* **Vision Capable:** Can see your screen, analyze games, and translate foreign text (Russian, Chinese, etc.) on the fly.
* **Sleep Mode:** Optimized for gamers. "Hei Vega" wakes it up for a single command, then it instantly sleeps to save resources/bandwidth.
* **System Control:** Can open apps, type text for you, and manage timers.
* **Invisible Internet:** Browses the web in the background to answer questions about weather, news, and stock prices without opening browser tabs.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/Stuba-UI/VEGA-Assistant.git](https://github.com/Stuba-UI/VEGA-Assistant.git)
    cd VEGA-Assistant
    ```

2.  **Install Dependencies**
    You need Python 3.10+.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You may also need to install `ffmpeg` on your system for audio processing.*

3.  **Setup Configuration**
    Rename `settings_example.json` to `settings.json`.
    ```json
    {
        "assistant_name": "VEGA",
        "voice_name": "en-US-ChristopherNeural",
        "ai_model": "llama-3.1-8b-instant",
        "vision_model": "llama-3.2-11b-vision-preview",
        "device": "cpu",
        "stt_model": "medium.en"
    }
    ```

4.  **Add API Keys**
    Create a `.env` file in the root folder and add your Groq key:
    ```env
    GROQ_API_KEY=gsk_your_key_here
    ```

## 🚀 Usage

Run the main script:
```bash
python main.py
Wake Word: "Hei Vega", "Hello Vega", or "Wake Up".

Sleep Command: "Go to sleep" (or use the GUI button).

One-Shot Mode: While sleeping, say "Hei Vega, what is the weather?" — He will wake up, answer, and immediately sleep again.

🧱 Built With
This project relies on these amazing open-source libraries:

RealtimeSTT - for low-latency speech recognition.

Edge-TTS - for high-quality neural voice synthesis.

Groq Python SDK - for the LLM intelligence.

DuckDuckGo Search - for privacy-preserving web searches.

⚠️ Disclaimer
This software is an AI experiment. It may generate incorrect information ("hallucinations").

Do not rely on this assistant for medical, legal, or financial advice.

API Costs: This project uses the Groq API. While currently offering a free tier, users are responsible for managing their own API usage and limits.

Privacy: This assistant listens to your microphone locally. No audio is sent to the cloud except for the text processing logic handled by Groq.

📄 License
This project is licensed under the MIT License - feel free to modify and distribute.
