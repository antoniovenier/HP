/* previa_celular.js — prévia do post numa moldura de celular, por rede.
 *
 * Clicar na capa abre um modal com um celular genérico (sem marca) e uma
 * barra com as redes. Cada rede mostra como o post fica: proporção certa,
 * o que a interface cobre (botões à direita, legenda embaixo, nome da conta)
 * e a legenda cortada no "... mais" no limite aproximado de cada rede.
 * Sem logos oficiais: só rótulos de texto e ícones genéricos desenhados aqui.
 *
 * Entrada: post = {capa, video?, legenda, titulo?, conta, canal, redes:[...],
 *                  laminas?:[...], tipo?, avatar?, cor?}
 *
 * API (window.PreviaCelular):
 *   abrir(post, {origem, rede, tema:"auto"|"claro"|"escuro", todas, acaoExtra:{rotulo, executar}})
 *   fechar()
 *   ligar(raizDom, {seletor, tema})   clique/Enter em [data-previa='{json}'] abre a prévia
 *   deItemAgenda(item, canaisPorId, {avatares})   converte um item do dados.json do painel
 *   cortarLegenda(texto, limite, maxLinhas), redesDoPost(post), normalizarRede(nome, post)
 *   REDES (tabela editável: limites, proporções, zonas)
 *
 * Acessível: Esc fecha, foco preso no modal, abas com setas, volta o foco
 * para a capa ao fechar. Tema claro/escuro (segue o painel). Sem rede, sem
 * bibliotecas externas. Funciona no node (module.exports) para os testes.
 */
(function (raiz) {
  "use strict";

  /* Limites de legenda são APROXIMADOS (celular de ~390 pt de largura, 2025/2026).
   * zonas = % da área do vídeo coberta pela interface (topo, base, direita) e
   * onde começa a coluna de botões (trilho). Ajuste aqui se a rede mudar. */
  var REDES = {
    instagram_reels: {rotulo: "Instagram Reels", curto: "Reels", layout: "vertical", estilo: "ig",
      proporcao: "9:16", tamanho: "1080×1920", limite: 55, linhas: 1, reticencias: "... ", mais: "mais",
      maximo: 2200, zonas: {topo: 11, base: 24, direita: 15, trilho: 50}, topo: "Reels",
      dica: "A legenda aparece em 1 linha por cima do vídeo: as primeiras palavras precisam prender."},
    instagram_feed: {rotulo: "Instagram Feed", curto: "Feed", layout: "feed", estilo: "ig",
      proporcao: "4:5", tamanho: "1080×1350", limite: 125, linhas: 2, reticencias: "... ", mais: "mais",
      maximo: 2200,
      dica: "No feed a capa aparece em 4:5; capa 9:16 perde um pedaço em cima e embaixo."},
    instagram_story: {rotulo: "Instagram Story", curto: "Story", layout: "story", estilo: "ig",
      proporcao: "9:16", tamanho: "1080×1920", limite: 0, linhas: 0, maximo: 0,
      zonas: {topo: 14, base: 20},
      dica: "Story não mostra legenda: o que importa tem de estar na arte, fora das faixas cobertas."},
    tiktok: {rotulo: "TikTok", curto: "TikTok", layout: "vertical", estilo: "tt",
      proporcao: "9:16", tamanho: "1080×1920", limite: 80, linhas: 2, reticencias: "... ", mais: "mais",
      maximo: 4000, zonas: {topo: 9, base: 22, direita: 15, trilho: 40},
      dica: "Legenda em até 2 linhas antes do \"mais\"; a coluna de botões cobre a direita."},
    youtube_shorts: {rotulo: "YouTube Shorts", curto: "Shorts", layout: "vertical", estilo: "yt",
      proporcao: "9:16", tamanho: "1080×1920", limite: 70, linhas: 2, reticencias: "...", mais: "",
      maximo: 100, campo: "titulo", zonas: {topo: 8, base: 24, direita: 16, trilho: 42},
      dica: "No Shorts aparece o TÍTULO (máx. 100 caracteres), não a descrição."},
    facebook: {rotulo: "Facebook", curto: "Facebook", layout: "texto_em_cima", estilo: "fb",
      proporcao: "4:5", tamanho: "1080×1350", limite: 125, linhas: 3, reticencias: "... ", mais: "Ver mais",
      maximo: 63206,
      dica: "O texto vem ANTES da imagem e corta em ~3 linhas com \"Ver mais\"."},
    facebook_reels: {rotulo: "Facebook Reels", curto: "FB Reels", layout: "vertical", estilo: "fb",
      proporcao: "9:16", tamanho: "1080×1920", limite: 60, linhas: 1, reticencias: "... ", mais: "Ver mais",
      maximo: 2200, zonas: {topo: 9, base: 24, direita: 15, trilho: 50},
      dica: "Vídeo vertical no Facebook vira Reels: mesma lógica do Instagram Reels."},
    facebook_story: {rotulo: "Facebook Story", curto: "FB Story", layout: "story", estilo: "fb",
      proporcao: "9:16", tamanho: "1080×1920", limite: 0, linhas: 0, maximo: 0,
      zonas: {topo: 14, base: 20},
      dica: "Story não mostra legenda: o texto tem de estar na arte."},
    threads: {rotulo: "Threads", curto: "Threads", layout: "texto_em_cima", estilo: "th",
      proporcao: "1:1", proporcaoVideo: "4:5", tamanho: "1080×1080", limite: 500, linhas: 0,
      reticencias: "... ", mais: "mais", maximo: 500,
      dica: "No Threads o texto é o principal: até 500 caracteres aparecem inteiros."},
    pinterest: {rotulo: "Pinterest", curto: "Pinterest", layout: "pin", estilo: "pin",
      proporcao: "2:3", tamanho: "1000×1500", limite: 40, linhas: 2, reticencias: "...", mais: "",
      maximo: 100, campo: "titulo",
      dica: "Na grade aparece a imagem 2:3 e o começo do título (máx. 100 caracteres)."}
  };
  var ORDEM = ["instagram_reels", "instagram_feed", "instagram_story", "tiktok", "youtube_shorts",
    "facebook", "facebook_reels", "facebook_story", "threads", "pinterest"];
  var PADRAO = ["instagram_reels", "instagram_feed", "instagram_story", "tiktok", "youtube_shorts",
    "facebook", "threads", "pinterest"];
  var APELIDOS = {
    reels: "instagram_reels", reel: "instagram_reels", instagramreels: "instagram_reels", igreels: "instagram_reels",
    feed: "instagram_feed", instagramfeed: "instagram_feed", igfeed: "instagram_feed",
    story: "instagram_story", stories: "instagram_story", instagramstory: "instagram_story",
    instagramstories: "instagram_story", igstory: "instagram_story",
    tiktok: "tiktok", tt: "tiktok",
    shorts: "youtube_shorts", short: "youtube_shorts", youtube: "youtube_shorts", yt: "youtube_shorts",
    youtubeshorts: "youtube_shorts", ytshorts: "youtube_shorts",
    facebookfeed: "facebook", facebookreels: "facebook_reels", fbreels: "facebook_reels",
    facebookstory: "facebook_story", facebookstories: "facebook_story", fbstory: "facebook_story",
    threads: "threads", pinterest: "pinterest", pin: "pinterest"
  };
  var TIPOS_VIDEO = {reels: 1, reel: 1, video: 1, short: 1, shorts: 1, corte: 1, clipe: 1};
  var CONFIG = {tema: "auto"};

  /* ------------------------------------------------------------------ */
  /* funções puras (testadas no node)                                    */
  /* ------------------------------------------------------------------ */
  function chave(s) {
    return String(s == null ? "" : s).normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]/g, "");
  }

  function ehVideo(post) {
    post = post || {};
    return !!post.video || !!TIPOS_VIDEO[chave(post.tipo)];
  }

  /* "Instagram" + tipo do post -> chave da tabela REDES (ou null) */
  function normalizarRede(nome, post) {
    var k = chave(nome), tipo = chave(post && post.tipo);
    if (REDES[nome]) return nome;
    if (k === "instagram" || k === "ig") {
      if (tipo === "story" || tipo === "stories") return "instagram_story";
      return ehVideo(post) ? "instagram_reels" : "instagram_feed";
    }
    if (k === "facebook" || k === "fb") {
      if (tipo === "story" || tipo === "stories") return "facebook_story";
      return ehVideo(post) ? "facebook_reels" : "facebook";
    }
    return APELIDOS[k] || null;
  }

  function redesDoPost(post) {
    var lista = post && post.redes;
    if (typeof lista === "string") lista = lista.split(/[,;|]/);
    if (!lista || !lista.length) return PADRAO.slice();
    var vistas = {}, res = [];
    for (var i = 0; i < lista.length; i++) {
      var r = normalizarRede(String(lista[i]).trim(), post);
      if (r && !vistas[r]) { vistas[r] = 1; res.push(r); }
    }
    res.sort(function (a, b) { return ORDEM.indexOf(a) - ORDEM.indexOf(b); });
    return res.length ? res : PADRAO.slice();
  }

  /* Corta a legenda como a rede faz no modo recolhido.
   * -> {visivel, cortou, total}  (total em caracteres de verdade, emoji = 1) */
  function cortarLegenda(texto, limite, maxLinhas) {
    var t = String(texto == null ? "" : texto).replace(/\r\n?/g, "\n").replace(/^\s+|\s+$/g, "");
    var total = Array.from(t).length;
    if (!limite || limite <= 0) return {visivel: "", cortou: total > 0, total: total};
    var cortou = false, base = t;
    if (maxLinhas > 0) {
      var linhas = base.split("\n");
      if (linhas.length > maxLinhas) { base = linhas.slice(0, maxLinhas).join("\n"); cortou = true; }
    }
    var cps = Array.from(base);
    if (cps.length > limite) {
      var corte = cps.slice(0, limite).join("");
      var esp = Math.max(corte.lastIndexOf(" "), corte.lastIndexOf("\n"));
      if (esp >= Math.floor(corte.length * 0.6)) corte = corte.slice(0, esp);
      base = corte;
      cortou = true;
    }
    if (cortou) base = base.replace(/[\s,;:\-–—]+$/, "");
    return {visivel: base, cortou: cortou, total: total};
  }

  function primeiraLinha(s) {
    return String(s || "").replace(/^\s+/, "").split(/\r?\n/)[0] || "";
  }

  /* qual texto a rede mostra: legenda, ou título (Shorts, Pinterest) */
  function textoDaRede(post, rede) {
    post = post || {};
    if (rede && rede.campo === "titulo") {
      if (post.titulo) return {texto: String(post.titulo), origem: "titulo"};
      var l = primeiraLinha(post.legenda);
      return {texto: l, origem: l ? "legenda" : "nenhum"};
    }
    if (post.legenda) return {texto: String(post.legenda), origem: "legenda"};
    if (post.titulo) return {texto: String(post.titulo), origem: "titulo_no_lugar"};
    return {texto: "", origem: "nenhum"};
  }

  function proporcaoDe(post, rede, redeChave) {
    var fmt = post && post.formatos && post.formatos[redeChave];
    if (fmt) return fmt;
    if (rede.proporcaoVideo && ehVideo(post)) return rede.proporcaoVideo;
    return rede.proporcao;
  }

  /* quanto a capa perde ao ser encaixada (object-fit: cover) na proporção da rede */
  function calcularCorte(largura, altura, proporcao) {
    var pr = String(proporcao).split(":"), alvo = (+pr[0]) / (+pr[1]);
    if (!largura || !altura || !alvo) return null;
    var r = largura / altura;
    if (Math.abs(r - alvo) / alvo < 0.02) return {perde: 0, onde: "nada"};
    if (r < alvo) return {perde: Math.round((1 - r / alvo) * 100), onde: "em cima e embaixo"};
    return {perde: Math.round((1 - alvo / r) * 100), onde: "dos lados"};
  }

  /* item de agenda do dados.json do painel -> post da prévia */
  function deItemAgenda(x, canais, extras) {
    x = x || {};
    extras = extras || {};
    var c = (canais && x.canal && canais[x.canal]) || {};
    var laminas = (Array.isArray(x.laminas) && x.laminas.length) ? x.laminas.slice() : null;
    return {
      capa: x.capa_zoom || x.capa_img || (laminas && laminas[0]) || "",
      capa_rapida: x.capa_img || "",
      video: x.video || "",
      legenda: x.legenda || "",
      titulo: x.titulo || "",
      conta: x.conta || c.handle || "",
      canal: x.canal_nome || c.nome || x.canal || "",
      cor: c.cor || "",
      tipo: x.tipo || "",
      redes: Array.isArray(x.redes) ? x.redes.slice() : [],
      laminas: laminas,
      avatar: (extras.avatares && extras.avatares[x.canal]) || ""
    };
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (ch) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"}[ch];
    });
  }

  /* texto -> HTML com #hashtags e @menções destacadas e quebras de linha */
  function legendaHtml(t) {
    return esc(t)
      .replace(/(^|[\s(])([#@][\p{L}\p{N}_]+(?:\.[\p{L}\p{N}_]+)*)/gu, "$1<span class=\"pc-tag\">$2</span>")
      .replace(/\n/g, "<br>");
  }

  function milhar(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  /* ------------------------------------------------------------------ */
  /* ícones genéricos (desenhados aqui; nenhum logo)                      */
  /* ------------------------------------------------------------------ */
  var IC = {
    coracao: "<path d=\"M12 20.3s-7.4-4.5-9.2-9C1.6 8.1 3.7 4.8 7 4.8c2 0 3.4 1 5 2.9 1.6-1.9 3-2.9 5-2.9 3.3 0 5.4 3.3 4.2 6.5-1.8 4.5-9.2 9-9.2 9z\"/>",
    balao: "<path d=\"M20.5 11.5a8.4 8.4 0 0 1-12.4 7.4L3.5 20.4l1.6-4.3a8.4 8.4 0 1 1 15.4-4.6z\"/>",
    aviao: "<path d=\"M21.3 3.2 10.4 13.9M21.3 3.2 14.6 21l-4.2-7.1L3.2 9.6z\"/>",
    salvar: "<path d=\"M18.5 21 12 15.8 5.5 21V3.5h13z\"/>",
    compartilhar: "<path d=\"M14 4.5 21 11l-7 6.5M21 11H11a7.5 7.5 0 0 0-7.5 7.5\"/>",
    pontos: "<circle cx=\"5.5\" cy=\"12\" r=\"1.3\"/><circle cx=\"12\" cy=\"12\" r=\"1.3\"/><circle cx=\"18.5\" cy=\"12\" r=\"1.3\"/>",
    musica: "<path d=\"M9 17.5V5.5l10.5-2v12\"/><circle cx=\"6.5\" cy=\"17.5\" r=\"2.5\"/><circle cx=\"17\" cy=\"15.5\" r=\"2.5\"/>",
    camera: "<rect x=\"3\" y=\"6.5\" width=\"18\" height=\"13.5\" rx=\"3\"/><circle cx=\"12\" cy=\"13.2\" r=\"3.4\"/><path d=\"M8.7 6.5 10 4h4l1.3 2.5\"/>",
    busca: "<circle cx=\"10.8\" cy=\"10.8\" r=\"6.8\"/><path d=\"M20.5 20.5 15.8 15.8\"/>",
    casa: "<path d=\"M3.5 10.5 12 3.5l8.5 7v10h-5.6v-6.2H9.1v6.2H3.5z\"/>",
    novo: "<rect x=\"3.5\" y=\"3.5\" width=\"17\" height=\"17\" rx=\"4.5\"/><path d=\"M12 8v8M8 12h8\"/>",
    video: "<rect x=\"3.5\" y=\"3.5\" width=\"17\" height=\"17\" rx=\"4.5\"/><path d=\"M10 8.6v6.8l5.8-3.4z\"/>",
    perfil: "<circle cx=\"12\" cy=\"8.3\" r=\"4\"/><path d=\"M4 20.5c0-4 3.6-6.3 8-6.3s8 2.3 8 6.3\"/>",
    gostei: "<path d=\"M7.2 10.4v10.1H3.5V10.4zM7.2 10.4 11 3.5c1.7 0 2.8 1.3 2.4 3L12.9 9h6a2 2 0 0 1 2 2.3l-1.2 7.4a2.1 2.1 0 0 1-2 1.8H7.2\"/>",
    repost: "<path d=\"m17 3.5 3 3-3 3M20 6.5H8.5a4.5 4.5 0 0 0-4.5 4.5v.8M7 20.5l-3-3 3-3M4 17.5h11.5a4.5 4.5 0 0 0 4.5-4.5v-.8\"/>",
    fechar: "<path d=\"M5.5 5.5l13 13M18.5 5.5l-13 13\"/>",
    disco: "<circle cx=\"12\" cy=\"12\" r=\"8.5\"/><circle cx=\"12\" cy=\"12\" r=\"2.5\"/>",
    sino: "<path d=\"M6 16.5V11a6 6 0 1 1 12 0v5.5l1.5 2h-15zM10 20.5a2 2 0 0 0 4 0\"/>"
  };

  function icone(nome, classe) {
    return "<svg class=\"pc-ic" + (classe ? " " + classe : "") + "\" viewBox=\"0 0 24 24\" aria-hidden=\"true\" focusable=\"false\">" +
      (IC[nome] || "") + "</svg>";
  }

  /* ------------------------------------------------------------------ */
  /* montagem das telas                                                   */
  /* ------------------------------------------------------------------ */
  function usuario(post) {
    var u = String(post.conta || "").replace(/^@/, "").trim();
    if (!u) u = chave(post.canal) || "conta";
    return u;
  }

  function nomeConta(post, rede) {
    var u = usuario(post);
    if (rede.estilo === "yt") return "@" + u;
    if (rede.estilo === "fb" || rede.estilo === "pin") return post.canal || u;
    return u;
  }

  function horaAgora() {
    var d = new Date();
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function status() {
    return "<div class=\"pc-status\" aria-hidden=\"true\"><span class=\"pc-hora\">" + horaAgora() +
      "</span><span class=\"pc-st-ics\"><i class=\"pc-sinal\"><i></i><i></i><i></i><i></i></i>" +
      "<i class=\"pc-bateria\"></i></span></div>";
  }

  function nav(vertical) {
    return "<div class=\"pc-nav" + (vertical ? " pc-nav-escura" : "") + "\" aria-hidden=\"true\">" +
      icone("casa") + icone("busca") + icone("novo") + icone("video") + icone("perfil") + "</div>";
  }

  function avatar(post, classe) {
    var letra = (String(post.canal || usuario(post)).trim()[0] || "H").toUpperCase();
    return "<span class=\"pc-avatar" + (classe ? " " + classe : "") + "\" data-pc-avatar" +
      (post.cor ? " style=\"--pc-cor-canal:" + esc(post.cor) + "\"" : "") + "><b>" + esc(letra) + "</b></span>";
  }

  function blocoLegenda(post, rede, expandida) {
    var info = textoDaRede(post, rede);
    var c = cortarLegenda(info.texto, rede.limite, rede.linhas);
    var html = legendaHtml(expandida ? info.texto.trim() : c.visivel);
    if (c.cortou && !expandida) {
      html += "<span class=\"pc-ret\">" + esc(rede.reticencias || "...") + "</span>";
      if (rede.mais) {
        html += "<button type=\"button\" class=\"pc-mais\" data-pc-acao=\"mais\" aria-label=\"" +
          esc(rede.mais) + " (mostrar a legenda inteira)\">" + esc(rede.mais) + "</button>";
      }
    }
    return html;
  }

  function caixaMidia(post, proporcao, estado, classe) {
    var pr = String(proporcao).split(":");
    var n = (post.laminas && post.laminas.length) || 0;
    var h = "<div class=\"pc-midia-caixa" + (classe ? " " + classe : "") + "\" style=\"aspect-ratio:" +
      (+pr[0]) + " / " + (+pr[1]) + "\"><div class=\"pc-midia\" data-pc-midia></div>";
    if (n > 1) {
      h += "<span class=\"pc-contador\">" + (estado.lamina + 1) + "/" + n + "</span>" +
        "<button type=\"button\" class=\"pc-seta pc-seta-ant\" data-pc-acao=\"ant\" aria-label=\"Lâmina anterior\"" +
        (estado.lamina === 0 ? " disabled" : "") + ">‹</button>" +
        "<button type=\"button\" class=\"pc-seta pc-seta-prox\" data-pc-acao=\"prox\" aria-label=\"Próxima lâmina\"" +
        (estado.lamina >= n - 1 ? " disabled" : "") + ">›</button>";
    }
    h += "</div>";
    if (n > 1) {
      h += "<div class=\"pc-pontos\" aria-hidden=\"true\">";
      for (var i = 0; i < Math.min(n, 10); i++) h += "<i" + (i === estado.lamina ? " class=\"pc-on\"" : "") + "></i>";
      h += "</div>";
    }
    return h;
  }

  function zonasHtml(z, lateral) {
    if (!z) return "";
    var h = "<div class=\"pc-zonas\" aria-hidden=\"true\">";
    if (z.topo) h += "<i class=\"pc-z pc-z-topo\"><span>coberto</span></i>";
    if (z.base) h += "<i class=\"pc-z pc-z-base" + (lateral ? "" : " pc-z-cheia") + "\"><span>coberto</span></i>";
    if (lateral && z.direita) h += "<i class=\"pc-z pc-z-dir\"></i>";
    return h + "</div>";
  }

  function varsZonas(z) {
    z = z || {};
    return "--z-topo:" + (z.topo || 0) + "%;--z-base:" + (z.base || 0) + "%;--z-dir:" +
      (z.direita || 0) + "%;--z-trilho:" + (z.trilho || 50) + "%";
  }

  function itemTrilho(ic, rotulo) {
    return "<span class=\"pc-tr\">" + icone(ic) + (rotulo ? "<small>" + esc(rotulo) + "</small>" : "") + "</span>";
  }

  function telaVertical(post, rede, est) {
    var e = rede.estilo, conta = nomeConta(post, rede);
    var topo = {
      ig: "<b>" + esc(rede.topo || "Reels") + "</b>" + icone("camera"),
      tt: "<span class=\"pc-tt-abas\"><span>Seguindo</span><b>Para você</b></span>" + icone("busca"),
      yt: "<span></span><span class=\"pc-ics\">" + icone("busca") + icone("pontos") + "</span>",
      fb: "<b>" + esc(rede.topo || "Reels") + "</b>" + icone("busca")
    }[e] || "";
    var trilho = {
      ig: itemTrilho("coracao", "12,4 mil") + itemTrilho("balao", "318") + itemTrilho("aviao", "96") +
        itemTrilho("pontos", "") + "<span class=\"pc-tr-capa\"></span>",
      tt: "<span class=\"pc-tr pc-tr-av\">" + avatar(post) + "<i class=\"pc-mais-av\">+</i></span>" +
        itemTrilho("coracao", "12,4 mil") + itemTrilho("balao", "318") + itemTrilho("salvar", "1.024") +
        itemTrilho("compartilhar", "96") + "<span class=\"pc-tr\">" + icone("disco", "pc-gira") + "</span>",
      yt: itemTrilho("gostei", "12 mil") + "<span class=\"pc-tr\">" + icone("gostei", "pc-inv") + "<small>Não gostei</small></span>" +
        itemTrilho("balao", "318") + itemTrilho("compartilhar", "Compartilhar") + itemTrilho("pontos", ""),
      fb: itemTrilho("gostei", "1,2 mil") + itemTrilho("balao", "318") + itemTrilho("compartilhar", "96") +
        itemTrilho("pontos", "")
    }[e] || "";
    var seguir = e === "yt" ? "Inscrever-se" : "Seguir";
    var linhaConta = "<div class=\"pc-conta\">" + (e === "tt" ? "" : avatar(post)) + "<b>" + esc(conta) + "</b>" +
      (e === "tt" ? "" : "<span class=\"pc-seguir\">" + seguir + "</span>") + "</div>";
    var audio = e === "ig" ? "<div class=\"pc-audio\">" + icone("musica") + "<span>" + esc(usuario(post)) + " · Áudio original</span></div>"
      : e === "tt" ? "<div class=\"pc-audio\">" + icone("musica") + "<span>som original - " + esc(usuario(post)) + "</span></div>" : "";
    return status() +
      "<div class=\"pc-video\" style=\"" + varsZonas(rede.zonas) + "\">" +
      "<div class=\"pc-midia\" data-pc-midia></div><div class=\"pc-degrade\"></div>" +
      "<div class=\"pc-topo-app pc-topo-" + e + "\">" + topo + "</div>" +
      "<div class=\"pc-trilho\">" + trilho + "</div>" +
      "<div class=\"pc-info" + (est.expandida ? " pc-expandida" : "") + "\">" + linhaConta +
      "<p class=\"pc-legenda\">" + blocoLegenda(post, rede, est.expandida) + "</p>" + audio + "</div>" +
      zonasHtml(rede.zonas, true) + "</div>" + nav(true);
  }

  function telaStory(post, rede) {
    return status() +
      "<div class=\"pc-video pc-video-story\" style=\"" + varsZonas(rede.zonas) + "\">" +
      "<div class=\"pc-midia\" data-pc-midia></div><div class=\"pc-degrade pc-degrade-topo\"></div>" +
      "<div class=\"pc-story-barras\"><i></i></div>" +
      "<div class=\"pc-story-topo\">" + avatar(post) + "<b>" + esc(nomeConta(post, rede)) + "</b><small>2 h</small>" +
      "<span class=\"pc-empurra\"></span>" + icone("pontos") + icone("fechar") + "</div>" +
      zonasHtml(rede.zonas, false) + "</div>" +
      "<div class=\"pc-story-base\" aria-hidden=\"true\"><span class=\"pc-campo\">Enviar mensagem</span>" +
      icone("coracao") + icone("aviao") + "</div>";
  }

  function temMidia(post) {
    return !!(post.capa || post.video || (post.laminas && post.laminas.length));
  }

  function telaFeed(post, rede, est, chaveRede) {
    var conta = nomeConta(post, rede);
    return status() + "<div class=\"pc-rolagem\">" +
      "<div class=\"pc-barra-app\"><b class=\"pc-app-nome\">Início</b><span class=\"pc-ics\">" +
      icone("coracao") + icone("aviao") + "</span></div>" +
      "<div class=\"pc-post-cab\">" + avatar(post, "pc-anel") + "<b>" + esc(conta) + "</b><span class=\"pc-empurra\"></span>" +
      icone("pontos") + "</div>" +
      caixaMidia(post, proporcaoDe(post, rede, chaveRede), est) +
      "<div class=\"pc-acoes\">" + icone("coracao") + icone("balao") + icone("aviao") +
      "<span class=\"pc-empurra\"></span>" + icone("salvar") + "</div>" +
      "<div class=\"pc-forte\">1.234 curtidas</div>" +
      "<p class=\"pc-legenda\"><b>" + esc(conta) + "</b> " + blocoLegenda(post, rede, est.expandida) + "</p>" +
      "<div class=\"pc-cinza\">Ver todos os 48 comentários</div><div class=\"pc-cinza pc-mini\">há 2 horas</div>" +
      "</div>" + nav(false);
  }

  function telaFacebook(post, rede, est, chaveRede) {
    return status() + "<div class=\"pc-rolagem\">" +
      "<div class=\"pc-barra-app\"><b class=\"pc-app-nome\">Início</b><span class=\"pc-ics\">" +
      icone("busca") + icone("aviao") + "</span></div>" +
      "<div class=\"pc-post-cab\">" + avatar(post) + "<span class=\"pc-nome2\"><b>" + esc(nomeConta(post, rede)) +
      "</b><small>2 h · Público</small></span><span class=\"pc-empurra\"></span>" + icone("pontos") + icone("fechar") + "</div>" +
      "<p class=\"pc-legenda pc-legenda-topo\">" + blocoLegenda(post, rede, est.expandida) + "</p>" +
      (temMidia(post) ? caixaMidia(post, proporcaoDe(post, rede, chaveRede), est) : "") +
      "<div class=\"pc-reacoes\"><span><i class=\"pc-bolinha\">" + icone("gostei") + "</i>1,2 mil</span>" +
      "<span>34 comentários · 12 compart.</span></div>" +
      "<div class=\"pc-botoes-fb\"><span>" + icone("gostei") + "Curtir</span><span>" + icone("balao") +
      "Comentar</span><span>" + icone("compartilhar") + "Compartilhar</span></div>" +
      "<div class=\"pc-fantasma\"><i></i><i></i><i></i></div></div>" + nav(false);
  }

  function telaThreads(post, rede, est, chaveRede) {
    return status() + "<div class=\"pc-rolagem\">" +
      "<div class=\"pc-barra-app pc-centro\"><b class=\"pc-app-nome\">Para você</b></div>" +
      "<div class=\"pc-th-post\">" + avatar(post) + "<div class=\"pc-th-corpo\">" +
      "<div class=\"pc-th-cab\"><b>" + esc(nomeConta(post, rede)) + "</b><small>2 h</small><span class=\"pc-empurra\"></span>" +
      icone("pontos") + "</div>" +
      "<p class=\"pc-legenda\">" + blocoLegenda(post, rede, est.expandida) + "</p>" +
      (temMidia(post) ? caixaMidia(post, proporcaoDe(post, rede, chaveRede), est, "pc-arredondada") : "") +
      "<div class=\"pc-acoes pc-acoes-th\">" + icone("coracao") + "<small>12</small>" + icone("balao") + "<small>3</small>" +
      icone("repost") + "<small>1</small>" + icone("aviao") + "</div>" +
      "</div></div><div class=\"pc-fantasma\"><i></i><i></i><i></i></div></div>" + nav(false);
  }

  function telaPin(post, rede, est, chaveRede) {
    return status() + "<div class=\"pc-rolagem\">" +
      "<div class=\"pc-busca\">" + icone("busca") + "<span>Pesquisar</span></div>" +
      "<div class=\"pc-grade\"><div class=\"pc-coluna\"><div class=\"pc-pin\">" +
      caixaMidia(post, proporcaoDe(post, rede, chaveRede), {lamina: 0}, "pc-arredondada pc-sem-carrossel") +
      "<p class=\"pc-legenda pc-pin-tit\">" + blocoLegenda(post, rede, est.expandida) + "</p>" +
      "<div class=\"pc-pin-conta\">" + avatar(post) + "<span>" + esc(nomeConta(post, rede)) + "</span>" +
      "<span class=\"pc-empurra\"></span>" + icone("pontos") + "</div></div>" +
      "<i class=\"pc-bloco\" style=\"aspect-ratio:3/4\"></i></div>" +
      "<div class=\"pc-coluna\"><i class=\"pc-bloco\" style=\"aspect-ratio:1/1\"></i>" +
      "<i class=\"pc-bloco\" style=\"aspect-ratio:2/3\"></i><i class=\"pc-bloco\" style=\"aspect-ratio:4/5\"></i></div></div>" +
      "</div>" + nav(false);
  }

  function montarTela(post, chaveRede, est) {
    var r = REDES[chaveRede];
    switch (r.layout) {
      case "vertical": return telaVertical(post, r, est);
      case "story": return telaStory(post, r, est);
      case "feed": return telaFeed(post, r, est, chaveRede);
      case "pin": return telaPin(post, r, est, chaveRede);
      default: return r.estilo === "th" ? telaThreads(post, r, est, chaveRede) : telaFacebook(post, r, est, chaveRede);
    }
  }

  function fichaHtml(post, chaveRede, est, opcoes) {
    var r = REDES[chaveRede], info = textoDaRede(post, r), c = cortarLegenda(info.texto, r.limite, r.linhas);
    var nome = r.campo === "titulo" ? "Título" : "Legenda";
    var h = "<h3 class=\"pc-ficha-tit\">" + esc(r.rotulo) + "</h3><dl class=\"pc-dados\">" +
      "<div><dt>Formato</dt><dd>" + esc(proporcaoDe(post, r, chaveRede)) + " · " + esc(r.tamanho) + "</dd></div>";
    if (r.limite > 0) {
      h += "<div><dt>" + nome + " visível</dt><dd>~" + r.limite + " caracteres" +
        (r.linhas ? " / " + r.linhas + " linha" + (r.linhas > 1 ? "s" : "") : "") +
        (r.mais ? " antes do \"" + esc(r.reticencias.trim() + " " + r.mais) + "\"" : "") + "</dd></div>";
      var sit = !c.total ? "<b class=\"pc-alerta\">vazia</b>"
        : c.cortou ? "<b class=\"pc-alerta\">aparece cortada</b> — só o começo fica à vista"
          : "<b class=\"pc-ok\">cabe inteira</b>";
      h += "<div><dt>Sua " + nome.toLowerCase() + "</dt><dd>" + milhar(c.total) + " caracteres — " + sit + "</dd></div>";
      if (r.maximo && c.total > r.maximo) {
        h += "<div><dt>Atenção</dt><dd><b class=\"pc-alerta\">passa do máximo da rede (" + milhar(r.maximo) +
          ")</b></dd></div>";
      } else if (r.maximo) {
        h += "<div><dt>Máximo da rede</dt><dd>" + milhar(r.maximo) + " caracteres</dd></div>";
      }
    } else {
      h += "<div><dt>Legenda</dt><dd>não aparece nesta rede</dd></div>";
    }
    if (r.zonas) {
      var z = r.zonas, partes = [];
      if (z.topo) partes.push("topo " + z.topo + "%");
      if (z.base) partes.push("base " + z.base + "%");
      if (z.direita) partes.push("direita " + z.direita + "%");
      h += "<div><dt>Interface cobre</dt><dd>" + partes.join(" · ") + "</dd></div>";
    }
    h += "<div><dt>Capa</dt><dd data-pc-corte>" + (temMidia(post) ? "conferindo…" : "sem capa (post só de texto)") + "</dd></div></dl>";
    if (info.origem === "titulo_no_lugar") {
      h += "<p class=\"pc-aviso\">Sem legenda nos dados: a prévia está usando o título no lugar.</p>";
    }
    if (r.dica) h += "<p class=\"pc-dica\">" + esc(r.dica) + "</p>";
    h += "<div class=\"pc-botoes\">";
    if (r.zonas) {
      h += "<button type=\"button\" class=\"pc-botao\" data-pc-acao=\"zonas\" aria-pressed=\"" + (est.zonas ? "true" : "false") +
        "\">" + (est.zonas ? "Esconder" : "Mostrar") + " zonas cobertas</button>";
    }
    if (r.layout !== "vertical" && r.layout !== "story") {
      h += "<button type=\"button\" class=\"pc-botao\" data-pc-acao=\"tema-app\">Tela " +
        (est.temaApp === "escuro" ? "clara" : "escura") + "</button>";
    }
    if (!est.todas) h += "<button type=\"button\" class=\"pc-botao\" data-pc-acao=\"todas\">Ver em todas as redes</button>";
    if (opcoes.acaoExtra && opcoes.acaoExtra.rotulo) {
      h += "<button type=\"button\" class=\"pc-botao\" data-pc-acao=\"extra\">" + esc(opcoes.acaoExtra.rotulo) + "</button>";
    }
    h += "</div><p class=\"pc-nota\">Simulação aproximada, sem logos oficiais; números da interface são de exemplo.</p>";
    return h;
  }

  /* ------------------------------------------------------------------ */
  /* modal (só no navegador)                                              */
  /* ------------------------------------------------------------------ */
  var E = {dlg: null, post: null, redes: [], atual: null, zonas: false, temaApp: "claro", expandida: false,
    lamina: 0, origem: null, opcoes: {}, todas: false, overflow: ""};

  function resolverTema(pedido) {
    if (pedido === "claro" || pedido === "escuro") return pedido;
    var d = document.documentElement, t = d.getAttribute("data-theme");
    if (t === "dark") return "escuro";
    if (t === "light") return "claro";
    try {
      var cs = (getComputedStyle(d).colorScheme || "") + " " + (getComputedStyle(document.body).colorScheme || "");
      if (/\bdark\b/.test(cs) && !/\blight\b/.test(cs)) return "escuro";
      if (/\blight\b/.test(cs) && !/\bdark\b/.test(cs)) return "claro";
    } catch (e) { /* sem getComputedStyle */ }
    return (raiz.matchMedia && raiz.matchMedia("(prefers-color-scheme: dark)").matches) ? "escuro" : "claro";
  }

  function focaveis() {
    var lista = E.dlg.querySelectorAll("button:not([disabled]), [href], input, select, textarea, video[controls], [tabindex]:not([tabindex=\"-1\"])");
    return Array.prototype.filter.call(lista, function (el) {
      return el.getClientRects().length > 0 && el.getAttribute("tabindex") !== "-1";
    });
  }

  function garantirDialogo() {
    if (E.dlg && document.body.contains(E.dlg)) return E.dlg;
    var d = document.createElement("dialog");
    d.className = "pc-modal";
    d.setAttribute("aria-labelledby", "pc-titulo");
    d.setAttribute("aria-describedby", "pc-sub");
    d.innerHTML =
      "<div class=\"pc-caixa\">" +
      "<div class=\"pc-cabeca\"><div class=\"pc-titulos\"><h2 class=\"pc-titulo\" id=\"pc-titulo\">Prévia no celular</h2>" +
      "<p class=\"pc-sub\" id=\"pc-sub\"></p></div>" +
      "<button type=\"button\" class=\"pc-fechar\" data-pc-acao=\"fechar\" aria-label=\"Fechar prévia\">" + icone("fechar") + "</button></div>" +
      "<div class=\"pc-redes\" role=\"tablist\" aria-label=\"Redes\"></div>" +
      "<div class=\"pc-corpo\"><div class=\"pc-palco\" id=\"pc-palco\" role=\"tabpanel\"></div>" +
      "<div class=\"pc-ficha\" aria-live=\"polite\"></div></div></div>";
    document.body.appendChild(d);
    d.addEventListener("click", aoClicar);
    d.addEventListener("keydown", aoTeclar);
    d.addEventListener("close", limpar);
    d.addEventListener("cancel", function (ev) { ev.preventDefault(); fechar(); });
    E.dlg = d;
    return d;
  }

  function aoClicar(ev) {
    if (ev.target === E.dlg) { fechar(); return; }   /* clique fora da caixa */
    var aba = ev.target.closest ? ev.target.closest("[data-pc-rede]") : null;
    if (aba) { selecionar(aba.getAttribute("data-pc-rede"), true); return; }
    var bt = ev.target.closest ? ev.target.closest("[data-pc-acao]") : null;
    if (!bt) return;
    var acao = bt.getAttribute("data-pc-acao");
    if (acao === "fechar") fechar();
    else if (acao === "mais") { E.expandida = true; renderPalco(".pc-legenda"); }
    else if (acao === "zonas") { E.zonas = !E.zonas; renderPalco("[data-pc-acao=zonas]"); }
    else if (acao === "tema-app") { E.temaApp = E.temaApp === "escuro" ? "claro" : "escuro"; renderPalco("[data-pc-acao=tema-app]"); }
    else if (acao === "ant" || acao === "prox") {
      var n = (E.post.laminas && E.post.laminas.length) || 1;
      E.lamina = Math.max(0, Math.min(n - 1, E.lamina + (acao === "prox" ? 1 : -1)));
      renderPalco(acao === "prox" ? (E.lamina >= n - 1 ? ".pc-seta-ant" : ".pc-seta-prox") : (E.lamina === 0 ? ".pc-seta-prox" : ".pc-seta-ant"));
    } else if (acao === "todas") {
      E.todas = true;
      E.redes = PADRAO.slice();
      if (E.redes.indexOf(E.atual) < 0) E.redes.push(E.atual);
      E.redes.sort(function (a, b) { return ORDEM.indexOf(a) - ORDEM.indexOf(b); });
      renderAbas();
      renderPalco();
      focarAba();
    } else if (acao === "extra" && E.opcoes.acaoExtra && typeof E.opcoes.acaoExtra.executar === "function") {
      var fn = E.opcoes.acaoExtra.executar;
      E.origem = null;
      fechar();
      fn();
    }
  }

  function aoTeclar(ev) {
    if (ev.key === "Escape") { ev.preventDefault(); fechar(); return; }
    if (ev.key === "Tab") {
      var f = focaveis();
      if (!f.length) return;
      var ativo = document.activeElement, pri = f[0], ult = f[f.length - 1];
      if (ev.shiftKey && (ativo === pri || !E.dlg.contains(ativo))) { ev.preventDefault(); ult.focus(); }
      else if (!ev.shiftKey && (ativo === ult || !E.dlg.contains(ativo))) { ev.preventDefault(); pri.focus(); }
      return;
    }
    var aba = ev.target.closest ? ev.target.closest("[data-pc-rede]") : null;
    if (!aba) return;
    var i = E.redes.indexOf(E.atual), novo = -1;
    if (ev.key === "ArrowRight" || ev.key === "ArrowDown") novo = (i + 1) % E.redes.length;
    else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") novo = (i - 1 + E.redes.length) % E.redes.length;
    else if (ev.key === "Home") novo = 0;
    else if (ev.key === "End") novo = E.redes.length - 1;
    if (novo >= 0) { ev.preventDefault(); selecionar(E.redes[novo], true); }
  }

  function selecionar(k, focar) {
    if (!REDES[k]) return;
    E.atual = k;
    E.expandida = false;
    renderAbas();
    renderPalco();
    if (focar) focarAba();
  }

  function focarAba() {
    var b = E.dlg.querySelector("[data-pc-rede=\"" + E.atual + "\"]");
    if (b) {
      b.focus();
      if (b.scrollIntoView) b.scrollIntoView({block: "nearest", inline: "nearest"});
    }
  }

  function renderAbas() {
    E.dlg.querySelector(".pc-redes").innerHTML = E.redes.map(function (k) {
      var r = REDES[k], sel = k === E.atual;
      return "<button type=\"button\" role=\"tab\" class=\"pc-aba\" id=\"pc-aba-" + k + "\" data-pc-rede=\"" + k +
        "\" aria-selected=\"" + sel + "\" aria-controls=\"pc-palco\" tabindex=\"" + (sel ? "0" : "-1") +
        "\" title=\"" + esc(r.rotulo) + "\">" + esc(r.curto) + "</button>";
    }).join("");
  }

  function colocarMidia(caixa, idx) {
    var p = E.post, r = REDES[E.atual];
    var fotos = (p.laminas && p.laminas.length) ? p.laminas : [p.capa];
    var src = fotos[idx] || p.capa || "";
    var usaVideo = idx === 0 && p.video && (r.layout === "vertical" || r.layout === "story" || r.layout === "feed" ||
      r.layout === "texto_em_cima");
    caixa.textContent = "";
    if (usaVideo) {
      var v = document.createElement("video");
      v.muted = true; v.loop = true; v.autoplay = true; v.playsInline = true;
      v.setAttribute("playsinline", ""); v.setAttribute("muted", "");
      if (p.capa) v.poster = p.capa;
      v.src = p.video;
      v.setAttribute("aria-label", "Vídeo do post");
      caixa.appendChild(v);
      v.addEventListener("loadedmetadata", function () { mostrarCorte(v.videoWidth, v.videoHeight); });
      var pr = v.play && v.play();
      if (pr && pr.catch) pr.catch(function () { /* autoplay bloqueado: fica o poster */ });
      return;
    }
    if (!src) {
      caixa.innerHTML = "<span class=\"pc-sem-capa\">sem capa</span>";
      return;
    }
    var img = document.createElement("img");
    img.alt = "Capa do post";
    img.decoding = "async";
    var rapida = idx === 0 && p.capa_rapida && p.capa_rapida !== src ? p.capa_rapida : "";
    img.src = rapida || src;
    if (rapida) {  /* miniatura na hora; troca pela nítida quando chegar */
      var nitida = new Image();
      nitida.onload = function () { if (img.isConnected) img.src = src; };
      nitida.src = src;
    }
    img.addEventListener("load", function () { if (idx === 0) mostrarCorte(img.naturalWidth, img.naturalHeight); });
    img.addEventListener("error", function () {
      if (rapida && img.src !== rapida) img.src = rapida;
      else caixa.innerHTML = "<span class=\"pc-sem-capa\">capa não carregou</span>";
    });
    caixa.appendChild(img);
  }

  function mostrarCorte(w, h) {
    var alvo = E.dlg && E.dlg.querySelector("[data-pc-corte]");
    if (!alvo || !w || !h) return;
    var r = REDES[E.atual], prop = proporcaoDe(E.post, r, E.atual), c = calcularCorte(w, h, prop);
    if (!c) return;
    var base = w + "×" + h + ". ";
    alvo.innerHTML = esc(base) + (c.perde === 0 ? "<b class=\"pc-ok\">encaixa sem corte</b>"
      : "<b class=\"pc-alerta\">perde ~" + c.perde + "% " + esc(c.onde) + "</b> nesta rede");
  }

  function renderPalco(focarSeletor) {
    var p = E.post, k = E.atual, r = REDES[k];
    var est = {expandida: E.expandida, lamina: E.lamina, zonas: E.zonas, temaApp: E.temaApp, todas: E.todas};
    var palco = E.dlg.querySelector(".pc-palco");
    var escuraSempre = r.layout === "vertical" || r.layout === "story";
    palco.setAttribute("aria-labelledby", "pc-aba-" + k);
    palco.innerHTML = "<div class=\"pc-celular\" role=\"group\" aria-label=\"Como fica no " + esc(r.rotulo) + "\">" +
      "<div class=\"pc-tela pc-l-" + r.layout + " pc-e-" + r.estilo + (E.zonas ? " pc-mostra-zonas" : "") +
      "\" data-pc-app=\"" + (escuraSempre ? "escuro" : E.temaApp) + "\">" + montarTela(p, k, est) +
      "<i class=\"pc-home\" aria-hidden=\"true\"></i></div><i class=\"pc-notch\" aria-hidden=\"true\"></i></div>";
    E.dlg.querySelector(".pc-ficha").innerHTML = fichaHtml(p, k, est, E.opcoes);
    var caixas = palco.querySelectorAll("[data-pc-midia]");
    for (var i = 0; i < caixas.length; i++) colocarMidia(caixas[i], r.layout === "pin" ? 0 : E.lamina);
    if (!temMidia(p)) {
      var alvo = E.dlg.querySelector("[data-pc-corte]");
      if (alvo) alvo.textContent = "sem capa (post só de texto)";
    }
    if (p.avatar) {
      var avs = palco.querySelectorAll("[data-pc-avatar]");
      for (var j = 0; j < avs.length; j++) {
        var im = document.createElement("img");
        im.alt = "";
        im.src = p.avatar;
        avs[j].appendChild(im);
      }
    }
    if (focarSeletor) {
      var alvoFoco = E.dlg.querySelector(focarSeletor + ":not([disabled])") || E.dlg.querySelector(".pc-fechar");
      if (alvoFoco && alvoFoco.focus) alvoFoco.focus();
    }
  }

  function normalizarPost(post) {
    var p = {};
    for (var k in (post || {})) if (Object.prototype.hasOwnProperty.call(post, k)) p[k] = post[k];
    if (typeof p.laminas === "string") p.laminas = [p.laminas];
    if (Array.isArray(p.imagens) && !p.laminas) p.laminas = p.imagens;
    if (p.laminas && !p.laminas.length) p.laminas = null;
    if (!p.capa && p.laminas) p.capa = p.laminas[0];
    return p;
  }

  function abrir(post, opcoes) {
    if (typeof document === "undefined") return null;
    opcoes = opcoes || {};
    garantirDialogo();
    E.post = normalizarPost(post);
    E.opcoes = opcoes;
    E.origem = opcoes.origem || document.activeElement;
    E.todas = !!opcoes.todas;
    E.redes = E.todas ? PADRAO.slice() : redesDoPost(E.post);
    var pedida = opcoes.rede ? normalizarRede(opcoes.rede, E.post) : null;
    E.atual = (pedida && E.redes.indexOf(pedida) >= 0) ? pedida : E.redes[0];
    E.zonas = !!opcoes.zonas;
    E.expandida = false;
    E.lamina = 0;
    var tema = resolverTema(opcoes.tema || CONFIG.tema);
    E.dlg.setAttribute("data-pc-tema", tema);
    E.temaApp = opcoes.temaApp || tema;
    var sub = [E.post.canal, E.post.conta ? "@" + String(E.post.conta).replace(/^@/, "") : ""].filter(Boolean).join(" · ");
    E.dlg.querySelector(".pc-sub").textContent = sub || (E.post.titulo || "");
    renderAbas();
    renderPalco();
    if (!E.dlg.open) {
      E.overflow = document.documentElement.style.overflow;
      document.documentElement.style.overflow = "hidden";
      if (typeof E.dlg.showModal === "function") E.dlg.showModal();
      else E.dlg.setAttribute("open", "");
    }
    focarAba();
    return E.dlg;
  }

  function limpar() {
    if (!E.dlg) return;
    var vs = E.dlg.querySelectorAll("video");
    for (var i = 0; i < vs.length; i++) { try { vs[i].pause(); } catch (e) { /* ok */ } }
    var palco = E.dlg.querySelector(".pc-palco");
    if (palco) palco.innerHTML = "";
    document.documentElement.style.overflow = E.overflow || "";
    var o = E.origem;
    E.origem = null;
    if (o && o.focus && document.contains(o)) { try { o.focus(); } catch (e) { /* ok */ } }
  }

  function fechar() {
    if (!E.dlg) return;
    if (typeof E.dlg.close === "function" && E.dlg.open) E.dlg.close();   /* dispara "close" -> limpar */
    else { E.dlg.removeAttribute("open"); limpar(); }
  }

  function lerPostDoElemento(el) {
    var post = {};
    var bruto = el.getAttribute("data-previa");
    if (bruto) { try { post = JSON.parse(bruto); } catch (e) { post = {}; } }
    if (!post.capa) {
      var img = el.tagName === "IMG" ? el : el.querySelector("img");
      if (img) post.capa = img.currentSrc || img.src;
    }
    return post;
  }

  function prepararCapas(raizDom, seletor) {
    var els = (raizDom || document).querySelectorAll(seletor);
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (!/^(BUTTON|A)$/.test(el.tagName)) {
        if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "0");
        if (!el.hasAttribute("role")) el.setAttribute("role", "button");
      }
      if (!el.hasAttribute("aria-label")) el.setAttribute("aria-label", "Ver prévia no celular");
    }
  }

  /* Liga a prévia em todos os [data-previa] (inclusive os que aparecerem depois). */
  function ligar(raizDom, opcoes) {
    opcoes = opcoes || {};
    raizDom = raizDom || document;
    var seletor = opcoes.seletor || "[data-previa]";
    function abrirDe(el) {
      var o = {};
      for (var k in opcoes) if (Object.prototype.hasOwnProperty.call(opcoes, k)) o[k] = opcoes[k];
      o.origem = el;
      abrir(typeof opcoes.obterPost === "function" ? opcoes.obterPost(el) : lerPostDoElemento(el), o);
    }
    raizDom.addEventListener("click", function (ev) {
      var el = ev.target.closest && ev.target.closest(seletor);
      if (el && raizDom.contains(el)) { ev.preventDefault(); abrirDe(el); }
    });
    raizDom.addEventListener("keydown", function (ev) {
      if (ev.key !== "Enter" && ev.key !== " ") return;
      var el = ev.target.closest && ev.target.closest(seletor);
      if (el && el === ev.target) { ev.preventDefault(); abrirDe(el); }
    });
    prepararCapas(raizDom, seletor);
    if (typeof MutationObserver === "function") {
      new MutationObserver(function () { prepararCapas(raizDom, seletor); })
        .observe(raizDom.nodeType === 9 ? raizDom.documentElement : raizDom, {childList: true, subtree: true});
    }
  }

  function configurar(op) {
    for (var k in (op || {})) if (Object.prototype.hasOwnProperty.call(op, k)) CONFIG[k] = op[k];
    return CONFIG;
  }

  var api = {
    REDES: REDES, ORDEM: ORDEM, PADRAO: PADRAO,
    abrir: abrir, fechar: fechar, ligar: ligar, configurar: configurar,
    deItemAgenda: deItemAgenda, cortarLegenda: cortarLegenda, redesDoPost: redesDoPost,
    normalizarRede: normalizarRede, textoDaRede: textoDaRede, calcularCorte: calcularCorte,
    legendaHtml: legendaHtml, montarTela: montarTela, proporcaoDe: proporcaoDe
  };
  if (typeof module === "object" && module && module.exports) module.exports = api;
  if (raiz) raiz.PreviaCelular = api;
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this));
