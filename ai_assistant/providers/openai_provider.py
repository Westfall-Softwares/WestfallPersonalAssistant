import os
from typing import Dict, Any
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class OpenAIProvider:
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            from security.api_key_vault import APIKeyVault
            vault = APIKeyVault()
            self.api_key = vault.get_key('openai')
        
        if self.api_key:
            openai.api_key = self.api_key
        else:
            raise ValueError("OpenAI API key not configured")
    
    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        try:
            # Prepare context message
            context_msg = f"Current window: {context.get('window', 'Unknown')}"
            if context.get('data'):
                context_msg += f"\nContext data: {context['data']}"
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for a personal desktop application."},
                    {"role": "user", "content": f"{context_msg}\n\nUser query: {query}"}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"