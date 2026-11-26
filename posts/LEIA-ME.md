# Fila do Instagram

- `fila.json` lista os posts. A automação (Actions → "Publicar no Instagram") roda a cada 30 minutos
  e publica **só** os itens com `"status": "aprovado"` cujo `publicar_em` já passou.
- Para aprovar: edite `fila.json` no GitHub e troque `"aguardando_aprovacao"` por `"aprovado"` no post.
- Para adiar: mude `publicar_em` (formato `2026-12-02T12:00:00-03:00`).
- Para cancelar: troque o status para `"descartado"`.
- Depois de publicar, a automação grava `"status": "publicado"`, o link do post e a data.
  Se der erro, grava o motivo em `"erro"` e o GitHub te avisa por e-mail.
- `"selo_ia": true` marca os posts com o selo "Informações de IA" do Instagram.
