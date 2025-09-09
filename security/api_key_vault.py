import os
import json
from security.encryption_manager import EncryptionManager

class APIKeyVault:
    def __init__(self):
        self.encryption = EncryptionManager()
        self.vault_file = 'data/.api_keys'
        self.keys = self.load_keys()
    
    def load_keys(self):
        if os.path.exists(self.vault_file):
            try:
                with open(self.vault_file, 'rb') as f:
                    encrypted = f.read()
                    decrypted = self.encryption.decrypt(encrypted)
                    return json.loads(decrypted)
            except:
                return {}
        return {}
    
    def save_keys(self):
        os.makedirs('data', exist_ok=True)
        encrypted = self.encryption.encrypt(json.dumps(self.keys))
        with open(self.vault_file, 'wb') as f:
            f.write(encrypted)
    
    def set_key(self, service, key):
        self.keys[service] = key
        self.save_keys()
    
    def get_key(self, service, default=None):
        return self.keys.get(service, default)
    
    def remove_key(self, service):
        if service in self.keys:
            del self.keys[service]
            self.save_keys()