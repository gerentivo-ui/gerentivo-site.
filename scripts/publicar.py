#!/usr/bin/env python3
"""Publica no Instagram (@gerentivo) os posts APROVADOS da fila cuja hora já chegou.

Lê posts/fila.json. Só publica itens com "status": "aprovado" e "publicar_em" <= agora.
As imagens precisam estar no ar em https://gerentivo.com.br/<caminho> (GitHub Pages).
Segredos (GitHub Actions): IG_TOKEN, IG_USER_ID.
"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://graph.instagram.com/v26.0"
SITE = os.environ.get("SITE_URL", "https://gerentivo.com.br").rstrip("/")
TOKEN = os.environ["IG_TOKEN"]
IG_ID = os.environ["IG_USER_ID"]
FILA = "posts/fila.json"

def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace").replace(TOKEN, "***")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {corpo}") from None

def esperar(container_id):
    for _ in range(10):
        st = call("GET", container_id, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container_id} terminou com {st}")
        time.sleep(30)
    raise RuntimeError(f"container {container_id} não ficou pronto a tempo")

def url_publica(caminho):
    url = f"{SITE}/{caminho.lstrip('/')}"
    try:  # confere que o GitHub Pages já serve a imagem
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as r:
            if r.status != 200:
                raise RuntimeError
    except Exception:
        raise RuntimeError(f"imagem ainda não está no ar: {url}")
    return url

def publicar(item, selo_ia):
    imgs = [url_publica(p) for p in item["imagens"]]
    extra = {"is_ai_generated": "true"} if selo_ia else {}
    if len(imgs) == 1:
        c = call("POST", f"{IG_ID}/media", image_url=imgs[0], caption=item["legenda"], **extra)["id"]
    else:
        filhos = []
        for u in imgs[:10]:
            filhos.append(call("POST", f"{IG_ID}/media", image_url=u, is_carousel_item="true")["id"])
        for f in filhos:
            esperar(f)
        c = call("POST", f"{IG_ID}/media", media_type="CAROUSEL", children=",".join(filhos),
                 caption=item["legenda"], **extra)["id"]
    esperar(c)
    media_id = call("POST", f"{IG_ID}/media_publish", creation_id=c)["id"]
    link = call("GET", media_id, fields="permalink").get("permalink", "")
    return media_id, link

def main():
    fila = json.load(open(FILA, encoding="utf-8"))
    agora = datetime.now(timezone.utc)
    selo_ia = fila.get("selo_ia", True)
    mudou, falhas = False, 0
    for item in fila["posts"]:
        if item.get("status") != "aprovado":
            continue
        quando = datetime.fromisoformat(item["publicar_em"])
        if quando > agora:
            continue
        print(f"Publicando {item['id']} (marcado para {item['publicar_em']})...")
        try:
            media_id, link = publicar(item, selo_ia)
            item.update(status="publicado", media_id=media_id, permalink=link,
                        publicado_em=agora.astimezone().isoformat(timespec="minutes"))
            item.pop("erro", None)
            print(f"  ok: {link}")
        except Exception as e:
            item["erro"] = str(e)[:500]
            falhas += 1
            print(f"  FALHOU: {e}")
        mudou = True
        break  # um post por execução, para não atropelar
    if mudou:
        with open(FILA, "w", encoding="utf-8") as f:
            json.dump(fila, f, ensure_ascii=False, indent=2)
            f.write("\n")
    sys.exit(1 if falhas else 0)

if __name__ == "__main__":
    main()
