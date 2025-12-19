import base64
import json
import os
import hashlib
import chromadb
from groq import Groq
from duckduckgo_search import DDGS

# --- MEMORY ENGINE ---
class vegaMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./vega_memory_db")
        self.collection = self.client.get_or_create_collection(name="user_facts")

    def _generate_id(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def remember(self, text):
        print(f">>> MEMORIZING: {text}")
        self.collection.add(documents=[text], ids=[self._generate_id(text)])

    def recall(self, query):
        try:
            results = self.collection.query(query_texts=[query], n_results=2)
            if results['documents'] and results['documents'][0]:
                return results['documents'][0]
        except: pass
        return []

# --- THE BRAIN ---
class MagicBrain:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        
        # Default Models
        self.text_model = "llama-3.1-8b-instant"
        self.vision_model = "llama-3.2-11b-vision-preview"
        
        # Try to load from settings.json
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    self.text_model = data.get("ai_model", self.text_model)
                    self.vision_model = data.get("vision_model", self.vision_model)
            except: pass
        
        self.long_term_memory = vegaMemory()
        self.short_term_file = "core/chat_history.json"
        
        self.system_prompt = {
            "role": "system", 
            "content": (
                "You are VEGA. "
                "1. TIMER: Output '[TIMER: seconds, message]'. "
                "2. TYPE: Output '[TYPE: text]'. "
                "3. SEARCH: Use [SEARCH RESULT] to answer news/weather. "
                "4. VISION: If an image is provided, analyze it directly."
                "Do not apologize. Be concise."
            )
        }
        self.load_short_term_memory()

    # --- NEW: LIVE MODEL SWITCHING ---
    def set_models(self, text_model=None, vision_model=None):
        if text_model:
            self.text_model = text_model
            print(f">>> SWITCHED BRAIN TO: {self.text_model}")
        if vision_model:
            self.vision_model = vision_model
            print(f">>> SWITCHED EYES TO: {self.vision_model}")

    def load_short_term_memory(self):
        if os.path.exists(self.short_term_file):
            try:
                with open(self.short_term_file, "r") as f:
                    self.chat_history = json.load(f)
            except:
                self.chat_history = [self.system_prompt]
        else:
            self.chat_history = [self.system_prompt]

    def save_short_term_memory(self):
        with open(self.short_term_file, "w") as f:
            json.dump(self.chat_history, f)

    def search_internet(self, query):
        print(f">>> BROWSING INTERNET: {query}")
        try:
            results = DDGS().text(query, max_results=3)
            if results:
                summary = " ".join([r['body'] for r in results])
                return f"\n[SEARCH RESULT for '{query}': {summary[:1000]}]"
        except Exception as e:
            print(f"Search failed: {e}")
        return "\n[SEARCH FAILED]"

    def think(self, text_input, image_path=None):
        clean_text = text_input.lower()
        
        # DYNAMIC MODEL SELECTION
        active_model = self.vision_model if image_path else self.text_model

        # 1. MEMORY
        if "remember" in clean_text and len(clean_text) > 10:
            fact = text_input.replace("remember", "").replace("that", "").strip()
            self.long_term_memory.remember(fact)

        # 2. CONTEXT & INTERNET
        context_str = ""
        relevant_facts = self.long_term_memory.recall(text_input)
        if relevant_facts:
            context_str += f"\n[MEMORY: {'; '.join(relevant_facts)}]"
        
        triggers = ["weather", "news", "price", "when is", "who is", "what is the", "current", "latest"]
        if any(t in clean_text for t in triggers):
            context_str += self.search_internet(text_input)

        # 3. PREPARE MESSAGE
        user_msg = {"role": "user", "content": []}
        
        if image_path:
            try:
                with open(image_path, "rb") as img:
                    b64_img = base64.b64encode(img.read()).decode('utf-8')
                user_msg["content"].append({"type": "text", "text": text_input + context_str})
                user_msg["content"].append({
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                })
            except Exception as e:
                return f"Error reading image: {e}"
        else:
            user_msg["content"] = text_input + context_str

        # 4. API CALL
        api_messages = self.chat_history + [user_msg]
        try:
            completion = self.client.chat.completions.create(
                model=active_model,
                messages=api_messages,
                temperature=0.6,
                max_tokens=400
            )
            response_text = completion.choices[0].message.content

            # 5. SAVE
            clean_input = text_input + " [Image]" if image_path else text_input
            self.chat_history.append({"role": "user", "content": clean_input})
            self.chat_history.append({"role": "assistant", "content": response_text})
            
            if len(self.chat_history) > 20:
                self.chat_history = [self.system_prompt] + self.chat_history[-15:]
            self.save_short_term_memory()

            return response_text

        except Exception as e:
            return f"Brain Error: {e}"