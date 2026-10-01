"""Aviso "no ar" (sai de 07_postados) -> fila do WhatsApp.

Formato (1 JSON por mensagem, o mesmo que o enviador local vai ler):
  {"grupo": "HP | Comissão 🚀", "texto": "*Claude - * ...", "anexos": [],
   "tipo": "no_ar", "criado_em": "...", "origem": "hp_studio.esteira", "item": "..."}

Só vai para a fila de verdade (H:\\HypadoLocal\\whatsapp_fila\\) quando
config.modo == "real" E config.aviso_no_ar_habilitado == true. Fora disso
(padrão) é modo sombra: grava em esteira\\sombra\\whatsapp_fila\\ para comparar
com o que o plantão mandou.
"""
from __future__ import annotations

from pathlib import Path

from hpbase import agora_iso, escrever_json, garantir

from .erros import ErroPermanente

CABECALHO = "*Claude - *"
NOMES_REDES = {"instagram": "Instagram", "facebook": "Facebook", "tiktok": "TikTok",
               "youtube": "YouTube", "threads": "Threads", "pinterest": "Pinterest"}


def montar_aviso(post: dict, confirmacoes: dict, grupo: str) -> dict:
    linhas = [f"{CABECALHO} No ar: {post['titulo']}",
              f"{post.get('nome_canal', post['canal'])} ({post['conta']})"]
    for rede in post["redes"]:
        c = confirmacoes.get(rede) or {}
        linhas.append(f"{NOMES_REDES.get(rede, rede)}: {c.get('link') or c.get('status') or 'ok'}")
    return {"grupo": grupo, "texto": "\n".join(linhas), "anexos": [], "tipo": "no_ar",
            "criado_em": agora_iso(), "origem": "hp_studio.esteira", "item": post["item"]}


class AvisadorWhatsApp:
    def __init__(self, cfg, forcar_sombra: bool = False):
        self.cfg = cfg
        self.sombra = forcar_sombra or not (cfg.real and cfg.aviso_no_ar_habilitado)

    @property
    def pasta(self) -> Path:
        return self.cfg.pasta_sombra / "whatsapp_fila" if self.sombra \
            else Path(self.cfg.whatsapp_fila)

    def enviar(self, item: Path, mensagem: dict, nome_arquivo: str) -> tuple[Path, str]:
        if not str(mensagem.get("texto", "")).startswith(CABECALHO):
            raise ErroPermanente("mensagem de WhatsApp tem que começar com *Claude - *")
        if mensagem.get("grupo") not in self.cfg.grupos_permitidos:
            raise ErroPermanente(f"grupo '{mensagem.get('grupo')}' fora da lista permitida")
        p = garantir(self.pasta) / nome_arquivo
        escrever_json(p, mensagem)
        return p, ("sombra" if self.sombra else "na_fila")
