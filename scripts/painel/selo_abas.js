/* selo_abas.js — selo (contador) das abas do painel HP.
 *
 * Regra: o selo mostra a contagem REAL de itens da aba e some quando é 0.
 * Não conta: null/undefined, texto vazio ou só espaços, e os textos de
 * "lista vazia" ("Nenhum item", "Nada aqui.", "carregando…", "—" ...).
 *
 * Uso no painel:
 *   const n = SeloAbas.contarSelo(grupos, "nao");     // grupos = {hoje:[...], nao:[...]}
 *   SeloAbas.renderSelo(elementoDoSelo, n);            // 0 => some; 1..99 => número; 100+ => "99+"
 *   `${rotulo}${SeloAbas.htmlSelo(n)}`                 // quando o HTML é montado em texto
 *
 * Sem dependências, sem rede. Funciona no navegador (window.SeloAbas) e no
 * node (module.exports), para os testes. A mesma lógica existe em selo_abas.py.
 */
(function (raiz) {
  "use strict";

  var CHAVES_TEXTO = ["texto", "titulo", "title", "text", "nome", "rotulo", "label"];
  var CHAVES_ABA = ["aba", "grupo"];

  var RX_PLACEHOLDER = [
    /^$/,
    /^[-—–_.·…]+$/,
    /^nenhum(?:a|as|os)?(?: [a-z0-9/]+){0,3}$/,
    /^nada(?: (?:aqui|por aqui|pendente|urgente|urgente para hoje|na fila|nesta data|nesta data para este canal|concluido ainda|a fazer|agendado|por enquanto|para hoje))?$/,
    /^sem (?:itens?|pendencias?|tarefas?|nada|dados|posts?|conteudo)(?: (?:agora|hoje|por enquanto))?$/,
    /^(?:vazio|vazia|carregando|tudo em dia|tudo certo|n\/?a|nao ha itens|nao ha pendencias)$/
  ];

  /* "  Nenhuma Pendência. " -> "nenhuma pendencia" */
  function normalizarTexto(s) {
    return String(s == null ? "" : s)
      .normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/\s+/g, " ").trim()
      .replace(/[.!…:;]+$/, "").trim();
  }

  function ehPlaceholder(texto) {
    var t = normalizarTexto(texto);
    for (var i = 0; i < RX_PLACEHOLDER.length; i++) {
      if (RX_PLACEHOLDER[i].test(t)) return true;
    }
    return false;
  }

  function ehElemento(x) {
    return typeof Element !== "undefined" && x instanceof Element;
  }

  function temChave(o, k) {
    return Object.prototype.hasOwnProperty.call(o, k);
  }

  /* true se o item é um item de verdade (conta no selo) */
  function ehItemReal(item) {
    if (item === null || item === undefined || item === false || item === true) return false;
    if (typeof item === "number") return isFinite(item);
    if (typeof item === "string") return !ehPlaceholder(item);
    if (ehElemento(item)) {
      if (item.hidden) return false;
      if (item.dataset && item.dataset.placeholder !== undefined) return false;
      var cl = item.classList;
      if (cl && (cl.contains("vazio") || cl.contains("placeholder") || cl.contains("empty"))) return false;
      return !ehPlaceholder(item.textContent);
    }
    if (Array.isArray(item)) return item.some(ehItemReal);
    if (typeof item === "object") {
      if (item.placeholder || item.vazio || item._placeholder) return false;
      var tipo = normalizarTexto(item.tipo || item.type || "");
      if (tipo === "placeholder" || tipo === "vazio" || tipo === "empty") return false;
      var temTexto = false;
      for (var i = 0; i < CHAVES_TEXTO.length; i++) {
        var k = CHAVES_TEXTO[i];
        if (temChave(item, k)) {
          temTexto = true;
          if (item[k] !== null && item[k] !== undefined) return !ehPlaceholder(item[k]);
        }
      }
      if (temTexto) return false;           /* tinha campo de texto, mas vazio */
      return Object.keys(item).length > 0;  /* {} não conta */
    }
    return false;
  }

  function abaDoItem(item) {
    if (!item || typeof item !== "object" || Array.isArray(item) || ehElemento(item)) return undefined;
    for (var i = 0; i < CHAVES_ABA.length; i++) {
      if (temChave(item, CHAVES_ABA[i])) return item[CHAVES_ABA[i]];
    }
    return undefined;
  }

  /* Conta os itens reais de uma aba.
   *  itens: lista; ou {aba: lista}; ou texto com um item por linha; ou NodeList.
   *  aba:   chave da aba (opcional). Numa lista, itens com campo `aba`/`grupo`
   *         diferente são ignorados; itens sem esse campo contam.
   */
  function contarSelo(itens, aba) {
    if (itens === null || itens === undefined) return 0;
    if (typeof itens === "number") return isFinite(itens) && itens > 0 ? Math.floor(itens) : 0;
    if (typeof itens === "string") {
      /* o bug clássico: "".split("\n") dá [""] e length 1 */
      return itens.split(/\r?\n/).filter(ehItemReal).length;
    }
    if (!Array.isArray(itens) && typeof itens.length === "number" && typeof itens !== "function") {
      itens = Array.prototype.slice.call(itens);   /* NodeList, HTMLCollection */
    }
    if (Array.isArray(itens)) {
      var temAba = aba !== null && aba !== undefined && aba !== "";
      var n = 0;
      for (var i = 0; i < itens.length; i++) {
        var it = itens[i];
        if (temAba) {
          var a = abaDoItem(it);
          if (a !== undefined && String(a) !== String(aba)) continue;
        }
        if (ehItemReal(it)) n++;
      }
      return n;
    }
    if (typeof itens === "object") {
      if (aba !== null && aba !== undefined && aba !== "") {
        return temChave(itens, aba) ? contarSelo(itens[aba], null) : 0;
      }
      var total = 0;
      for (var k in itens) if (temChave(itens, k)) total += contarSelo(itens[k], null);
      return total;
    }
    return 0;
  }

  /* Texto do selo: "" quando 0 (some), "99+" acima de 99. */
  function textoSelo(n) {
    n = Number(n);
    if (!isFinite(n) || n <= 0) return "";
    n = Math.floor(n);
    return n > 99 ? "99+" : String(n);
  }

  /* Mostra ou esconde o selo. Usa `hidden` E display:none, porque um CSS
   * como `.num{display:inline-flex}` passa por cima do atributo hidden. */
  function renderSelo(el, n) {
    if (!el) return el;
    var t = textoSelo(n);
    el.textContent = t;
    if (t) {
      el.hidden = false;
      if (el.style) el.style.removeProperty("display");
      el.removeAttribute("aria-hidden");
    } else {
      el.hidden = true;
      if (el.style) el.style.display = "none";
      el.setAttribute("aria-hidden", "true");
    }
    return el;
  }

  function escHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"}[c];
    });
  }

  /* HTML do selo para montar em texto: "" quando 0. */
  function htmlSelo(n, classe, tag) {
    var t = textoSelo(n);
    if (!t) return "";
    tag = tag || "b";
    return "<" + tag + " class=\"" + escHtml(classe == null ? "num" : classe) + "\">" + t + "</" + tag + ">";
  }

  /* Atualiza todos os [data-selo-aba] dentro de `raizDom` a partir dos grupos. */
  function atualizarSelos(raizDom, grupos) {
    var els = (raizDom || document).querySelectorAll("[data-selo-aba]");
    for (var i = 0; i < els.length; i++) {
      renderSelo(els[i], contarSelo(grupos, els[i].getAttribute("data-selo-aba")));
    }
    return els.length;
  }

  var api = {
    contarSelo: contarSelo, renderSelo: renderSelo, textoSelo: textoSelo,
    htmlSelo: htmlSelo, ehItemReal: ehItemReal, ehPlaceholder: ehPlaceholder,
    atualizarSelos: atualizarSelos, normalizarTexto: normalizarTexto
  };
  if (typeof module === "object" && module && module.exports) module.exports = api;
  if (raiz) {
    raiz.SeloAbas = api;
    raiz.contarSelo = contarSelo;
    raiz.renderSelo = renderSelo;
  }
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this));
