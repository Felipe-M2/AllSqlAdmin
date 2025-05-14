import os
from pathlib import Path
from cryptography.fernet import Fernet
import base64

class SimpleCrypto:
    def __init__(self):
        # Cria a pasta 'files' se não existir
        self.files_dir = Path(os.getcwd()) / "files"
        self.files_dir.mkdir(exist_ok=True)
        
        # Caminho para o arquivo de chave
        self.key_file = self.files_dir / "secret.key"
        
        # Carrega ou gera uma nova chave
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self):
        """Carrega a chave do arquivo ou gera uma nova"""
        if self.key_file.exists():
            # Lê a chave existente (codificada em base64)
            with open(self.key_file, "rb") as f:
                encoded_key = f.read()
            return base64.urlsafe_b64decode(encoded_key)
        else:
            # Gera uma nova chave e salva (codificada em base64)
            new_key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(base64.urlsafe_b64encode(new_key))
            return new_key
    
    def encrypt(self, text):
        """Criptografa o texto usando Fernet"""
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt(self, encrypted_text):
        """Descriptografa o texto usando Fernet"""
        return self.cipher.decrypt(encrypted_text.encode()).decode()