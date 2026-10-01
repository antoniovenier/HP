"""publicar_extra — as lacunas do YouTube (playlists, correção, conferência em lote,
legenda, cota) e do Facebook (agenda por API, comentários) que o PC ainda não tem.

O envio em si (YouTube `videos.insert`, Facebook foto/carrossel/reel/story/texto)
JÁ EXISTE no PC (hp_studio\\publicar\\) e não é refeito aqui. Tudo deste pacote
recebe o `cliente` do PC por injeção (contrato em contrato_pc.py) e um
`token_de(canal)`; nenhum módulo lê token nem faz rede por conta própria.
"""
import os.path as _op
import sys as _sys

_HP = _op.dirname(_op.dirname(_op.abspath(__file__)))
if _HP not in _sys.path:
    _sys.path.insert(0, _HP)
