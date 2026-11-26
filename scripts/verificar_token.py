#!/usr/bin/env python3
"""Confere se o token do Instagram funciona e, quando possível, renova.

- Token do login unificado/Facebook (começa com "EAA", usuário do sistema): não expira; só confere.
- Token do login do Instagram (começa com "IG"): renova. Se o secret GH_PAT existir, grava o token
  novo em IG_TOKEN sozinho; sem GH_PAT, FALHA quando faltarem menos de 15 dias para vencer
  (o GitHub manda e-mail).
"""
import json, os, subprocess, sys, urllib.parse, urllib.request

TOKEN = os.environ["IG_TOKEN"].strip()
IG_ID = os.environ.get("IG_USER_ID", "").strip()
FB = TOKEN.startswith("EAA")
HOST = "graph.facebook.com" if FB else "graph.instagram.com"
print(f"Tipo de token: {'login unificado/Facebook' if FB else 'login do Instagram'} (host {HOST}), {len(TOKEN)} caracteres")

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("Erro:", e.read().decode(errors="replace").replace(TOKEN, "***"))
        sys.exit(1)

q = urllib.parse.quote(TOKEN)
conta = get(f"https://{HOST}/v26.0/{IG_ID or 'me'}?fields=username&access_token={q}")
print(f"Token OK: acesso à conta @{conta.get('username')}")
if FB:
    print("Token de usuário do sistema: não precisa renovar.")
    sys.exit(0)

r = get(f"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={q}")
novo, dias = r.get("access_token"), int(r.get("expires_in", 0)) // 86400
print(f"Renovação: token válido por mais {dias} dias")
if novo and novo != TOKEN:
    if os.environ.get("GH_TOKEN"):
        subprocess.run(["gh", "secret", "set", "IG_TOKEN", "--body", novo], check=True)
        print("IG_TOKEN atualizado automaticamente.")
    elif dias < 15:
        print("ATENÇÃO: o token vence em menos de 15 dias e não há GH_PAT. Gere um novo token no app da Meta e atualize o secret IG_TOKEN.")
        sys.exit(1)
