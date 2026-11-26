#!/usr/bin/env python3
"""Confere se o token do Instagram funciona e tenta renová-lo.

Se o secret GH_PAT existir (token do GitHub com permissão de escrever Secrets neste repositório),
o token renovado é gravado automaticamente em IG_TOKEN. Sem GH_PAT, a execução FALHA quando
faltarem menos de 15 dias para vencer, e o GitHub manda um e-mail avisando.
"""
import json, os, subprocess, sys, urllib.parse, urllib.request

TOKEN = os.environ["IG_TOKEN"]

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("Erro:", e.read().decode(errors="replace").replace(TOKEN, "***"))
        sys.exit(1)

me = get("https://graph.instagram.com/v26.0/me?fields=user_id,username&access_token=" + urllib.parse.quote(TOKEN))
print(f"Token OK para @{me.get('username')}")

r = get("https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=" + urllib.parse.quote(TOKEN))
novo, dias = r.get("access_token"), int(r.get("expires_in", 0)) // 86400
print(f"Renovação: token válido por mais {dias} dias")
if novo and novo != TOKEN:
    if os.environ.get("GH_TOKEN"):
        subprocess.run(["gh", "secret", "set", "IG_TOKEN", "--body", novo], check=True)
        print("IG_TOKEN atualizado automaticamente.")
    elif dias < 15:
        print("ATENÇÃO: o token vence em menos de 15 dias e não há GH_PAT para atualizar sozinho. Gere um novo token no app da Meta e atualize o secret IG_TOKEN.")
        sys.exit(1)
