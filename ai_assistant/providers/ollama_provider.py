import requests
import json
from typing import Dict, Any

class OllamaProvider:
    def __init__(self, model="llama2"):
        self.base_url = "http://localhost:11434"
        self.model = model
        self.check_connection()
    
    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Ollama server not running")
        except:
            raise ConnectionError("Could not connect to Ollama. Make sure it's running.")
    
    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        try:
            # Prepare prompt with context
            prompt = f"Context: You are assisting with a {context.get('window', 'desktop')} application.\n"
            if context.get('data'):
                prompt += f"Additional context: {json.dumps(context['data'])}\n"
            prompt += f"\nUser query: {query}\n\nResponse:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                return "Error: Could not generate response from Ollama"
                
        except Exception as e:
            return f"Error: {str(e)}"