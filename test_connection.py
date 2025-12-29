# -*- coding: utf-8 -*-
"""Script de teste de conexão com a API Sankhya."""

from dotenv import load_dotenv
import os

load_dotenv()

print("=== Configurações carregadas ===")
url = os.getenv('SANKHYA_URL')
port = int(os.getenv('SANKHYA_PORT', '8180'))
username = os.getenv('SANKHYA_USERNAME')
password = os.getenv('SANKHYA_PASSWORD')

print(f"URL: {url}:{port}")
print(f"User: {username}")
print()

from sankhya_sdk.core.wrapper import SankhyaWrapper

print("=== Criando wrapper ===")
try:
    wrapper = SankhyaWrapper(host=url, port=port)
    print(f"Wrapper criado: {wrapper.base_url}")
    
    print()
    print("=== Tentando autenticação ===")
    wrapper.authenticate(username, password)
    
    if wrapper.is_authenticated:
        print("✅ Autenticado com sucesso!")
        print(f"   User Code: {wrapper.user_code}")
        print(f"   Session ID: {wrapper.session_id[:30]}..." if wrapper.session_id and len(wrapper.session_id) > 30 else f"   Session ID: {wrapper.session_id}")
    else:
        print("❌ Falha na autenticação")
    
    print()
    print("=== Logout ===")
    wrapper.dispose()
    print("✅ Logout realizado com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
