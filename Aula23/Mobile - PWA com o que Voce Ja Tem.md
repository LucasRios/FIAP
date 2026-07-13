# Aula 12 — Mobile: PWA com o que Você Já Tem

## Objetivo

Transformar os apps Streamlit e Gradio já construídos em Progressive Web Apps — instaláveis na tela inicial do celular sem precisar de loja de apps. Entender o que um PWA é, o que ele não é, e por que essa é a entrada mais natural para o front-end de IA em mobile.

---

# 1. O Problema Mobile do Desenvolvedor de IA

Você construiu um app Streamlit que analisa notícias. Funciona bem no desktop. Mas o usuário acessa pelo celular e a experiência é ruim — a interface não é responsiva, não tem ícone na tela inicial, não funciona offline, aparece a barra do browser tomando espaço.

As opções tradicionais para resolver isso são complexas:
- Criar um app nativo (Swift/Kotlin) exige aprender uma nova linguagem e plataforma
- Criar um app React Native ou Flutter exige abandonar Python e a stack que você já sabe
- Publicar na App Store/Google Play exige contas de desenvolvedor e processo de aprovação

O **PWA (Progressive Web App)** é o caminho do meio: você faz pequenas adições ao que já existe e o app passa a se comportar como um app nativo — ícone na tela inicial, splash screen, funciona em tela cheia sem barra do browser.

---

# 2. O que é um PWA

Um PWA é uma aplicação web que cumpre três critérios técnicos:

**1. HTTPS:** toda comunicação precisa ser segura. Se você já fez o deploy na Aula 11 com certificado SSL, esse critério já está cumprido.

**2. Web App Manifest:** um arquivo JSON que descreve o app (nome, ícone, cor, modo de exibição). O browser lê esse arquivo para saber como instalar o app.

**3. Service Worker:** um script JavaScript que roda em background, intercepta requisições de rede e habilita funcionalidades offline. Para nossos apps, o service worker mínimo já é suficiente.

```
O que um PWA oferece:
  ✅ Instalável na tela inicial (Android e iOS)
  ✅ Abre em tela cheia sem barra do browser
  ✅ Splash screen personalizada
  ✅ Funciona com conexão instável (com cache)
  ✅ Notificações push (com permissão do usuário)
  ✅ Ícone de app com badge de notificação

O que um PWA não oferece:
  ❌ Acesso a Bluetooth, NFC, sensores avançados do hardware
  ❌ Suporte completo no iOS (algumas limitações no Safari)
  ❌ Distribuição via App Store (possível via wrappers, mas não nativo)
  ❌ Notificações push no iOS Safari (apenas no iOS 16.4+)
```

---

# 3. PWA com Streamlit

O Streamlit não oferece suporte nativo a PWA, mas você pode adicionar os arquivos necessários manualmente usando `st.components.v1`.

```python
# app.py — injetar o manifest e registrar o service worker
import streamlit as st
import streamlit.components.v1 as components

# Injeta o link para o manifest e o script de registro do service worker
# via um componente HTML customizado
components.html("""
<link rel="manifest" href="/manifest.json">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/sw.js').then(function(registration) {
        console.log('Service Worker registrado:', registration.scope);
      });
    });
  }
</script>
""", height=0)
```

**Problema:** o Streamlit serve arquivos estáticos a partir de um diretório específico. O `manifest.json` e o `sw.js` precisam estar acessíveis via URL.

A solução mais prática para PWA com Streamlit é usar um **proxy Nginx** na frente — que serve os arquivos estáticos do PWA e encaminha o restante para o Streamlit.

---

# 4. PWA com Gradio — Abordagem Direta

O Gradio tem suporte nativo para customização de cabeçalhos HTML, o que torna a implementação de PWA mais direta:

```python
import gradio as gr

# Cabeçalhos HTML customizados que o Gradio injeta no <head>
cabecalho_pwa = """
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#FF4B4B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Análise de IA">
<link rel="apple-touch-icon" href="/icone-192.png">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
"""

with gr.Blocks(
    title="Análise de IA",
    head=cabecalho_pwa,
    theme=gr.themes.Soft()
) as demo:
    gr.Markdown("## Análise de Notícias")
    # ... resto da interface

demo.launch()
```

---

# 5. O Web App Manifest

O `manifest.json` diz ao browser como instalar e exibir o app:

```json
{
  "name": "Análise de IA — Sprint FIAP",
  "short_name": "AnáliseIA",
  "description": "Análise de sentimento e resumo de notícias com IA",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFFFF",
  "theme_color": "#FF4B4B",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icone-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icone-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshot-mobile.png",
      "sizes": "390x844",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ]
}
```

Campos importantes:

- `display: "standalone"` — abre sem barra do browser, como um app nativo
- `start_url` — qual URL abre quando o usuário toca no ícone
- `icons` — ícone em dois tamanhos mínimos (192 e 512px). Use o [maskable.app](https://maskable.app) para gerar ícones com área segura para Android

---

# 6. O Service Worker Mínimo

Para apps de IA conectados a APIs externas, o service worker principal objetivo é registrar o app como PWA — não necessariamente funcionar offline. Um service worker mínimo cumpre esse papel:

```javascript
// sw.js
const CACHE_VERSION = 'v1';
const CACHE_NAME = `analise-ia-${CACHE_VERSION}`;

// Arquivos para cachear (assets estáticos)
const ARQUIVOS_ESTATICOS = [
  '/',
  '/icone-192.png',
  '/icone-512.png',
];

// Instalação — faz cache dos arquivos estáticos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ARQUIVOS_ESTATICOS))
  );
});

// Fetch — tenta rede primeiro; se falhar, serve do cache
self.addEventListener('fetch', (event) => {
  // Não intercepta chamadas à API (deixa passar direto)
  if (event.request.url.includes('/v1/')) {
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
```

O ponto crítico: **não intercepte chamadas de API**. Se o service worker tentar cachear respostas do modelo de IA, o usuário vai ver respostas antigas — o comportamento mais confuso possível num app de IA.

---

# 7. Nginx como Proxy — Servindo Front + PWA Files

Para o deploy na AWS (EC2 ou Fargate), o Nginx resolve o problema de servir os arquivos estáticos do PWA:

```nginx
# nginx.conf
server {
    listen 80;

    # Arquivos estáticos do PWA (manifest, service worker, ícones)
    location /manifest.json {
        root /etc/nginx/pwa;
        add_header Content-Type application/manifest+json;
    }

    location /sw.js {
        root /etc/nginx/pwa;
        add_header Content-Type application/javascript;
        add_header Service-Worker-Allowed /;
    }

    location /icone-192.png {
        root /etc/nginx/pwa;
    }

    location /icone-512.png {
        root /etc/nginx/pwa;
    }

    # Todo o resto vai para o Streamlit
    location / {
        proxy_pass http://frontend:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```yaml
# docker-compose.yml atualizado
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./pwa:/etc/nginx/pwa    # pasta com manifest.json, sw.js, ícones
    depends_on:
      - frontend
      - backend

  frontend:
    build: ./frontend
    # não expõe porta diretamente — só o nginx acessa

  backend:
    build: ./backend
    # não expõe porta diretamente — só o nginx acessa
```

---

# 8. Testando o PWA

```bash
# No Chrome DevTools (F12):
# 1. Aba Application → Manifest: verifica se o manifest foi carregado
# 2. Aba Application → Service Workers: verifica se o SW está registrado
# 3. Aba Lighthouse → Mobile: gera score de PWA

# No celular:
# Android Chrome: botão "Adicionar à tela inicial" aparece automaticamente
# iOS Safari: menu compartilhar → "Adicionar à Tela de Início"
```

O score mínimo do Lighthouse para ser considerado um PWA instalável é 100% nos critérios de PWA — HTTPS, manifest válido e service worker registrado.

---

# Referências

- [MDN — Progressive Web Apps](https://developer.mozilla.org/pt-BR/docs/Web/Progressive_web_apps)
- [web.dev — PWA](https://web.dev/progressive-web-apps/)
- [Maskable Icons](https://maskable.app)
- [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview/)
- [Gradio — Custom HTML](https://www.gradio.app/guides/custom-CSS-and-JS)
