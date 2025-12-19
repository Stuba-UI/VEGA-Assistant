import chromadb
import hashlib

class vegaMemory:
    def __init__(self):
        # 1. Initialize Database (Persistent = Saved to disk)
        self.client = chromadb.PersistentClient(path="./vega_memory_db")
        
        # 2. Create/Load Collection
        # "get_or_create" means it loads your old memories if they exist
        self.collection = self.client.get_or_create_collection(name="user_facts")

    def _generate_id(self, text):
        """Generates a STABLE ID. 'I like pizza' will always equal the same ID."""
        return hashlib.sha256(text.encode()).hexdigest()

    def remember(self, text):
        doc_id = self._generate_id(text)
        
        # Check if we already know this to avoid log spam
        existing = self.collection.get(ids=[doc_id])
        if existing['ids']:
            print(f"[Memory] I already know: '{text}'")
            return

        print(f"[Memory] Storing new fact: '{text}'")
        self.collection.add(
            documents=[text],
            ids=[doc_id]
        )

    def recall(self, query):
        print(f"[Memory] Searching for: '{query}'...")
        results = self.collection.query(
            query_texts=[query],
            n_results=2 
        )
        
        # Safety check: Did we actually find anything?
        if results['documents'] and results['documents'][0]:
            return results['documents'][0] # Returns a list of matches
        return []

# --- INTEGRATION WITH MAIN ---
# You can paste this Class into a new file `core/memory.py`
# Then in main.py:
# from core.memory import vegaMemory
# memory = vegaMemory()
# memory.remember(user_text) # Call this when user says "Remember that..."
