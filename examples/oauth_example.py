# -*- coding: utf-8 -*-
"""
Exemplo de autenticação OAuth2 com Sankhya API Gateway.

Este exemplo demonstra o fluxo completo de autenticação:
1. Carregar credenciais do .env
2. Autenticar via OAuth2 Client Credentials
3. Obter Bearer Token
4. Fazer uma requisição de teste

Requisitos:
- .env configurado com as credenciais corretas
- Token de Integração (X-Token) obtido em Configurações Gateway
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv


# =============================================================================
# Configuração
# =============================================================================

load_dotenv()

# Credenciais OAuth2 (Portal do Desenvolvedor - areadev.sankhya.com.br)
SANKHYA_CLIENT_ID = os.getenv("SANKHYA_CLIENT_ID")
SANKHYA_CLIENT_SECRET = os.getenv("SANKHYA_CLIENT_SECRET")

# Token de Integração (Configurações Gateway no Sankhya OM)
SANKHYA_X_TOKEN = os.getenv("SANKHYA_TOKEN")

# URL base para autenticação
SANKHYA_AUTH_BASE_URL = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")


# =============================================================================
# Funções de Autenticação
# =============================================================================

def validate_credentials() -> bool:
    """Valida se todas as credenciais estão configuradas."""
    missing = []
    
    if not SANKHYA_CLIENT_ID:
        missing.append("SANKHYA_CLIENT_ID")
    if not SANKHYA_CLIENT_SECRET:
        missing.append("SANKHYA_CLIENT_SECRET")
    if not SANKHYA_X_TOKEN:
        missing.append("SANKHYA_TOKEN")
    
    if missing:
        print("❌ Credenciais ausentes no .env:")
        for var in missing:
            print(f"   - {var}")
        return False
    
    print("✅ Todas as credenciais configuradas")
    print(f"   Client ID: {SANKHYA_CLIENT_ID[:8]}...{SANKHYA_CLIENT_ID[-4:]}")
    print(f"   X-Token:   {SANKHYA_X_TOKEN[:8]}...{SANKHYA_X_TOKEN[-4:]}")
    return True


def authenticate_oauth2() -> Optional[Dict[str, Any]]:
    """
    Autentica via OAuth2 Client Credentials Flow.
    
    Endpoint: POST /authenticate
    Headers: X-Token (Token de Integração)
    Body: client_id, client_secret, grant_type=client_credentials
    
    Returns:
        Dict com access_token, expires_in, etc. ou None em caso de erro
    """
    url = f"{SANKHYA_AUTH_BASE_URL}/authenticate"
    
    payload = {
        "client_id": SANKHYA_CLIENT_ID,
        "client_secret": SANKHYA_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    headers = {
        "X-Token": SANKHYA_X_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print(f"\n🔐 Autenticando em: {url}")
    print(f"   Headers: X-Token={SANKHYA_X_TOKEN[:8]}...")
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            
            print(f"\n✅ Autenticação bem-sucedida!")
            print(f"   Access Token: {access_token[:20]}...{access_token[-10:]}")
            print(f"   Expira em: {expires_in} segundos")
            
            return {
                "access_token": access_token,
                "expires_in": expires_in,
                "token_type": data.get("token_type", "Bearer"),
                "raw_response": data
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = (
                error_data.get("error_description") 
                or error_data.get("error") 
                or response.text
            )
            
            print(f"\n❌ Falha na autenticação:")
            print(f"   Status: {response.status_code}")
            print(f"   Erro: {error_msg}")
            
            # Diagnóstico de erros comuns
            if "X-Token" in str(error_msg):
                print("\n💡 Dica: Verifique se o Token de Integração está correto.")
                print("   Obtenha em: Sankhya OM > Configurações Gateway > Chave do cliente")
            elif "Invalid client" in str(error_msg):
                print("\n💡 Dica: Verifique CLIENT_ID e CLIENT_SECRET.")
                print("   Obtenha em: areadev.sankhya.com.br > Minhas soluções")
            
            return None
            
    except requests.Timeout:
        print("\n❌ Timeout na requisição")
        return None
    except requests.RequestException as e:
        print(f"\n❌ Erro de rede: {e}")
        return None


def test_api_call(access_token: str) -> bool:
    """
    Faz uma chamada de teste à API usando o Bearer Token.
    
    Args:
        access_token: Token JWT obtido na autenticação
        
    Returns:
        True se a chamada foi bem-sucedida
    """
    # Endpoint de teste - lista informações básicas
    url = f"{SANKHYA_AUTH_BASE_URL}/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.getSchema"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Payload mínimo para teste
    payload = {
        "serviceName": "DbExplorerSP.getSchema",
        "requestBody": {
            "entityName": "Parceiro"
        }
    }
    
    print(f"\n🧪 Testando chamada à API...")
    print(f"   Endpoint: {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Chamada de teste bem-sucedida!")
            return True
        else:
            print(f"⚠️  Chamada retornou: {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False



# =============================================================================
# Auto-Refresh Demonstration
# =============================================================================

def demo_auto_refresh():
    """
    Demonstra auto-refresh de tokens em ação.
    
    Mostra como fazer múltiplas requisições sem se preocupar com renovação de tokens.
    O SDK cuida de tudo automaticamente!
    """
    print("\n" + "=" * 60)
    print("🔄 Demonstração: Auto-Refresh de Tokens OAuth2")
    print("=" * 60)
    
    if not validate_credentials():
        print("\n⚠️  Configure o arquivo .env antes de executar.")
        return
    
    # Configurar cliente OAuth
    from sankhya_sdk.auth import OAuthClient
    from sankhya_sdk.http.session import SankhyaSession
    
    oauth = OAuthClient(
        base_url=SANKHYA_AUTH_BASE_URL,
        token=SANKHYA_X_TOKEN
    )
    
    print("\n🔐 Autenticando...")
    oauth.authenticate(SANKHYA_CLIENT_ID, SANKHYA_CLIENT_SECRET)
    print("✅ Autenticado com sucesso!")
    
    # Criar sessão HTTP com auto-refresh
    session = SankhyaSession(oauth, base_url=SANKHYA_AUTH_BASE_URL)
    
    print("\n" + "-" * 60)
    print("Fazendo múltiplas requisições...")
    print("O token será renovado automaticamente quando necessário!")
    print("-" * 60)
    
    # Simular múltiplas requisições
    for i in range(3):
        print(f"\n📡 Requisição {i+1}...")
        try:
            # Exemplo: listar informações do schema
            # (ajuste o endpoint conforme sua API)
            response = session.post(
                "/gateway/v1/mge/service.sbr",
                json={
                    "serviceName": "DbExplorerSP.getSchema",
                    "requestBody": {"entityName": "Parceiro"}
                }
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Requisição bem-sucedida!")
            else:
                print(f"   ⚠️  Status inesperado: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Demonstração concluída!")
    print("\nO que aconteceu:")
    print("  • Você fez múltiplas requisições consecutivas")
    print("  • O SDK verificou automaticamente a validade do token em cada chamada")
    print("  • Se o token estivesse próximo de expirar, seria renovado automaticamente")
    print("  • Você não precisou se preocupar com nada disso! 🎉")
    print("=" * 60)


# =============================================================================
# Main
# =============================================================================

def main():
    """Executa o exemplo de autenticação OAuth2."""
    print("=" * 60)
    print("🔑 Exemplo de Autenticação OAuth2 - Sankhya API")
    print("=" * 60)
    
    # 1. Validar credenciais
    print("\n📋 Verificando credenciais...")
    if not validate_credentials():
        print("\n⚠️  Configure o arquivo .env antes de executar.")
        sys.exit(1)
    
    # 2. Autenticar
    print("\n" + "-" * 40)
    result = authenticate_oauth2()
    
    if not result:
        print("\n⚠️  Verifique as configurações e tente novamente.")
        sys.exit(1)
    
    # 3. Teste opcional
    print("\n" + "-" * 40)
    test_api_call(result["access_token"])
    
    print("\n" + "=" * 60)
    print("✅ Exemplo finalizado")
    print("=" * 60)
    
    # 4. Demonstração de auto-refresh (opcional)
    print("\n\n💡 Deseja ver a demonstração de auto-refresh? (s/n): ", end="")
    try:
        choice = input().lower()
        if choice == 's':
            demo_auto_refresh()
    except (EOFError, KeyboardInterrupt):
        print("\n\nDemo cancelado.")
    
    return result


if __name__ == "__main__":
    main()
