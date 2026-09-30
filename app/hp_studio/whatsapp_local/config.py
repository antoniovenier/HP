"""Constantes, caminhos e configuração do enviador local de WhatsApp.

Tudo que é "regra da empresa" para o WhatsApp mora aqui, num lugar só:
- toda mensagem começa com PREFIXO ("*Claude - *");
- WhatsApp só para 3 coisas (TIPOS_PERMITIDOS);
- só o grupo "HP | Comissão 🚀" e os grupos da lista "HP | Grupos"
  (arquivo grupos_permitidos.json, que o Antônio mantém);
- ritmo baixo: nunca menos de 20 s entre mensagens.

Pastas (no PC do Antônio; em teste o conftest troca a raiz):
  H:\\HypadoLocal\\whatsapp_perfil\\          perfil separado do navegador (login do QR)
  H:\\HypadoLocal\\whatsapp_fila\\            1 JSON por mensagem a enviar
      rejeitadas\\ enviadas\\ erros\\
  H:\\HypadoLocal\\whatsapp_local\\           config.json, grupos_permitidos.json,
      estado.json, ritmo.json, recebidas\\AAAA-MM-DD.jsonl
  H:\\HypadoLocal\\whatsapp_sombra\\          modo sombra
      app\\ (o que o app mandaria) plantao\\ (o que o plantão mandou) relatorios\\
  G:\\Meu Drive\\Hypado\\06 Projeto\\AVISO.md  texto-modelo do aviso "no ar"
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field, fields
from pathlib import Path

from hpbase import escrever_json, garantir, ler_json, raiz_drive, raiz_local

PREFIXO = "*Claude - *"
TIPOS_PERMITIDOS = ("resumo_dia", "no_ar", "resumo_sabado")
GRUPO_COMISSAO = "HP | Comissão 🚀"
URL_WHATSAPP = "https://web.whatsapp.com/"

INTERVALO_MIN_ABSOLUTO = 20      # segundos; ninguém baixa disso nem pela config
LIMITE_TEXTO = 4096              # caracteres por mensagem (bem abaixo do limite do app)
LIMITE_LEGENDA = 1000            # acima disso o texto vai separado do anexo
MAX_ANEXOS = 10

# Nome bonito dos canais (os ids vêm do módulo de métricas / esteira).
NOMES_CANAIS = {
    "gta": "GTA 6 | HP",
    "futebol": "Futebol | HP",
    "filmes": "Filmes e Séries | HP",
    "receitas": "Receitas | HP",
    "carros": "Carros | HP",
    "destinos": "Destinos | HP",
}
ORDEM_CANAIS = list(NOMES_CANAIS.values())


def nfc(texto) -> str:
    """Normaliza Unicode (NFC) e tira espaço das pontas.

    "Comissão" pode chegar com o "ã" em 1 ou 2 códigos (NFC x NFD); depois
    disto os dois viram o mesmo texto e a comparação fica exata.
    """
    return unicodedata.normalize("NFC", str(texto or "")).strip()


# ----------------------------------------------------------------- caminhos
def pasta_perfil() -> Path:
    return raiz_local() / "whatsapp_perfil"


def pasta_fila() -> Path:
    return raiz_local() / "whatsapp_fila"


def pasta_config() -> Path:
    return raiz_local() / "whatsapp_local"


def pasta_recebidas() -> Path:
    return pasta_config() / "recebidas"


def pasta_sombra() -> Path:
    return raiz_local() / "whatsapp_sombra"


def pasta_sombra_app() -> Path:
    return pasta_sombra() / "app"


def pasta_sombra_plantao() -> Path:
    return pasta_sombra() / "plantao"


def pasta_sombra_relatorios() -> Path:
    return pasta_sombra() / "relatorios"


def arquivo_config() -> Path:
    return pasta_config() / "config.json"


def arquivo_grupos() -> Path:
    return pasta_config() / "grupos_permitidos.json"


def arquivo_estado() -> Path:
    return pasta_config() / "estado.json"


def arquivo_ritmo() -> Path:
    return pasta_config() / "ritmo.json"


def arquivo_trava() -> Path:
    return pasta_config() / "enviador.lock"


def arquivo_modelo_aviso() -> Path:
    return raiz_drive() / "06 Projeto" / "AVISO.md"


MODELO_EXEMPLO = Path(__file__).with_name("AVISO.md")


def candidatos_metricas() -> list[Path]:
    """Onde procurar o metricas_painel.json (o primeiro que existir vale)."""
    return [
        raiz_local() / "metricas" / "metricas_painel.json",
        raiz_local() / "app" / "metricas_painel.json",
        raiz_drive() / "06 Projeto" / "metricas_painel.json",
        raiz_drive() / "06 Projeto" / "app" / "metricas_painel.json",
    ]


# ------------------------------------------------------------ configuração
@dataclass
class Config:
    modo: str = "sombra"                 # "sombra" (padrão) ou "real"
    max_por_hora: int = 10               # teto de mensagens por hora
    intervalo_min_seg: float = 20        # nunca menos de 20 s
    max_tentativas: int = 3              # depois disso vai para erros\
    canal_navegador: str | None = None   # None = Chromium do Playwright; "chrome" = Chrome instalado
    ler_recebidas: bool = True           # salvar mensagens novas do Antônio
    ler_recebidas_a_cada_min: int = 30   # no vigiar, passa em todos os grupos
    ultimas_mensagens: int = 20          # quantas mensagens ler por conversa
    timeout_login_seg: int = 300         # quanto o comando login espera o QR
    timeout_carregar_seg: int = 90       # quanto espera o WhatsApp Web carregar
    grupo_padrao: str = GRUPO_COMISSAO   # para onde vão avisos/resumos sem grupo
    grupo_por_canal: dict = field(default_factory=dict)  # {"GTA 6 | HP": "HP | GTA 6"}
    arquivo_agendados: str | None = None # se preenchido, o vigiar monta o "no ar" sozinho
    janela_no_ar_horas: int = 24         # posts mais velhos que isso não viram aviso
    hora_resumo_dia: str | None = None   # "08:00" = o vigiar monta o resumo de ontem
    hora_resumo_sabado: str | None = None  # "10:00" = o vigiar monta o resumo no sábado
    arquivo_metricas: str | None = None  # caminho do metricas_painel.json (senão procura)

    def __post_init__(self):
        self.modo = str(self.modo or "sombra").strip().lower()
        if self.modo not in ("sombra", "real"):
            self.modo = "sombra"          # na dúvida, o seguro
        try:
            self.intervalo_min_seg = max(float(INTERVALO_MIN_ABSOLUTO),
                                         float(self.intervalo_min_seg))
        except (TypeError, ValueError):
            self.intervalo_min_seg = float(INTERVALO_MIN_ABSOLUTO)
        self.max_por_hora = max(1, int(self.max_por_hora or 1))
        self.max_tentativas = max(1, int(self.max_tentativas or 3))
        self.ultimas_mensagens = max(1, int(self.ultimas_mensagens or 20))
        if not isinstance(self.grupo_por_canal, dict):
            self.grupo_por_canal = {}


CONFIG_EXEMPLO = {
    "_leia": ("Configuração do enviador local de WhatsApp. 'modo': 'sombra' "
              "(só monta e compara, não abre o navegador) ou 'real' (envia). "
              "Intervalo mínimo nunca fica abaixo de 20 s."),
    **{f.name: (f.default_factory() if callable(f.default_factory) else f.default)  # type: ignore[misc]
       for f in fields(Config)},
}

GRUPOS_EXEMPLO = {
    "_leia": ("Lista 'HP | Grupos': nomes EXATOS dos grupos do WhatsApp que "
              "podem receber mensagem (copie o nome como aparece no topo da "
              "conversa, com emoji). 'HP | Comissão 🚀' é sempre permitido. "
              "Nunca coloque contato individual aqui."),
    "grupos": [],
}


def carregar_config(caminho: Path | None = None) -> Config:
    dados = ler_json(Path(caminho) if caminho else arquivo_config(), {}) or {}
    if not isinstance(dados, dict):
        dados = {}
    validos = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in dados.items() if k in validos})


def carregar_grupos_permitidos(caminho: Path | None = None) -> list[str]:
    """'HP | Comissão 🚀' + a lista do Antônio (sem repetição, tudo em NFC).

    Aceita `{"grupos": [...]}` ou só a lista `[...]`. Arquivo quebrado =
    só a Comissão (falha para o lado seguro).
    """
    try:
        dados = ler_json(Path(caminho) if caminho else arquivo_grupos(), [])
    except Exception:
        dados = []
    lista = dados.get("grupos", []) if isinstance(dados, dict) else dados
    if not isinstance(lista, list):
        lista = []
    saida: list[str] = []
    for g in [GRUPO_COMISSAO, *lista]:
        if isinstance(g, str) and nfc(g) and nfc(g) not in saida:
            saida.append(nfc(g))
    return saida


def preparar_pastas() -> None:
    """Cria as pastas e, se faltarem, o config.json e o grupos_permitidos.json
    de exemplo (nunca sobrescreve o que o Antônio já editou)."""
    from .fila import Fila  # import aqui para não criar ciclo
    Fila().preparar()
    for p in (pasta_config(), pasta_recebidas(), pasta_sombra_app(),
              pasta_sombra_plantao(), pasta_sombra_relatorios()):
        garantir(p)
    if not arquivo_config().exists():
        escrever_json(arquivo_config(), CONFIG_EXEMPLO)
    if not arquivo_grupos().exists():
        escrever_json(arquivo_grupos(), GRUPOS_EXEMPLO)
