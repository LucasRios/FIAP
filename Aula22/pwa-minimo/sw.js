// sw.js — service worker mínimo, com um console.log em cada etapa do ciclo de vida
const VERSAO = "v1";
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

// FETCH: TODO pedido de rede das páginas controladas passa por aqui.
self.addEventListener("fetch", (evento) => {
  if (evento.request.mode === "navigate") {
    // Abrir ou recarregar a página: tenta a rede; sem rede, a página offline.
    evento.respondWith(
      fetch(evento.request).catch(() => caches.match("offline.html"))
    );
  }
  // Os demais pedidos não são tocados: seguem para a rede normalmente.
});
