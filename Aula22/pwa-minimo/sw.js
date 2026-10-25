// sw.js — service worker mínimo, com um console.log em cada etapa do ciclo de vida
const VERSAO = "v4";
const CACHE = `pwa-minimo-${VERSAO}`;
const ARQUIVOS = ["offline.html", "icones/icone-192.png"];

// INSTALL: roda uma vez por versão do sw.js. Guarda o que vamos precisar sem rede.
self.addEventListener("install", (evento) => {
  console.log("[sw] install", VERSAO);
  evento.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ARQUIVOS))
  );
});

// ACTIVATE: a versão nova assume. Hora de apagar os caches das versões antigas.
self.addEventListener("activate", (evento) => {
  console.log("[sw] activate", VERSAO);
  evento.waitUntil(
    caches.keys().then((nomes) =>
      Promise.all(nomes.filter((n) => n !== CACHE).map((n) => caches.delete(n)))
    )
  );
});

// Rede primeiro, guardando uma cópia; sem rede, a cópia — MARCADA como cópia.
async function redePrimeiroComCopia(pedido) {
  const cache = await caches.open(CACHE);
  try {
    const resposta = await fetch(pedido);
    await cache.put(pedido, resposta.clone());     // clone: o corpo de uma resposta só pode ser lido uma vez
    console.log("[sw] dados.json: rede (cópia guardada)");
    return resposta;
  } catch (erro) {
    const guardada = await cache.match(pedido);
    if (!guardada) throw erro;                      // nunca houve um GET com rede: não há cópia
    console.log("[sw] dados.json: sem rede, devolvendo a cópia");
    const cabecalhos = new Headers(guardada.headers);
    cabecalhos.set("X-Origem", "cache");            // a página precisa saber que o dado é velho
    return new Response(await guardada.blob(), { status: guardada.status, headers: cabecalhos });
  }
}

// FETCH: TODO pedido de rede das páginas controladas passa por aqui.
self.addEventListener("fetch", (evento) => {
  const url = new URL(evento.request.url);
  if (url.pathname.endsWith("/dados.json") && url.searchParams.get("estrategia") === "cache") {
    evento.respondWith(redePrimeiroComCopia(evento.request));
    return;
  }

  if (evento.request.mode === "navigate") {
    // Abrir ou recarregar a página: tenta a rede; sem rede, a página offline.
    evento.respondWith(
      fetch(evento.request).catch(() => caches.match("offline.html"))
    );
  }
  // Os demais pedidos não são tocados: seguem para a rede normalmente.
});
