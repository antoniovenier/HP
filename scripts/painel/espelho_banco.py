"""Espelho local do banco do painel público (substitui o ArtifactData nas rotinas).

Por que existe: a ferramenta ArtifactData trava rotinas. Com este espelho a
rotina do painel lê e grava tudo num SQLite local e, no fim, exporta um único
`painel_dados.json`, que o `montar_painel_publico.py` publica junto do HTML
(como o `dados.json` de hoje) ou embute dentro do HTML no build.
Nenhuma chamada de rede, nenhum segredo.

Banco:   <HP_LOCAL>/app/painel_espelho.sqlite   (H:\\HypadoLocal\\app\\...)
Tabela:  docs(colecao, doc_id, dados JSON, atualizado_em, versao)

API (mesmos nomes do ArtifactData):
    b = EspelhoBanco()
    b.set("canais", "gta", {...})         substitui o documento
    b.update("canais", "gta", {...})      junta campos (cria se não existir)
    b.get("canais", "gta")                -> dados ou None
    b.list("canais")                      -> [{"id", "dados", "versao", "atualizado_em"}]
    b.query("agenda", {"status": "postado"}, ordenar="hora")
    b.delete("canais", "gta")             -> True/False
    b.batch([{"op": "set", ...}, ...])    tudo ou nada (rollback se algo falhar)
    b.exportar()                          -> grava painel_dados.json
    b.importar("export.json")             -> lê o export que o Claude fez 1 vez

Idempotente: gravar o mesmo conteúdo de novo não muda versão nem data; importar
o mesmo arquivo duas vezes deixa o banco igual; exportar sem mudança gera a
mesma "assinatura" (a rotina pode pular a publicação).

CLI (PowerShell):
    python scripts\\painel\\espelho_banco.py importar x.json
    python scripts\\painel\\espelho_banco.py exportar
    python scripts\\painel\\espelho_banco.py set colecao id '{\\"campo\\": 1}'
    python scripts\\painel\\espelho_banco.py listar colecao
    python scripts\\painel\\espelho_banco.py --help
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import html as _html
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


# --------------------------------------------------------------------------
# hpbase: ../app/hp_studio_nuvem (repositório), ../06 Projeto/app/hp_studio_nuvem (PC)
# ou a pasta indicada em HP_APP.
# --------------------------------------------------------------------------
def _preparar_hpbase() -> None:
    aqui = Path(__file__).resolve().parent
    candidatos: list[Path] = []
    env = os.environ.get("HP_APP")
    if env:
        candidatos += [Path(env), Path(env) / "hp_studio_nuvem", Path(env) / "hp_studio"]
    scripts = aqui.parent
    candidatos += [scripts.parent / "app" / "hp_studio_nuvem",
                   scripts.parent / "06 Projeto" / "app" / "hp_studio_nuvem",
                   scripts.parent / "app" / "hp_studio",
                   scripts.parent / "06 Projeto" / "app" / "hp_studio"]
    for c in candidatos:
        if (c / "hpbase" / "__init__.py").exists():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            return


_preparar_hpbase()
from hpbase import agora_iso, escrever_json, ler_json, obter_logger, pasta_app  # noqa: E402

FORMATO = "hp-painel-espelho/1"
NOME_BANCO = "painel_espelho.sqlite"
NOME_EXPORT = "painel_dados.json"
# chaves de topo do export que NÃO são coleções
RESERVADAS = {"gerado", "_espelho", "formato", "dias"}
_NOME_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,63}$")

# o painel é PÚBLICO: nada com cara de segredo pode entrar no espelho
_CHAVES_PROIBIDAS = {"access_token", "refresh_token", "token", "senha", "password",
                     "secret", "client_secret", "api_key", "apikey", "authorization"}
_PADROES_SEGREDO = [
    re.compile(r"\bEAA[A-Za-z0-9]{20,}"),              # token da Meta
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),          # chave Google
    re.compile(r"\bya29\.[0-9A-Za-z_\-]{10,}"),        # OAuth Google
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{10,}", re.I),
    re.compile(r"access_token=[^&\s\"']+", re.I),
]
_DATA_URI = re.compile(r"data:[\w/+.\-]+;base64,[A-Za-z0-9+/=]+")

_SQL_CRIAR = """
CREATE TABLE IF NOT EXISTS docs (
    colecao      TEXT    NOT NULL,
    doc_id       TEXT    NOT NULL,
    dados        TEXT    NOT NULL,
    atualizado_em TEXT   NOT NULL,
    versao       INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (colecao, doc_id)
);
CREATE INDEX IF NOT EXISTS docs_colecao ON docs(colecao);
"""


class ErroEspelho(ValueError):
    """Operação inválida no espelho (nada foi gravado)."""


class SegredoNoDado(ErroEspelho):
    """Tentativa de gravar algo com cara de token/senha no painel público."""


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------
def caminho_banco() -> Path:
    return pasta_app() / NOME_BANCO


def caminho_export() -> Path:
    return pasta_app() / NOME_EXPORT


def _canonico(dados: Any) -> str:
    """JSON sempre igual para o mesmo conteúdo (ordem das chaves fixa)."""
    try:
        return json.dumps(dados, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as e:
        raise ErroEspelho(f"dados não são JSON válido: {e}") from None


def _validar_nome(tipo: str, nome: Any) -> str:
    if not isinstance(nome, str) or not nome.strip():
        raise ErroEspelho(f"{tipo} vazio")
    if tipo == "coleção" and (not _NOME_OK.match(nome) or nome in RESERVADAS):
        raise ErroEspelho(f"nome de coleção inválido: {nome!r} "
                          "(use letras, números, _ . -; reservados: "
                          + ", ".join(sorted(RESERVADAS)) + ")")
    if tipo == "id" and len(nome) > 200:
        raise ErroEspelho("id com mais de 200 caracteres")
    return nome


def _procurar_chave_proibida(obj: Any, caminho: str = "") -> str | None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).strip().lower() in _CHAVES_PROIBIDAS and v not in (None, "", [], {}):
                return f"{caminho}.{k}" if caminho else str(k)
            achou = _procurar_chave_proibida(v, f"{caminho}.{k}" if caminho else str(k))
            if achou:
                return achou
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            achou = _procurar_chave_proibida(v, f"{caminho}[{i}]")
            if achou:
                return achou
    return None


def verificar_sem_segredo(dados: Any, texto: str | None = None) -> None:
    """Levanta SegredoNoDado se houver chave ou valor com cara de segredo.

    A mensagem nunca mostra o valor, só onde está. Imagens em data: URI são
    ignoradas (base64 pode formar "EAA..." por acaso).
    """
    onde = _procurar_chave_proibida(dados)
    if onde:
        raise SegredoNoDado(f"campo com nome de segredo no painel público: {onde}")
    s = _DATA_URI.sub("", texto if texto is not None else _canonico(dados))
    for rx in _PADROES_SEGREDO:
        if rx.search(s):
            raise SegredoNoDado("valor com cara de token/chave no painel público "
                                "(removido; confira a origem dos dados)")


def _pegar(d: Any, caminho: str) -> Any:
    """Lê campo com ponto: "redes.instagram.seguidores"."""
    atual = d
    for parte in caminho.split("."):
        if isinstance(atual, dict) and parte in atual:
            atual = atual[parte]
        elif isinstance(atual, list) and parte.isdigit() and int(parte) < len(atual):
            atual = atual[int(parte)]
        else:
            return None
    return atual


def _combina(valor: Any, cond: Any) -> bool:
    if isinstance(cond, dict) and cond and all(str(k).startswith("$") for k in cond):
        for op, alvo in cond.items():
            try:
                if op == "$eq" and not valor == alvo:
                    return False
                if op == "$ne" and not valor != alvo:
                    return False
                if op == "$gt" and not (valor is not None and valor > alvo):
                    return False
                if op == "$gte" and not (valor is not None and valor >= alvo):
                    return False
                if op == "$lt" and not (valor is not None and valor < alvo):
                    return False
                if op == "$lte" and not (valor is not None and valor <= alvo):
                    return False
                if op == "$in" and valor not in alvo:
                    return False
                if op == "$nin" and valor in alvo:
                    return False
                if op == "$existe" and (valor is not None) != bool(alvo):
                    return False
                if op == "$contem":
                    if isinstance(valor, (list, tuple)):
                        if alvo not in valor:
                            return False
                    elif not (isinstance(valor, str) and str(alvo).lower() in valor.lower()):
                        return False
            except TypeError:  # comparar texto com número, etc.
                return False
            if op not in {"$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", "$nin",
                          "$existe", "$contem"}:
                raise ErroEspelho(f"operador desconhecido na consulta: {op}")
        return True
    return valor == cond


def _juntar(base: Any, novo: dict, profundo: bool) -> dict:
    res = copy.deepcopy(base) if isinstance(base, dict) else {}
    for k, v in novo.items():
        if profundo and isinstance(v, dict) and isinstance(res.get(k), dict):
            res[k] = _juntar(res[k], v, True)
        else:
            res[k] = copy.deepcopy(v)
    return res


# --------------------------------------------------------------------------
# importação: aceita vários formatos de export
# --------------------------------------------------------------------------
_CH_COLECAO = ("colecao", "collection", "coleção")
_CH_ID = ("doc_id", "id", "_id", "docId", "key", "chave")
_CH_DADOS = ("dados", "data", "doc", "document", "value", "valor")


def _doc_de_registro(reg: dict) -> tuple[str, Any] | None:
    doc_id = next((reg[k] for k in _CH_ID if k in reg and reg[k] not in (None, "")), None)
    if doc_id is None:
        return None
    for k in _CH_DADOS:
        if k in reg:
            return str(doc_id), reg[k]
    resto = {k: v for k, v in reg.items() if k not in _CH_ID and k not in _CH_COLECAO}
    return str(doc_id), resto


def normalizar_export(obj: Any) -> tuple[list[tuple[str, str, Any]], list[str]]:
    """Transforma qualquer formato aceito em [(colecao, doc_id, dados)].

    Formatos aceitos:
      1. o próprio painel_dados.json (e o dados.json do painel de hoje):
         {"colecao": {"doc_id": dados}, "gerado": ..., "_espelho": ...}
      2. {"colecoes": {...}} ou {"collections": {...}}
      3. coleção como lista: {"colecao": [{"id": "x", ...}, {"doc_id": "y", "data": {...}}]}
         ou {"colecao": {"documents": [...]}}
      4. lista de registros: [{"collection": "c", "doc_id": "x", "data": {...}}]
    Devolve também a lista do que foi ignorado (com o motivo).
    """
    docs: list[tuple[str, str, Any]] = []
    ignorados: list[str] = []

    if isinstance(obj, list):
        for i, reg in enumerate(obj):
            if not isinstance(reg, dict):
                ignorados.append(f"[{i}] não é objeto")
                continue
            col = next((reg[k] for k in _CH_COLECAO if k in reg), None)
            par = _doc_de_registro(reg)
            if not col or par is None:
                ignorados.append(f"[{i}] sem coleção ou id")
                continue
            docs.append((str(col), par[0], par[1]))
        return docs, ignorados

    if not isinstance(obj, dict):
        raise ErroEspelho("o arquivo não tem objeto nem lista no topo")

    for chave in ("colecoes", "collections"):
        if isinstance(obj.get(chave), dict):
            obj = obj[chave]
            break

    for col, valor in obj.items():
        if col in RESERVADAS:
            ignorados.append(f"{col} (chave reservada, não é coleção)")
            continue
        if isinstance(valor, dict) and isinstance(valor.get("documents"), list) \
                and len(valor) <= 3:
            valor = valor["documents"]
        if isinstance(valor, dict):
            for doc_id, dados in valor.items():
                docs.append((col, str(doc_id), dados))
        elif isinstance(valor, list):
            pulados = 0
            for reg in valor:
                par = _doc_de_registro(reg) if isinstance(reg, dict) else None
                if par is None:
                    pulados += 1
                    continue
                docs.append((col, par[0], par[1]))
            if pulados:
                ignorados.append(f"{col}: {pulados} item(ns) sem id")
        else:
            ignorados.append(f"{col} (valor solto, não é coleção)")
    return docs, ignorados


# --------------------------------------------------------------------------
# o espelho
# --------------------------------------------------------------------------
class EspelhoBanco:
    """Banco de coleções/documentos em SQLite, com a API do ArtifactData."""

    def __init__(self, caminho: str | Path | None = None,
                 relogio: Callable[[], str] = agora_iso):
        self.caminho = Path(caminho) if caminho else caminho_banco()
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._relogio = relogio
        self._con = sqlite3.connect(str(self.caminho), timeout=10,
                                    isolation_level=None)  # transação manual
        self._con.execute("PRAGMA busy_timeout = 10000")
        self._con.executescript(_SQL_CRIAR)
        self._em_transacao = False
        self._log = obter_logger("painel_espelho")

    # ---- ciclo de vida ----------------------------------------------------
    def fechar(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None  # type: ignore[assignment]

    def __enter__(self) -> "EspelhoBanco":
        return self

    def __exit__(self, *exc) -> bool:
        self.fechar()
        return False

    @contextlib.contextmanager
    def transacao(self) -> Iterator["EspelhoBanco"]:
        """Tudo dentro do bloco grava junto; qualquer erro desfaz tudo."""
        if self._em_transacao:  # aninhada: participa da de fora
            yield self
            return
        self._con.execute("BEGIN IMMEDIATE")
        self._em_transacao = True
        try:
            yield self
        except BaseException:
            self._con.execute("ROLLBACK")
            raise
        else:
            self._con.execute("COMMIT")
        finally:
            self._em_transacao = False

    # ---- leitura ------------------------------------------------------------
    def _linha(self, colecao: str, doc_id: str):
        return self._con.execute(
            "SELECT dados, atualizado_em, versao FROM docs WHERE colecao=? AND doc_id=?",
            (colecao, doc_id)).fetchone()

    def get(self, colecao: str, doc_id: str) -> Any:
        """Dados do documento (ou None se não existir)."""
        lin = self._linha(colecao, str(doc_id))
        return json.loads(lin[0]) if lin else None

    def registro(self, colecao: str, doc_id: str) -> dict | None:
        lin = self._linha(colecao, str(doc_id))
        if not lin:
            return None
        return {"id": str(doc_id), "dados": json.loads(lin[0]),
                "atualizado_em": lin[1], "versao": lin[2]}

    def list(self, colecao: str, limite: int | None = None,
             apos: str | None = None) -> list[dict]:
        """Documentos da coleção em ordem de id: [{"id","dados","versao","atualizado_em"}].

        Paginação: passe o último id recebido em `apos`.
        """
        sql = "SELECT doc_id, dados, atualizado_em, versao FROM docs WHERE colecao=?"
        args: list[Any] = [colecao]
        if apos is not None:
            sql += " AND doc_id > ?"
            args.append(str(apos))
        sql += " ORDER BY doc_id"
        if limite:
            sql += " LIMIT ?"
            args.append(int(limite))
        return [{"id": d, "dados": json.loads(j), "atualizado_em": a, "versao": v}
                for d, j, a, v in self._con.execute(sql, args)]

    def query(self, colecao: str, filtro: dict | None = None,
              ordenar: str | None = None, desc: bool = False,
              limite: int | None = None) -> list[dict]:
        """Filtra por campos (ponto para campo dentro de campo).

        filtro = {"status": "postado", "hora": {"$gte": "12:00"},
                  "redes": {"$contem": "tiktok"}}
        Operadores: $eq $ne $gt $gte $lt $lte $in $nin $existe $contem.
        """
        filtro = filtro or {}
        res = []
        for reg in self.list(colecao):
            d = reg["dados"]
            if all(_combina(_pegar(d, campo), cond) for campo, cond in filtro.items()):
                res.append(reg)
        if ordenar:
            chave = ordenar

            def k(r: dict):
                v = _pegar(r["dados"], chave)
                return (v is None, str(type(v).__name__), v if v is not None else 0)
            try:
                res.sort(key=k, reverse=desc)
            except TypeError:
                res.sort(key=lambda r: str(_pegar(r["dados"], chave)), reverse=desc)
        return res[:limite] if limite else res

    def colecoes(self) -> list[dict]:
        return [{"colecao": c, "total": n, "atualizado_em": a}
                for c, n, a in self._con.execute(
                    "SELECT colecao, COUNT(*), MAX(atualizado_em) FROM docs "
                    "GROUP BY colecao ORDER BY colecao")]

    def tudo(self) -> dict[str, dict[str, Any]]:
        """{colecao: {doc_id: dados}} de todo o banco."""
        out: dict[str, dict[str, Any]] = {}
        for c, d, j in self._con.execute(
                "SELECT colecao, doc_id, dados FROM docs ORDER BY colecao, doc_id"):
            out.setdefault(c, {})[d] = json.loads(j)
        return out

    # ---- escrita ------------------------------------------------------------
    def _gravar(self, colecao: str, doc_id: str, dados: Any) -> dict:
        _validar_nome("coleção", colecao)
        _validar_nome("id", doc_id)
        texto = _canonico(dados)
        verificar_sem_segredo(dados, texto)
        lin = self._linha(colecao, doc_id)
        if lin and lin[0] == texto:  # idempotente: nada mudou
            return {"id": doc_id, "versao": lin[2], "mudou": False}
        versao = (lin[2] + 1) if lin else 1
        self._con.execute(
            "INSERT INTO docs(colecao, doc_id, dados, atualizado_em, versao) "
            "VALUES (?,?,?,?,?) ON CONFLICT(colecao, doc_id) DO UPDATE SET "
            "dados=excluded.dados, atualizado_em=excluded.atualizado_em, "
            "versao=excluded.versao",
            (colecao, doc_id, texto, self._relogio(), versao))
        return {"id": doc_id, "versao": versao, "mudou": True}

    def set(self, colecao: str, doc_id: str, dados: Any) -> dict:
        """Substitui o documento inteiro (cria se não existir)."""
        with self.transacao():
            return self._gravar(colecao, str(doc_id), dados)

    def update(self, colecao: str, doc_id: str, dados: dict,
               profundo: bool = False, criar: bool = True) -> dict:
        """Junta os campos de `dados` no documento (raso; profundo=True junta
        também os objetos de dentro). Cria o documento se não existir."""
        if not isinstance(dados, dict):
            raise ErroEspelho("update precisa de um objeto {campo: valor}")
        with self.transacao():
            atual = self.get(colecao, str(doc_id))
            if atual is None and not criar:
                raise ErroEspelho(f"documento não existe: {colecao}/{doc_id}")
            if atual is not None and not isinstance(atual, dict):
                raise ErroEspelho(f"{colecao}/{doc_id} não é objeto; use set")
            return self._gravar(colecao, str(doc_id), _juntar(atual, dados, profundo))

    def delete(self, colecao: str, doc_id: str) -> bool:
        with self.transacao():
            cur = self._con.execute("DELETE FROM docs WHERE colecao=? AND doc_id=?",
                                    (colecao, str(doc_id)))
            return cur.rowcount > 0

    def limpar_colecao(self, colecao: str) -> int:
        with self.transacao():
            return self._con.execute("DELETE FROM docs WHERE colecao=?",
                                     (colecao,)).rowcount

    def batch(self, operacoes: Iterable[dict]) -> list[dict]:
        """Várias operações numa transação só: ou tudo grava, ou nada grava.

        Cada operação: {"op": "set"|"update"|"delete", "colecao": ..., "doc_id": ...,
        "dados": {...}, "profundo": false}. Também aceita os nomes em inglês
        (action, collection, id, data).
        """
        ops = list(operacoes)
        res: list[dict] = []
        with self.transacao():
            for i, o in enumerate(ops):
                if not isinstance(o, dict):
                    raise ErroEspelho(f"operação {i}: não é objeto")
                op = str(o.get("op") or o.get("action") or o.get("acao") or "").lower()
                col = next((o[k] for k in _CH_COLECAO if k in o), None)
                doc_id = next((o[k] for k in _CH_ID if k in o), None)
                dados = next((o[k] for k in _CH_DADOS if k in o), None)
                if not col or doc_id in (None, ""):
                    raise ErroEspelho(f"operação {i}: falta coleção ou id")
                if op == "set":
                    res.append(self.set(col, doc_id, dados))
                elif op in ("update", "merge"):
                    res.append(self.update(col, doc_id, dados,
                                           profundo=bool(o.get("profundo"))))
                elif op in ("delete", "apagar"):
                    res.append({"id": str(doc_id), "apagado": self.delete(col, doc_id)})
                else:
                    raise ErroEspelho(f"operação {i}: tipo desconhecido {op!r}")
        self._log.info("batch com %d operações gravado", len(ops))
        return res

    # ---- importar / exportar ------------------------------------------------
    def importar(self, origem: str | Path | Any, substituir: bool = False) -> dict:
        """Importa um export (arquivo ou objeto já lido). Transacional.

        substituir=True apaga antes as coleções que vierem no arquivo (para o
        espelho ficar exatamente igual ao export).
        """
        obj = ler_json(Path(origem)) if isinstance(origem, (str, Path)) else origem
        if obj is None:
            raise ErroEspelho(f"arquivo não encontrado: {origem}")
        docs, ignorados = normalizar_export(obj)
        mudaram = 0
        with self.transacao():
            if substituir:
                for col in sorted({c for c, _, _ in docs}):
                    self._con.execute("DELETE FROM docs WHERE colecao=?", (col,))
            for col, doc_id, dados in docs:
                if self._gravar(col, doc_id, dados)["mudou"]:
                    mudaram += 1
        res = {"documentos": len(docs), "mudaram": mudaram,
               "colecoes": sorted({c for c, _, _ in docs}), "ignorados": ignorados}
        self._log.info("importar: %d docs (%d mudaram), %d coleções, ignorados=%s",
                       len(docs), mudaram, len(res["colecoes"]), ignorados)
        return res

    def assinatura(self) -> str:
        """Impressão digital do conteúdo (muda só quando algum dado muda)."""
        return hashlib.sha256(_canonico(self.tudo()).encode("utf-8")).hexdigest()[:16]

    def montar_export(self, gerado: str | None = None) -> dict:
        tudo = self.tudo()
        atualizadas = {c["colecao"]: c["atualizado_em"] for c in self.colecoes()}
        dados: dict[str, Any] = {"gerado": gerado or agora_iso()}
        dados.update(tudo)
        dados["_espelho"] = {
            "formato": FORMATO,
            "assinatura": hashlib.sha256(_canonico(tudo).encode("utf-8")).hexdigest()[:16],
            "total_documentos": sum(len(v) for v in tudo.values()),
            "colecoes_atualizadas": atualizadas,
        }
        return dados

    def exportar(self, destino: str | Path | None = None,
                 gerado: str | None = None) -> dict:
        """Grava painel_dados.json (atômico). Devolve {caminho, assinatura, mudou}.

        `mudou` compara a assinatura com a do arquivo que já estava lá: se for
        False, a rotina não precisa republicar o painel.
        """
        destino = Path(destino) if destino else caminho_export()
        anterior = ler_json(destino, padrao={}) or {}
        ass_ant = (anterior.get("_espelho") or {}).get("assinatura") \
            if isinstance(anterior, dict) else None
        dados = self.montar_export(gerado)
        ass = dados["_espelho"]["assinatura"]
        escrever_json(destino, dados)
        self._log.info("exportar: %d documentos -> %s (mudou=%s)",
                       dados["_espelho"]["total_documentos"], destino.name, ass != ass_ant)
        return {"caminho": str(destino), "assinatura": ass, "mudou": ass != ass_ant,
                "documentos": dados["_espelho"]["total_documentos"]}

    def comparar(self, origem: str | Path | Any) -> dict:
        """Modo sombra: compara o espelho com um export do banco de verdade."""
        obj = ler_json(Path(origem)) if isinstance(origem, (str, Path)) else origem
        docs, _ = normalizar_export(obj)
        arquivo = {(c, d): _canonico(v) for c, d, v in docs}
        cols = {c for c, _ in arquivo}
        meu = {(c, d): _canonico(v) for c, m in self.tudo().items() if c in cols
               for d, v in m.items()}
        so_arq = sorted(f"{c}/{d}" for c, d in arquivo.keys() - meu.keys())
        so_meu = sorted(f"{c}/{d}" for c, d in meu.keys() - arquivo.keys())
        dif = sorted(f"{c}/{d}" for c, d in arquivo.keys() & meu.keys()
                     if arquivo[(c, d)] != meu[(c, d)])
        return {"iguais": not (so_arq or so_meu or dif), "so_no_arquivo": so_arq,
                "so_no_espelho": so_meu, "diferentes": dif,
                "conferidos": len(arquivo)}


# --------------------------------------------------------------------------
# embutir os dados no HTML (build do painel, sem chamada em tempo de execução)
# --------------------------------------------------------------------------
ID_BLOCO_DADOS = "painel-dados"


def json_para_script(dados: Any) -> str:
    """JSON seguro para ficar dentro de <script> (nunca fecha a tag por engano)."""
    s = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("<", "\\u003c").replace(">", "\\u003e")
             .replace("&", "\\u0026").replace("\u2028", "\\u2028")
             .replace("\u2029", "\\u2029"))


def embutir_no_html(html: str, dados: Any, id_bloco: str = ID_BLOCO_DADOS) -> str:
    """Coloca/atualiza <script type="application/json" id="painel-dados"> no HTML.

    Idempotente: se o bloco já existe, é trocado. Se houver o marcador
    <!--PAINEL_DADOS--> ele é usado; senão entra antes do primeiro <script>
    (para já existir quando o código do painel rodar) ou no fim.
    No JavaScript do painel:
        const DADOS = JSON.parse(document.getElementById("painel-dados").textContent);
    """
    bloco = (f'<script type="application/json" id="{_html.escape(id_bloco)}">'
             f"{json_para_script(dados)}</script>")
    rx = re.compile(r'<script type="application/json" id="' + re.escape(id_bloco)
                    + r'">.*?</script>', re.S)
    if rx.search(html):
        return rx.sub(lambda _m: bloco, html, count=1)
    if "<!--PAINEL_DADOS-->" in html:
        return html.replace("<!--PAINEL_DADOS-->", bloco, 1)
    m = re.search(r"<script\b", html, re.I)
    if m:
        return html[:m.start()] + bloco + "\n" + html[m.start():]
    return html + "\n" + bloco + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
class _Formato(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix or "uso: ")


def _parser_pt(**kw) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False, formatter_class=_Formato, **kw)
    p._positionals.title = "argumentos"
    p._optionals.title = "opções"
    p.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    return p


def _ler_json_arg(texto: str | None, arquivo: str | None) -> Any:
    if arquivo:
        if arquivo == "-":
            return json.loads(sys.stdin.read())
        return json.loads(Path(arquivo).read_text(encoding="utf-8-sig"))
    if texto is None:
        raise ErroEspelho("faltou o JSON (ou use --arquivo)")
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        raise ErroEspelho(
            "JSON inválido. No PowerShell 5.1 as aspas somem: escreva "
            "'{\\\"campo\\\": 1}' ou grave num arquivo e use --arquivo") from None


def _imprimir(obj: Any) -> None:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    p = _parser_pt(prog="espelho_banco.py",
                   description="Espelho local do banco do painel público (sem ArtifactData).",
                   epilog="Exemplos:\n"
                          "  python scripts\\painel\\espelho_banco.py importar export.json\n"
                          "  python scripts\\painel\\espelho_banco.py exportar\n"
                          "  python scripts\\painel\\espelho_banco.py set canais gta --arquivo gta.json\n"
                          "  python scripts\\painel\\espelho_banco.py listar canais")
    p.add_argument("--banco", help="arquivo SQLite (padrão: H:\\HypadoLocal\\app\\painel_espelho.sqlite)")
    sub = p.add_subparsers(dest="cmd", metavar="comando", title="comandos")

    def novo(nome: str, ajuda: str) -> argparse.ArgumentParser:
        sp = sub.add_parser(nome, help=ajuda, description=ajuda, add_help=False,
                            formatter_class=_Formato)
        sp._positionals.title = "argumentos"
        sp._optionals.title = "opções"
        sp.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
        return sp

    s = novo("importar", "importa um export JSON (feito 1 vez pela sessão do Claude)")
    s.add_argument("arquivo")
    s.add_argument("--substituir", action="store_true",
                   help="apaga antes as coleções que vierem no arquivo")
    s = novo("exportar", "grava painel_dados.json com tudo")
    s.add_argument("--saida", help="arquivo de saída (padrão: H:\\HypadoLocal\\app\\painel_dados.json)")
    for nome, ajuda in (("set", "substitui um documento"), ("update", "junta campos num documento")):
        s = novo(nome, ajuda)
        s.add_argument("colecao")
        s.add_argument("id")
        s.add_argument("json", nargs="?", help="dados em JSON (ou use --arquivo)")
        s.add_argument("--arquivo", help="lê os dados deste arquivo JSON ('-' = entrada padrão)")
        if nome == "update":
            s.add_argument("--profundo", action="store_true",
                           help="junta também os objetos de dentro")
    s = novo("get", "mostra um documento")
    s.add_argument("colecao")
    s.add_argument("id")
    s = novo("listar", "lista os documentos de uma coleção")
    s.add_argument("colecao")
    s.add_argument("--so-ids", action="store_true", help="mostra só os ids")
    s = novo("consultar", "filtra documentos: consultar agenda '{\"status\":\"postado\"}'")
    s.add_argument("colecao")
    s.add_argument("filtro", nargs="?", default="{}")
    s.add_argument("--ordenar")
    s = novo("apagar", "apaga um documento")
    s.add_argument("colecao")
    s.add_argument("id")
    s = novo("batch", "aplica várias operações de um arquivo JSON (tudo ou nada)")
    s.add_argument("arquivo")
    novo("colecoes", "lista as coleções e quantos documentos cada uma tem")
    s = novo("comparar", "modo sombra: compara o espelho com um export do banco real")
    s.add_argument("arquivo")
    s = novo("embutir", "embute painel_dados.json dentro de um HTML")
    s.add_argument("html")
    s.add_argument("--dados", help="JSON a embutir (padrão: painel_dados.json)")
    s.add_argument("--saida", help="HTML de saída (padrão: sobrescreve o de entrada)")

    a = p.parse_args(argv)
    if not a.cmd:
        p.print_help()
        return 2
    try:
        if a.cmd == "embutir":
            dados = ler_json(Path(a.dados) if a.dados else caminho_export())
            if dados is None:
                raise ErroEspelho("painel_dados.json não existe; rode 'exportar' antes")
            origem = Path(a.html)
            html = origem.read_text(encoding="utf-8")
            destino = Path(a.saida) if a.saida else origem
            destino.write_text(embutir_no_html(html, dados), encoding="utf-8")
            _imprimir({"ok": True, "html": str(destino)})
            return 0
        with EspelhoBanco(a.banco) as b:
            if a.cmd == "importar":
                _imprimir(b.importar(a.arquivo, substituir=a.substituir))
            elif a.cmd == "exportar":
                _imprimir(b.exportar(a.saida))
            elif a.cmd == "set":
                _imprimir(b.set(a.colecao, a.id, _ler_json_arg(a.json, a.arquivo)))
            elif a.cmd == "update":
                _imprimir(b.update(a.colecao, a.id, _ler_json_arg(a.json, a.arquivo),
                                   profundo=a.profundo))
            elif a.cmd == "get":
                doc = b.registro(a.colecao, a.id)
                if doc is None:
                    print(f"não existe: {a.colecao}/{a.id}", file=sys.stderr)
                    return 1
                _imprimir(doc)
            elif a.cmd == "listar":
                regs = b.list(a.colecao)
                _imprimir([r["id"] for r in regs] if a.so_ids else regs)
            elif a.cmd == "consultar":
                _imprimir(b.query(a.colecao, json.loads(a.filtro), ordenar=a.ordenar))
            elif a.cmd == "apagar":
                _imprimir({"apagado": b.delete(a.colecao, a.id)})
            elif a.cmd == "batch":
                _imprimir(b.batch(_ler_json_arg(None, a.arquivo)))
            elif a.cmd == "colecoes":
                _imprimir(b.colecoes())
            elif a.cmd == "comparar":
                r = b.comparar(a.arquivo)
                _imprimir(r)
                return 0 if r["iguais"] else 1
    except (ErroEspelho, json.JSONDecodeError, OSError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
