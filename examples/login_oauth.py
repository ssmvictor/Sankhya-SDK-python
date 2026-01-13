import os
import logging
from dotenv import load_dotenv
from sankhya_sdk.auth.oauth_client import OAuthClient
from sankhya_sdk.http.session import SankhyaSession

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

def main():
    # Carrega variáveis do arquivo .env
    load_dotenv()
    
    # Obtém credenciais das variáveis de ambiente
    client_id = os.getenv("SANKHYA_CLIENT_ID", "seu_client_id")
    client_secret = os.getenv("SANKHYA_CLIENT_SECRET", "seu_client_secret")
    base_url = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")
    token_extra = os.getenv("SANKHYA_TOKEN") # X-Token

    if client_id == "seu_client_id":
        print("Defina as variáveis de ambiente para testar.")
        return

    print(f"Iniciando autenticação OAuth com {base_url}...")

    # 1. Inicializa o cliente OAuth
    oauth = OAuthClient(base_url=base_url, token=token_extra)

    try:
        # 2. Realiza a autenticação inicial
        token = oauth.authenticate(client_id, client_secret)
        print(f"Autenticado com sucesso! Token: {token[:10]}...")

        # 3. Cria a sessão autenticada
        session = SankhyaSession(oauth_client=oauth, base_url=base_url)

        # 4. Exemplo de requisição (ajuste o endpoint conforme sua API)
        # Endpoint arbitrário apenas para demonstrar a injeção do header
        print("Tentando acessar endpoint de teste...")
        response = session.get("/gateway/v1/mge/teste")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
