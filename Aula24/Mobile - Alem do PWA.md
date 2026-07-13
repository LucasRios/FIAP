# Aula 13 — Mobile: Além do PWA

## Objetivo

Entender quando o PWA não é suficiente, conhecer as opções para empacotar um app web como app nativo sem abandonar Python/JavaScript, e mapear o caminho de evolução do front-end de IA em mobile — do PWA ao app nativo real.

---

# 1. Os Limites do PWA

Na aula anterior instalamos nosso app como PWA. Mas ao testar no celular, você pode encontrar limitações:

**No iOS (Safari):**
- Notificações push só a partir do iOS 16.4 e apenas para apps adicionados à tela inicial
- Acesso à câmera e microfone funciona, mas com restrições em contextos específicos
- Não aparece na App Store — usuários precisam saber o processo de "Adicionar à Tela de Início"
- Alguns recursos de background (sync, execução em background) ainda são limitados

**No Android:**
- PWA funciona muito melhor — Chrome suporta quase todos os recursos da spec
- Pode aparecer no Google Play via [Trusted Web Activity (TWA)](https://developer.chrome.com/docs/android/trusted-web-activity/)
- Mas sem uma presença na App Store do iOS, parte significativa dos usuários fica de fora

**Para apps de IA específicamente:**
- Modelos que rodam localmente (on-device) precisam de acesso nativo ao hardware
- Inferência em tempo real com câmera (visão computacional) precisa de APIs nativas
- Apps que precisam funcionar 100% offline com modelos grandes precisam de storage nativo

---

# 2. O Mapa da Evolução Mobile

```
Nível 1 — PWA (Aula 12)
  └─ Sua app web com manifest + service worker
  └─ Instalável, tela cheia, sem barra do browser
  └─ Não precisa de nova tecnologia

Nível 2 — WebView Wrapper
  └─ Empacota sua app web em um shell nativo
  └─ Tecnologias: Capacitor, Cordova
  └─ Pode ser publicado na App Store
  └─ Acessa APIs nativas via plugins

Nível 3 — Framework Híbrido
  └─ Escreve JavaScript/TypeScript uma vez, compila para nativo
  └─ Tecnologias: React Native, Expo, Ionic
  └─ UI nativa em cada plataforma
  └─ Abandona Python — chama sua FastAPI via HTTP

Nível 4 — App Nativo
  └─ Swift (iOS) ou Kotlin (Android) puro
  └─ Performance máxima, acesso total ao hardware
  └─ Dois codebases diferentes para iOS e Android
  └─ Mais trabalhoso, melhor resultado
```

Para o desenvolvedor de front-end de IA que vem de Python, o caminho natural é:
**PWA → Capacitor (wrapper) → Expo/React Native (híbrido)** — deixando o modelo de IA sempre no back-end FastAPI.

---

# 3. Capacitor — Sua Web App Dentro de um App Nativo

O Capacitor (criado pela equipe do Ionic) pega qualquer aplicação web e a empacota dentro de um shell iOS/Android. O app roda em uma WebView, mas tem acesso às APIs nativas via plugins JavaScript.

```bash
# Pré-requisitos
npm install @capacitor/core @capacitor/cli
npx cap init "Análise de IA" "br.edu.fiap.analise" --web-dir build
```

**O desafio com Streamlit/Gradio:** eles geram HTML dinâmico no servidor. O Capacitor precisa de arquivos estáticos (HTML/JS/CSS).

A solução: usar o **iframe approach** — sua web app roda como um servidor externo e o app nativo exibe via iframe ou WebView apontando para a URL.

```javascript
// capacitor.config.json
{
  "appId": "br.edu.fiap.analise",
  "appName": "Análise de IA",
  "webDir": "www",
  "server": {
    "url": "https://meu-app.streamlit.app",  // aponta para o Streamlit Cloud
    "cleartext": false
  },
  "plugins": {
    "SplashScreen": {
      "launchShowDuration": 2000,
      "backgroundColor": "#FF4B4B"
    }
  }
}
```

Com essa configuração, o Capacitor cria um app nativo que exibe seu Streamlit numa WebView — com ícone na App Store, splash screen, e acesso a plugins nativos como câmera e notificações push.

```bash
# Gerar o projeto iOS/Android
npx cap add ios
npx cap add android
npx cap sync

# Abrir no Xcode (iOS)
npx cap open ios

# Abrir no Android Studio
npx cap open android
```

---

# 4. Expo Web — Para Quem Quer Ir Além

O Expo é um framework sobre React Native que permite escrever componentes uma vez e compilar para iOS, Android e Web. A parte interessante para o desenvolvedor de IA: o back-end continua sendo sua FastAPI em Python — o Expo só substitui o front-end.

```bash
npx create-expo-app analise-ia --template blank-typescript
cd analise-ia
```

```typescript
// App.tsx — chamando a FastAPI que você já construiu
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';

const API_URL = 'https://meu-backend.aws.com';

export default function App() {
  const [texto, setTexto] = useState('');
  const [resultado, setResultado] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  const analisar = async () => {
    setCarregando(true);
    try {
      const resposta = await fetch(`${API_URL}/v1/analise/sentimento`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'sua-chave-aqui'
        },
        body: JSON.stringify({ texto })
      });
      const dados = await resposta.json();
      setResultado(`${dados.sentimento} (${(dados.confianca * 100).toFixed(0)}%)`);
    } catch {
      setResultado('Erro ao conectar com o servidor.');
    } finally {
      setCarregando(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.titulo}>Análise de IA</Text>
      <TextInput
        style={styles.input}
        multiline
        placeholder="Cole o texto para análise..."
        value={texto}
        onChangeText={setTexto}
      />
      <TouchableOpacity style={styles.botao} onPress={analisar} disabled={carregando}>
        {carregando ? <ActivityIndicator color="#FFF" /> : <Text style={styles.botaoTexto}>Analisar</Text>}
      </TouchableOpacity>
      {resultado && <Text style={styles.resultado}>{resultado}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#FFF' },
  titulo: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  input: { borderWidth: 1, borderColor: '#CCC', borderRadius: 8, padding: 12, height: 120, marginBottom: 16 },
  botao: { backgroundColor: '#FF4B4B', padding: 16, borderRadius: 8, alignItems: 'center' },
  botaoTexto: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  resultado: { marginTop: 20, fontSize: 18, textAlign: 'center' }
});
```

O back-end continua sendo exatamente a FastAPI construída nas Aulas 1-4. O front-end mobile chama os mesmos endpoints — a separação de responsabilidades que construímos paga dividendos aqui.

---

# 5. Trusted Web Activity — PWA na Google Play Store

Se você quiser publicar seu PWA na Google Play Store sem escrever uma linha de código nativo, o TWA (Trusted Web Activity) permite isso:

```bash
# Instala a ferramenta da Google para gerar o app TWA
npm install -g @bubblewrap/cli

bubblewrap init --manifest https://meu-app.com/manifest.json
bubblewrap build
```

O resultado é um `.aab` (Android App Bundle) que você sobe para o Google Play. O app exibe sua web app em tela cheia — sem barra do browser, com acesso aos recursos PWA que você já implementou.

**Limitação:** funciona apenas no Android. Para iOS, não há equivalente oficial — você precisa do Capacitor ou de um app nativo.

---

# 6. Quando Cada Abordagem Faz Sentido

| Situação | Abordagem |
|---|---|
| Demo, portfólio, uso interno | PWA — zero custo de desenvolvimento extra |
| App para distribuir para usuários sem conhecimento técnico | Capacitor (WebView wrapper) |
| App que precisa de câmera, GPS ou notificações nativas | Capacitor com plugins |
| Produto que compete com apps nativos em UI e performance | Expo / React Native |
| App que roda o modelo no dispositivo (on-device AI) | App nativo (Swift/Kotlin) |
| Publicar na Play Store sem código nativo (Android only) | Trusted Web Activity |

---

# 7. A Perspectiva do Front-end de IA

O padrão que emerge para o front-end de IA em mobile é:

```
Modelo de IA (Claude, GPT, modelo local)
  ↓
FastAPI (back-end Python) — o mesmo que você construiu
  ↓
HTTP / REST
  ↓
┌────────────────┬──────────────────┬─────────────────┐
│ Streamlit/     │ PWA / Capacitor  │ React Native /  │
│ Gradio (web)   │ (instalável)     │ Expo (nativo)   │
└────────────────┴──────────────────┴─────────────────┘
```

O back-end é o mesmo. O front-end se adapta ao contexto de uso. Isso é exatamente o que a separação front/back que construímos neste semestre habilita.

A evolução natural para um desenvolvedor de front-end de IA:
1. Domine a stack web (Streamlit, Gradio, FastAPI) — feito neste semestre
2. Publique via PWA — simples, sem custo adicional
3. Empacote com Capacitor quando precisar de distribuição via loja
4. Aprenda React Native quando o produto justificar UI totalmente nativa

---

# Referências

- [Capacitor — Documentação](https://capacitorjs.com/docs)
- [Expo — Documentação](https://docs.expo.dev)
- [Trusted Web Activity — Google](https://developer.chrome.com/docs/android/trusted-web-activity/)
- [React Native](https://reactnative.dev)
- [Bubblewrap — Google](https://github.com/GoogleChromeLabs/bubblewrap)
- [On-device AI — MediaPipe](https://developers.google.com/mediapipe)
