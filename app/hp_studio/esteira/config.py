"""Configuração da esteira (H:\\HypadoLocal\\esteira\\config.json).

Tudo tem valor padrão seguro: modo "sombra" (não publica nada de verdade) e
aviso "no ar" desligado. O arquivo config.json só precisa ter o que muda.
"""
from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from pathlib import Path

from hpbase import escrever_json, garantir, ler_json, raiz_drive, raiz_local

from .constantes import CRITERIO_ETAPA, TODAS_AS_PASTAS

# Modelos de comando dos scripts que já existem no PC. SUPOSIÇÃO: os
# parâmetros abaixo são o palpite da nuvem; se o script real usar outros
# nomes, ajuste só em config.json -> "comandos" (sem mexer no código).
# Marcadores: {python} {scripts} {url} {entrada} {saida} {item} {idioma}
COMANDOS_PADRAO = {
    "baixar": ["{python}", "{scripts}/ytdlp.py", "{url}", "--saida", "{saida}"],
    "dublar": ["{python}", "{scripts}/dublar.py", "--srt", "{entrada}",
               "--saida", "{saida}"],
    "falar": ["{python}", "{scripts}/dublar.py", "--texto-arquivo", "{entrada}",
              "--saida", "{saida}"],
    "estaticos": ["{python}", "{scripts}/estaticos.py", "--pedido", "{entrada}",
                  "--saida", "{saida}"],
}

EDITOR_PADRAO = {
    "largura": 1080,
    "altura": 1920,
    "fps": 30,
    "crf": 20,
    "preset": "medium",
    "lufs": -14.0,          # alvo de loudness (Instagram/TikTok/YouTube)
    "true_peak": -1.5,
    "lra": 11.0,
    "fundo": "desfoque",    # "desfoque" (fundo borrado) ou "preto"
    "fonte_legenda": "Arial",
    "tamanho_legenda": 68,
    "margem_legenda": 480,  # px do rodapé: fica acima dos botões do app
    "tamanho_credito": 40,
    "volume_original_com_dublagem": 0.12,
    "capa_segundo": 1.0,
    "bitrate_audio": "192k",
}

LEGENDADOR_PADRAO = {
    "modelo": "small",
    "dispositivo": "cpu",
    "tipo_computacao": "int8",
    "idioma": None,         # None = detecta sozinho
    "max_caracteres": 42,   # por linha de legenda (celular)
}

NARRADOR_PADRAO = {
    "abertura_max_s": 2.0,  # pergunta tem que caber nos 2 primeiros segundos
    "inicio_trecho_s": 2.3,
    "folga_fim_s": 0.3,
    "acelerar_max": 1.25,   # atempo máximo para caber a abertura
}

def _python_padrao() -> str:
    """python.exe (não pythonw.exe) para os subprocessos: o rodar() já usa
    CREATE_NO_WINDOW, então não abre janela, e o script tem stdout de verdade."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe" and (exe.parent / "python.exe").exists():
        return str(exe.parent / "python.exe")
    return str(exe)


TIMEOUTS_PADRAO = {
    "baixar": 1800,
    "dublar": 1800,
    "falar": 600,
    "estaticos": 600,
    "ffmpeg": 3600,        # edição do vídeo final
    "ffmpeg_curto": 300,   # narração, quadros, capa
}


@dataclass
class Config:
    raiz: Path
    modo: str = "sombra"                      # "sombra" | "real"
    aviso_no_ar_habilitado: bool = False      # decisão 30/09: o aviso "no ar" é do whatsapp_local
    p0_na_janela: bool = True                 # decisão 30/09: P0 roda também das 18h às 22h30
    grupo_whatsapp: str = "HP | Comissão 🚀"
    grupos_permitidos: list = field(default_factory=lambda: ["HP | Comissão 🚀"])
    max_voltas: int = 2
    max_tentativas: int = 3
    pasta_scripts: Path | None = None
    python: str = field(default_factory=_python_padrao)
    fila_api: Path | None = None
    whatsapp_fila: Path | None = None
    copiar_midia_para_fila: bool = True
    redes_api: list = field(default_factory=lambda: ["instagram", "threads",
                                                     "facebook", "youtube"])
    redes_manuais: list = field(default_factory=lambda: ["tiktok", "pinterest"])
    comandos: dict = field(default_factory=lambda: copy.deepcopy(COMANDOS_PADRAO))
    editor: dict = field(default_factory=lambda: dict(EDITOR_PADRAO))
    legendador: dict = field(default_factory=lambda: dict(LEGENDADOR_PADRAO))
    narrador: dict = field(default_factory=lambda: dict(NARRADOR_PADRAO))
    timeouts: dict = field(default_factory=lambda: dict(TIMEOUTS_PADRAO))
    criterio_etapa: dict = field(default_factory=lambda: dict(CRITERIO_ETAPA))
    largura_quadro_revisao: int = 540        # quadros menores = menos token
    arquivar_postados_dias: int = 7          # 07_postados -> _arquivo\AAAA-MM (0 = nunca)

    def __post_init__(self):
        self.raiz = Path(self.raiz)
        if self.pasta_scripts is None:
            self.pasta_scripts = raiz_drive() / "scripts"
        if self.fila_api is None:
            self.fila_api = raiz_local() / "fila_api"
        if self.whatsapp_fila is None:
            self.whatsapp_fila = raiz_local() / "whatsapp_fila"
        self.pasta_scripts = Path(self.pasta_scripts)
        self.fila_api = Path(self.fila_api)
        self.whatsapp_fila = Path(self.whatsapp_fila)
        if self.modo not in ("sombra", "real"):
            raise ValueError("config.modo tem que ser 'sombra' ou 'real'")

    # --- caminhos --------------------------------------------------------
    def pasta(self, etapa: str) -> Path:
        return self.raiz / etapa

    @property
    def pasta_sombra(self) -> Path:
        return self.raiz / "sombra"

    @property
    def arquivo_config(self) -> Path:
        return self.raiz / "config.json"

    @property
    def trava_vigia(self) -> Path:
        return self.raiz / ".vigia.lock"

    @property
    def real(self) -> bool:
        return self.modo == "real"

    def garantir_pastas(self) -> None:
        for p in TODAS_AS_PASTAS:
            garantir(self.pasta(p))

    def como_dict(self) -> dict:
        d = {}
        for k in ("modo", "aviso_no_ar_habilitado", "p0_na_janela", "grupo_whatsapp",
                  "grupos_permitidos", "max_voltas", "max_tentativas",
                  "copiar_midia_para_fila", "redes_api", "redes_manuais",
                  "comandos", "editor", "legendador", "narrador", "timeouts",
                  "criterio_etapa", "largura_quadro_revisao", "arquivar_postados_dias"):
            d[k] = copy.deepcopy(getattr(self, k))
        d["pasta_scripts"] = str(self.pasta_scripts)
        d["fila_api"] = str(self.fila_api)
        d["whatsapp_fila"] = str(self.whatsapp_fila)
        return d


_DICIONARIOS = ("comandos", "editor", "legendador", "narrador", "timeouts",
                "criterio_etapa")


def carregar_config(raiz: Path | None = None, **sobrepor) -> Config:
    """Lê esteira\\config.json (se existir) por cima dos padrões."""
    raiz = Path(raiz) if raiz else raiz_local() / "esteira"
    base = Config(raiz=raiz)
    dados = ler_json(raiz / "config.json", {}) or {}
    dados.update(sobrepor)
    for chave, valor in dados.items():
        if chave.startswith("_") or not hasattr(base, chave) or chave == "raiz":
            continue
        if chave in _DICIONARIOS and isinstance(valor, dict):
            atual = getattr(base, chave)
            atual.update(valor)
        else:
            setattr(base, chave, valor)
    base.__post_init__()
    return base


def salvar_config_padrao(cfg: Config) -> Path:
    """Grava config.json com todos os padrões (não sobrescreve se existir)."""
    p = cfg.arquivo_config
    if not p.exists():
        d = cfg.como_dict()
        d["_leia"] = ("modo: 'sombra' (padrão) não publica nada; 'real' grava na "
                      "fila_api. aviso_no_ar_habilitado só vale com modo 'real' — deixe false: "
                      "o aviso 'no ar' é montado pelo whatsapp_local. p0_na_janela: "
                      "P0 (urgente) roda também das 18h às 22h30, 1 pesado por vez.")
        escrever_json(p, d)
    return p
