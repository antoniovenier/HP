"""Plugins do --simular: não chamam NADA externo (nem ffmpeg, nem scripts,
nem fila da API/WhatsApp de verdade). Só criam arquivos de mentira com o
texto SIMULADO, para a esteira andar, mover e registrar tudo."""
from __future__ import annotations

from pathlib import Path

from hpbase import agora_iso, escrever_json, garantir

from .agendador import AgendadorFilaApi
from .aviso import AvisadorWhatsApp
from .plugins import Plugins

MARCA = "SIMULADO — arquivo de mentira gerado pela esteira em --simular\n"


def _falso(p: Path) -> Path:
    p = Path(p)
    garantir(p.parent)
    p.write_text(MARCA, encoding="utf-8")
    return p


class BaixadorSimulado:
    def baixar(self, url: str, destino: Path) -> Path:
        return _falso(Path(destino) / "bruto.mp4")


class MidiaSimulada:
    def info(self, arquivo: Path) -> dict:
        return {"duracao": 15.0, "largura": 1080, "altura": 1920, "fps": 30.0,
                "tem_video": True, "tem_audio": True, "codec_video": "simulado",
                "codec_audio": "simulado", "fonte": "simulado"}

    def extrair_audio(self, video: Path, saida: Path) -> Path:
        return _falso(saida)

    def quadros(self, video: Path, pasta: Path, largura: int = 540) -> list[dict]:
        nomes = ("quadro_1_inicio.jpg", "quadro_2_meio.jpg", "quadro_3_fim.jpg")
        return [{"arquivo": _falso(Path(pasta) / n).name, "segundo": t}
                for n, t in zip(nomes, (1.0, 7.5, 14.0))]

    def reduzir_imagem(self, imagem: Path, saida: Path, largura: int = 540) -> Path:
        return _falso(saida)

    def loudness(self, arquivo: Path) -> float | None:
        return -14.0


class LegendadorSimulado:
    def legendar(self, audio: Path, pasta: Path, idioma: str | None = None) -> Path:
        p = Path(pasta) / "legenda.srt"
        p.write_text("1\n00:00:00,000 --> 00:00:02,000\n(legenda simulada)\n",
                     encoding="utf-8")
        return p


class DubladorSimulado:
    def dublar(self, item: Path, legenda: Path, pedido: dict) -> Path:
        return _falso(Path(item) / "dublagem.wav")


class NarradorSimulado:
    def narrar(self, item: Path, roteiro: dict, duracao: float) -> Path:
        return _falso(Path(item) / "narracao.wav")


class EditorSimulado:
    def editar(self, item: Path, pedido: dict) -> dict:
        _falso(Path(item) / "final.mp4")
        _falso(Path(item) / "capa.jpg")
        dados = {"final": "final.mp4", "capa": "capa.jpg", "duracao": 15.0,
                 "largura": 1080, "altura": 1920, "fps": 30.0, "lufs": -14.0,
                 "alvo_lufs": -14.0, "legenda_queimada": True, "falas": 1,
                 "dublagem": bool(pedido.get("dublar")),
                 "narracao": bool(pedido.get("narrar_toque_hp")),
                 "simulado": True, "gerado_em": agora_iso()}
        escrever_json(Path(item) / "edicao.json", dados)
        return dados


class DesignerSimulado:
    def gerar(self, item: Path, pedido: dict) -> list[Path]:
        if pedido["tipo"] == "threads_texto":
            p = Path(item) / "texto_threads.txt"
            p.write_text(pedido["texto"], encoding="utf-8")
            return [p]
        n = max(1, len(pedido.get("laminas") or [])) if pedido["tipo"] == "carrossel" else 1
        return [_falso(Path(item) / "arte" / f"arte_{i:02d}.png") for i in range(1, n + 1)]


class AgendadorSimulado(AgendadorFilaApi):
    """Grava o que iria para a fila em esteira\\sombra\\fila_api (sem copiar
    mídia) e confirma na hora com status 'simulado'."""

    def __init__(self, cfg):
        super().__init__(cfg, forcar_sombra=True)

    def _midia(self, item: Path, post: dict):
        item = Path(item).resolve()
        capa = str(item / post["capa"]) if post.get("capa") else None
        return [str(item / a) for a in post["arquivos"]], capa

    def conferir(self, item, post, rede, registro):
        return {"status": "simulado", "link": None, "em": agora_iso(), "fonte": "--simular"}


def plugins_simulados(cfg) -> Plugins:
    return Plugins(
        baixador=BaixadorSimulado(),
        midia=MidiaSimulada(),
        legendador=LegendadorSimulado(),
        dublador=DubladorSimulado(),
        narrador=NarradorSimulado(),
        editor=EditorSimulado(),
        designer=DesignerSimulado(),
        agendador=AgendadorSimulado(cfg),
        avisador=AvisadorWhatsApp(cfg, forcar_sombra=True),
    )
