# Aula 09 — UX para IA, Latência e Streaming com Gradio

> **Objetivo:** Traduzir os princípios de Design System para IA (vistos na Aula 02 com Streamlit) para o universo dos modelos generativos, usando Gradio como plataforma. Construir interfaces que comunicam incerteza, exibem o processo de geração em tempo real e coletam feedback humano de forma estruturada.

---

## O ponto de partida: o que já sabemos

Na Aula 02 estabelecemos quatro pilares de UX para sistemas de IA:

1. **Transparência e Explainability** — mostrar *por que* a IA chegou a um resultado.
2. **Gestão de Expectativa e Incerteza** — comunicar scores de confiança, nunca apresentar respostas como verdades absolutas.
3. **Design para Latência** — o usuário tolera espera, mas rejeita silêncio.
4. **Human-in-the-loop** — manter o humano no controle e coletar feedback para retreinamento.

Esses pilares foram aplicados no Streamlit. Agora vamos reaplica-los no Gradio — mas com uma diferença fundamental no modelo de execução que muda tudo.

---

## 1. O Modelo de Eventos do Gradio e por que ele importa para UX

### Revisitando o problema do Streamlit

No Streamlit, toda interação do usuário dispara um **rerun completo** do script. Isso significa que qualquer ajuste em um slider, qualquer clique de botão, faz o Python reexecutar tudo do topo ao fim.

Para interfaces simples isso funciona. Para modelos generativos — onde uma resposta pode levar segundos para ser gerada token a token — esse modelo cria um problema sério: **a interface fica congelada até o modelo terminar**.

Imagine pedir ao ChatGPT que esperasse gerar toda a resposta para só então exibir tudo de uma vez. A percepção de latência seria devastadora. O "efeito de digitação" que todos associam a interfaces de IA generativa existe precisamente para combater isso.

### O modelo orientado a eventos

O Gradio resolve isso com uma arquitetura diferente: em vez de reexecutar o script inteiro, ele conecta **eventos específicos a funções específicas**.

```
Streamlit:  Interação → Script inteiro roda de cima a baixo
Gradio:     Interação → Apenas a função vinculada ao evento é chamada
```

Essa distinção tem consequências diretas para os quatro pilares de UX:

| Pilar de UX             | Streamlit                          | Gradio                                  |
| ----------------------- | ---------------------------------- | --------------------------------------- |
| Transparência           | `st.spinner`, `st.status`          | `gr.Markdown` com status dinâmico       |
| Gestão de Incerteza     | `st.metric` + `st.progress`        | `gr.Label` com scores nativos           |
| Design para Latência    | Rerun bloqueia tudo                | Streaming nativo via geradores Python   |
| Human-in-the-loop       | Botões customizados + session_state | Sistema de `Flagging` nativo            |

---

## 2. Gerenciamento de Incerteza no Gradio

### O componente gr.Label

O Gradio tem um componente construído especificamente para exibir resultados probabilísticos: o `gr.Label`. Ele recebe um dicionário onde as chaves são os rótulos e os valores são as probabilidades — e renderiza automaticamente um ranking visual com barras de confiança.

Isso é diferente do Streamlit, onde você precisava compor manualmente `st.metric` + `st.progress`. No Gradio, a estrutura de dados *é* a interface.

```python
import gradio as gr


def classificar_texto(texto: str) -> dict:
    """
    Simula um classificador de sentimento com scores de confiança.
    Em produção, aqui entraria seu modelo real (transformers, sklearn, etc).
    """
    if not texto.strip():
        # Retornar dicionário vazio deixa o gr.Label em estado neutro
        return {}

    texto_lower = texto.lower()

    # Simulação de scores probabilísticos — a soma deve ser próxima de 1
    if any(palavra in texto_lower for palavra in ["ótimo", "excelente", "adorei", "bom"]):
        return {"Positivo": 0.88, "Neutro": 0.09, "Negativo": 0.03}
    elif any(palavra in texto_lower for palavra in ["péssimo", "horrível", "odeio", "ruim"]):
        return {"Negativo": 0.91, "Neutro": 0.07, "Positivo": 0.02}
    else:
        return {"Neutro": 0.61, "Positivo": 0.25, "Negativo": 0.14}


with gr.Blocks(title="Classificador de Sentimento") as demo:

    gr.Markdown("## 🧠 Classificador de Sentimento com Scores de Confiança")
    gr.Markdown(
        "Este classificador retorna **probabilidades**, não apenas um rótulo. "
        "Observe como scores diferentes communicam incerteza de forma diferente."
    )

    with gr.Row():
        # Coluna de entrada
        with gr.Column():
            input_texto = gr.Textbox(
                label="Texto para análise",
                placeholder="Digite uma frase sobre um produto, serviço ou experiência...",
                lines=4
            )
            botao_analisar = gr.Button("Analisar Sentimento", variant="primary")

        # Coluna de saída — gr.Label renderiza o dicionário como barras de confiança
        with gr.Column():
            output_label = gr.Label(
                label="Distribuição de Probabilidade",
                num_top_classes=3  # exibe os 3 rótulos com maiores scores
            )

    # Exemplos ajudam o usuário a entender o espaço de entrada
    gr.Examples(
        examples=[
            "O produto é excelente, superou minhas expectativas!",
            "Entrega atrasou três dias e o atendimento foi péssimo.",
            "Recebi o pedido ontem.",
        ],
        inputs=input_texto,
        label="Exemplos para testar"
    )

    # Conectar o evento de clique à função
    botao_analisar.click(
        fn=classificar_texto,
        inputs=input_texto,
        outputs=output_label
    )

    # Também responde ao Enter
    input_texto.submit(
        fn=classificar_texto,
        inputs=input_texto,
        outputs=output_label
    )

demo.launch()
```

### Regra mental

> Se sua função retorna um dicionário `{rótulo: probabilidade}`, use `gr.Label`. Ele traduz incerteza estatística em linguagem visual sem nenhuma linha extra de código.

---

## 3. Streaming de Respostas — O "Efeito ChatGPT"

### Por que streaming existe

Modelos de linguagem geram texto **token por token** — palavra por palavra, ou até sílaba por sílaba. Exibir cada token conforme ele é gerado serve a dois propósitos:

**Primeiro, reduz a percepção de latência.** Uma resposta que leva 8 segundos para ser gerada parece instantânea quando o usuário vê o texto aparecer progressivamente desde o primeiro segundo.

**Segundo, comunica que o sistema está trabalhando.** O usuário não precisa de spinner. O próprio texto em movimento *é* o feedback de progresso.

### Geradores Python como mecanismo de streaming

O Gradio implementa streaming de forma elegante: se sua função é um **gerador Python** (usa `yield` em vez de `return`), o Gradio automaticamente atualiza o componente de saída a cada valor produzido.

```python
import gradio as gr
import time


def gerar_resposta_streaming(pergunta: str):
    """
    Demonstra o padrão de streaming com um gerador Python.
    
    Em vez de return (que entrega tudo de uma vez),
    usamos yield para entregar o texto progressivamente.
    Gradio reconhece geradores e atualiza a UI a cada yield.
    """
    if not pergunta.strip():
        yield "Por favor, faça uma pergunta."
        return

    # Simulação de resposta — em produção, itere sobre os tokens do seu modelo
    resposta_completa = (
        f"Analisando sua pergunta: '{pergunta}'\n\n"
        "Esta é uma resposta simulada que aparece token por token, "
        "demonstrando como o streaming reduz a percepção de latência "
        "em interfaces de modelos generativos. "
        "O usuário vê o progresso imediatamente, sem esperar o fim da geração."
    )

    # Simular geração token a token
    texto_acumulado = ""
    for caractere in resposta_completa:
        texto_acumulado += caractere
        # yield entrega o estado atual do texto para o Gradio atualizar a UI
        yield texto_acumulado
        time.sleep(0.02)  # simula latência de geração


with gr.Blocks(title="Streaming Demo") as demo:

    gr.Markdown("## ⚡ Streaming de Respostas — O Efeito ChatGPT")
    gr.Markdown(
        "Observe como o texto aparece progressivamente. "
        "Compare mentalmente com uma interface que exibiria tudo de uma vez após 3 segundos de espera."
    )

    input_pergunta = gr.Textbox(
        label="Sua pergunta",
        placeholder="Pergunte qualquer coisa...",
        lines=2
    )

    botao = gr.Button("Gerar Resposta", variant="primary")

    # gr.Textbox como saída é suficiente para receber o stream de texto
    output_resposta = gr.Textbox(
        label="Resposta (gerada em streaming)",
        lines=6,
        interactive=False  # usuário não edita a saída
    )

    # Para streaming, adicionar streaming=True no evento
    botao.click(
        fn=gerar_resposta_streaming,
        inputs=input_pergunta,
        outputs=output_resposta,
        # Este parâmetro é o que ativa o comportamento de streaming
        # Sem ele, o Gradio esperaria o gerador terminar antes de atualizar a UI
    )

    input_pergunta.submit(
        fn=gerar_resposta_streaming,
        inputs=input_pergunta,
        outputs=output_resposta,
    )

demo.launch()
```

> **Nota importante:** Para streaming funcionar com geradores, a função deve usar `yield` — não `return`. O Gradio detecta automaticamente que a função é um gerador e trata cada `yield` como uma atualização parcial da interface.

### Padrão de acumulação de tokens

O detalhe crucial no exemplo acima é que a cada `yield` entregamos o texto **completo até aquele momento**, não apenas o novo fragmento. Isso garante que a saída no componente sempre reflita o estado atual da resposta, sem precisar de lógica de concatenação no lado do Gradio.

```
yield "Ol"              → componente exibe: "Ol"
yield "Olá"             → componente exibe: "Olá"
yield "Olá, tudo"       → componente exibe: "Olá, tudo"
yield "Olá, tudo bem?"  → componente exibe: "Olá, tudo bem?"
```

---

## 4. Human-in-the-Loop — O Sistema de Flagging

### O problema que o Flagging resolve

Na Aula 02, implementamos human-in-the-loop com botões customizados e `session_state`. Funciona, mas tem um custo: você precisa construir e manter a lógica de coleta de feedback manualmente.

O Gradio tem um mecanismo nativo para isso chamado **Flagging**. A ideia é simples: qualquer `gr.Interface` (e `gr.Blocks` com configuração) pode ter um botão de "Flag" que, quando clicado, salva automaticamente a entrada, a saída e um comentário opcional em um arquivo CSV local.

Isso cria um dataset de feedback estruturado que pode alimentar diretamente o processo de retreinamento.

### Flagging em gr.Interface

```python
import gradio as gr
import csv
import os
from datetime import datetime


def analisar_texto(texto: str) -> tuple[str, str]:
    """
    Retorna o resultado da análise e uma explicação.
    Retornar múltiplos valores popula múltiplos componentes de saída.
    """
    if not texto.strip():
        return "Aguardando entrada...", ""

    palavras = texto.lower().split()
    score = sum(1 for p in palavras if p in ["bom", "ótimo", "excelente", "adorei"])
    score -= sum(1 for p in palavras if p in ["ruim", "péssimo", "horrível", "odeio"])

    if score > 0:
        resultado = "😊 Positivo"
        explicacao = f"Encontradas {score} palavra(s) positivas no texto."
    elif score < 0:
        resultado = "😞 Negativo"
        explicacao = f"Encontradas {abs(score)} palavra(s) negativas no texto."
    else:
        resultado = "😐 Neutro"
        explicacao = "Nenhuma palavra fortemente positiva ou negativa identificada."

    return resultado, explicacao


# FlagCallback customizado para salvar feedback com timestamp
class FeedbackLogger(gr.SimpleCSVLogger):
    """
    Extensão do logger padrão que adiciona timestamp ao registro.
    Em produção, você poderia enviar para um banco de dados ou API.
    """
    def flag(self, flag_data, flag_option="", username=None):
        # Chama o comportamento padrão (salva em CSV)
        super().flag(flag_data, flag_option, username)


# gr.Interface com flagging configurado
demo = gr.Interface(
    fn=analisar_texto,
    inputs=gr.Textbox(
        label="Texto para análise",
        placeholder="Digite aqui...",
        lines=3
    ),
    outputs=[
        gr.Textbox(label="Resultado"),
        gr.Textbox(label="Explicação")
    ],
    title="🔍 Analisador com Feedback Humano",
    description=(
        "Analise o sentimento de um texto. Se o resultado estiver **errado**, "
        "clique em **Flag** para registrar o erro. "
        "Esses registros alimentam o processo de melhoria do modelo."
    ),
    examples=[
        ["O produto chegou rápido e é excelente!"],
        ["Péssima experiência, horrível atendimento."],
        ["Recebi o pedido na terça-feira."],
    ],
    # Configura o sistema de flagging nativo
    flagging_mode="manual",          # usuário decide quando flaggar
    flagging_options=["Errou o rótulo", "Explicação incorreta", "Outro"],
    flagging_dir="feedback_logs",    # pasta onde o CSV será salvo
)

demo.launch()
```

### Entendendo o arquivo de feedback

Após os usuários interagirem, o Gradio cria automaticamente um arquivo `feedback_logs/log.csv` com colunas para entrada, saída e flag. Esse arquivo é o ponto de partida para construir um dataset de retreinamento:

```
input,output_resultado,output_explicacao,flag,username,timestamp
"O produto é ótimo!","😊 Positivo","Encontradas 1 palavra(s) positivas","Errou o rótulo","",2024-01-15 10:23:44
```

---

## 5. Mão na Massa — Chatbot com Streaming e Feedback

Agora vamos unir os três conceitos em um único app: um chatbot que faz streaming de texto, exibe um score de confiança simulado e permite ao usuário avaliar a resposta com um sistema de like/dislike.

Este é o padrão de interface mais comum em produtos de IA generativa modernos.

```python
import gradio as gr
import time
import random
from datetime import datetime


# ─────────────────────────────────────────────
# CAMADA DE LÓGICA (simulando um modelo real)
# ─────────────────────────────────────────────

def calcular_confianca(pergunta: str) -> float:
    """
    Em produção: retornaria logprobs ou outro sinal de confiança do modelo.
    Aqui simulamos com base no comprimento da pergunta.
    Perguntas mais específicas tendem a gerar respostas mais confiantes.
    """
    if len(pergunta) > 50:
        return round(random.uniform(0.78, 0.95), 2)
    elif len(pergunta) > 20:
        return round(random.uniform(0.55, 0.77), 2)
    else:
        return round(random.uniform(0.30, 0.54), 2)


def gerar_resposta(pergunta: str, historico: list) -> tuple:
    """
    Simula um modelo de linguagem gerativo.
    
    Parâmetros:
        pergunta:  mensagem atual do usuário
        historico: lista de tuplas (pergunta, resposta) — conversa anterior
    
    Retorna:
        Um gerador de tokens (para streaming) e o score de confiança.
    
    Nota: Em uma integração real com OpenAI/Anthropic/Hugging Face,
    você iteraria sobre o stream da API em vez de simular com time.sleep.
    """
    confianca = calcular_confianca(pergunta)

    respostas_simuladas = {
        "default": (
            "Compreendi sua pergunta. Com base no contexto fornecido, "
            "posso indicar que este é um sistema de demonstração que simula "
            "o comportamento de um modelo de linguagem generativo. "
            "Em uma implementação real, aqui estaria a resposta do seu modelo, "
            "gerada token por token via streaming."
        )
    }

    resposta = respostas_simuladas["default"]

    return resposta, confianca


# ─────────────────────────────────────────────
# CAMADA DE ESTADO
# ─────────────────────────────────────────────

# Armazena feedback para análise posterior
# Em produção: persistir em banco de dados
registro_feedback = []


def salvar_feedback(pergunta: str, resposta: str, tipo: str):
    """Registra feedback do usuário com contexto completo."""
    registro_feedback.append({
        "timestamp": datetime.now().isoformat(),
        "pergunta": pergunta,
        "resposta": resposta,
        "feedback": tipo
    })
    return registro_feedback


# ─────────────────────────────────────────────
# CAMADA DE INTERFACE
# ─────────────────────────────────────────────

def processar_mensagem(pergunta: str, historico: list):
    """
    Função principal do chatbot.
    
    Esta é a função conectada ao evento de submit do chatbot.
    Ela é um gerador: yield a cada token atualiza o componente de chat.
    
    O Gradio gerencia o histórico automaticamente quando usamos gr.ChatInterface,
    mas aqui usamos gr.Blocks para ter mais controle sobre o layout.
    """
    if not pergunta.strip():
        # Não processar mensagens vazias
        yield historico, "", "", ""
        return

    resposta_completa, confianca = gerar_resposta(pergunta, historico)

    # Determinar nível de confiança para feedback visual
    if confianca >= 0.78:
        nivel = "🟢 Alta"
        descricao_confianca = f"Confiança: {int(confianca*100)}% — O modelo tem alta certeza nesta resposta."
    elif confianca >= 0.55:
        nivel = "🟡 Média"
        descricao_confianca = f"Confiança: {int(confianca*100)}% — Recomenda-se verificar informações importantes."
    else:
        nivel = "🔴 Baixa"
        descricao_confianca = f"Confiança: {int(confianca*100)}% — Esta resposta pode conter imprecisões."

    # Iniciar o streaming: adicionar a mensagem do usuário e uma resposta parcial
    historico_atual = historico + [[pergunta, ""]]

    # Gerar tokens progressivamente — cada yield atualiza o chat
    texto_parcial = ""
    for caractere in resposta_completa:
        texto_parcial += caractere
        historico_atual[-1][1] = texto_parcial
        yield historico_atual, descricao_confianca, nivel, resposta_completa
        time.sleep(0.015)

    # Yield final com resposta completa
    yield historico_atual, descricao_confianca, nivel, resposta_completa


# ─────────────────────────────────────────────
# CONSTRUÇÃO DO APP
# ─────────────────────────────────────────────

with gr.Blocks(title="AI Chatbot com Streaming e Feedback", theme=gr.themes.Soft()) as demo:

    # Estado interno — persiste entre interações sem rerun completo
    # Equivalente ao st.session_state do Streamlit
    estado_ultima_pergunta = gr.State("")
    estado_ultima_resposta = gr.State("")

    # ── Cabeçalho ──────────────────────────────────────────────
    gr.Markdown("# 🤖 Chatbot com Streaming, Confiança e Feedback Humano")
    gr.Markdown(
        "Este app demonstra os quatro pilares de UX para IA vistos na Aula 02, "
        "agora aplicados a um modelo generativo com Gradio:\n"
        "**Transparência** · **Gestão de Incerteza** · **Design para Latência** · **Human-in-the-loop**"
    )

    gr.Markdown("---")

    # ── Layout principal ────────────────────────────────────────
    with gr.Row():

        # Coluna esquerda: chat
        with gr.Column(scale=3):
            gr.Markdown("### 💬 Conversa")

            chatbot = gr.Chatbot(
                label="Histórico",
                height=400,
                show_copy_button=True,  # facilita copiar respostas
                bubble_full_width=False
            )

            with gr.Row():
                input_mensagem = gr.Textbox(
                    label="",
                    placeholder="Digite sua mensagem e pressione Enter...",
                    scale=4,
                    container=False
                )
                botao_enviar = gr.Button("Enviar ➤", variant="primary", scale=1)

            botao_limpar = gr.Button("🗑️ Limpar conversa", variant="secondary")

        # Coluna direita: feedback e confiança
        with gr.Column(scale=2):

            # ── Pilar: Gestão de Incerteza ──────────────────────
            gr.Markdown("### 📊 Gestão de Incerteza")
            output_confianca_texto = gr.Textbox(
                label="Análise de Confiança",
                lines=2,
                interactive=False,
                value="Aguardando resposta..."
            )
            output_nivel = gr.Textbox(
                label="Nível",
                interactive=False,
                value=""
            )

            gr.Markdown("---")

            # ── Pilar: Human-in-the-loop ────────────────────────
            gr.Markdown("### 👥 Human-in-the-loop")
            gr.Markdown(
                "Avalie a última resposta. "
                "Seu feedback é registrado para retreinamento do modelo."
            )

            with gr.Row():
                botao_like = gr.Button("👍 Resposta correta", variant="secondary")
                botao_dislike = gr.Button("👎 Resposta incorreta", variant="secondary")

            output_feedback_status = gr.Textbox(
                label="Status do Feedback",
                interactive=False,
                value=""
            )

            gr.Markdown("---")

            # ── Pilar: Transparência (exemplos) ─────────────────
            gr.Markdown("### 💡 Exemplos para testar")
            gr.Examples(
                examples=[
                    ["Explique o conceito de streaming em interfaces de IA"],
                    ["O que é human-in-the-loop e por que é importante?"],
                    ["Como funciona o sistema de confiança deste app?"],
                    ["Oi"],  # pergunta curta → confiança baixa simulada
                ],
                inputs=input_mensagem,
                label=""
            )

    # ─────────────────────────────────────────────
    # CONEXÃO DE EVENTOS
    # ─────────────────────────────────────────────

    def on_enviar(mensagem, historico):
        """Wrapper que captura a pergunta para o sistema de feedback."""
        return mensagem, historico

    # Evento de envio — conecta input ao processamento com streaming
    botao_enviar.click(
        fn=processar_mensagem,
        inputs=[input_mensagem, chatbot],
        outputs=[chatbot, output_confianca_texto, output_nivel, estado_ultima_resposta],
    ).then(
        # Após o streaming terminar, guardar a pergunta no estado
        fn=lambda msg: msg,
        inputs=input_mensagem,
        outputs=estado_ultima_pergunta
    ).then(
        # Limpar o campo de input após envio
        fn=lambda: "",
        outputs=input_mensagem
    )

    # Também responde ao Enter
    input_mensagem.submit(
        fn=processar_mensagem,
        inputs=[input_mensagem, chatbot],
        outputs=[chatbot, output_confianca_texto, output_nivel, estado_ultima_resposta],
    ).then(
        fn=lambda msg: msg,
        inputs=input_mensagem,
        outputs=estado_ultima_pergunta
    ).then(
        fn=lambda: "",
        outputs=input_mensagem
    )

    # Evento de feedback positivo
    def registrar_like(pergunta, resposta):
        salvar_feedback(pergunta, resposta, "positivo")
        total = len(registro_feedback)
        return f"✅ Feedback positivo registrado. Total acumulado: {total} avaliações."

    botao_like.click(
        fn=registrar_like,
        inputs=[estado_ultima_pergunta, estado_ultima_resposta],
        outputs=output_feedback_status
    )

    # Evento de feedback negativo
    def registrar_dislike(pergunta, resposta):
        salvar_feedback(pergunta, resposta, "negativo")
        total = len(registro_feedback)
        positivos = sum(1 for r in registro_feedback if r["feedback"] == "positivo")
        negativos = total - positivos
        return (
            f"🔴 Feedback negativo registrado. "
            f"Total: {total} avaliações ({positivos} positivos, {negativos} negativos)."
        )

    botao_dislike.click(
        fn=registrar_dislike,
        inputs=[estado_ultima_pergunta, estado_ultima_resposta],
        outputs=output_feedback_status
    )

    # Limpar histórico do chat
    botao_limpar.click(
        fn=lambda: ([], "Aguardando resposta...", "", ""),
        outputs=[chatbot, output_confianca_texto, output_nivel, output_feedback_status]
    )

demo.launch()
```

---

## 6. Conectando um Modelo Real (OpenAI / Anthropic)

O app acima funciona com dados simulados. Trocar a camada de simulação por uma chamada real a uma API de LLM exige apenas alterar a função `gerar_resposta`. A estrutura do app permanece idêntica.

```python
# Exemplo de integração com a API da OpenAI
# pip install openai

import openai
import gradio as gr


# Boas práticas: nunca hardcode a chave de API
# Use variável de ambiente: export OPENAI_API_KEY="sua-chave"
client = openai.OpenAI()


def gerar_com_streaming(pergunta: str, historico: list):
    """
    Integração real com OpenAI usando streaming.
    
    O cliente OpenAI suporta streaming nativo — ao iterar sobre
    stream.choices[0].delta.content, recebemos tokens progressivamente.
    Cada token é concatenado e entregue via yield para o Gradio.
    """
    # Converter histórico do formato Gradio para formato OpenAI
    mensagens = []
    for pergunta_anterior, resposta_anterior in historico:
        mensagens.append({"role": "user", "content": pergunta_anterior})
        mensagens.append({"role": "assistant", "content": resposta_anterior})

    # Adicionar mensagem atual
    mensagens.append({"role": "user", "content": pergunta})

    # Chamada à API com stream=True
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensagens,
        stream=True,            # ativa o streaming
        max_tokens=500,
        temperature=0.7
    )

    historico_atual = historico + [[pergunta, ""]]
    texto_parcial = ""

    # Iterar sobre os chunks de tokens retornados pela API
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            texto_parcial += delta
            historico_atual[-1][1] = texto_parcial
            # yield atualiza o chat a cada token recebido
            yield historico_atual


# App simplificado usando gr.ChatInterface
# gr.ChatInterface gerencia o histórico automaticamente
demo = gr.ChatInterface(
    fn=gerar_com_streaming,
    title="💬 Chatbot com GPT-4 e Streaming Real",
    description="Cada token aparece conforme é gerado pela API da OpenAI.",
    examples=[
        "O que é streaming em LLMs?",
        "Explique o conceito de tokens em 3 frases.",
    ],
)

demo.launch()
```

### Regra mental

> O streaming no Gradio é transparente: se sua função API suporta iteração de chunks (OpenAI, Anthropic, Hugging Face), basta iterar e fazer `yield`. A interface se atualiza automaticamente.

---

## 7. Tabela Comparativa Final — Os Quatro Pilares em Cada Ferramenta

| Pilar                  | Streamlit (Aula 02)                              | Gradio (Aula 09)                                           |
| ---------------------- | ------------------------------------------------ | ---------------------------------------------------------- |
| Transparência          | `st.spinner`, `st.status` com passos             | `gr.Markdown` dinâmico via `.then()` encadeado             |
| Gestão de Incerteza    | `st.metric` + `st.progress` compostos manualmente | `gr.Label` com dicionário `{rótulo: probabilidade}`        |
| Design para Latência   | Rerun bloqueia; `st.cache_data` mitiga           | Streaming nativo com geradores Python + `yield`            |
| Human-in-the-loop      | Botões customizados + `session_state`            | `flagging_mode` nativo ou botões com `gr.State`            |

---

## 8. Checklist do App de IA com Gradio

- Os scores de confiança estão visíveis e interpretáveis?
- O usuário consegue distinguir visualmente alta, média e baixa confiança?
- As respostas longas usam streaming (nenhum spinner estático para geração de texto)?
- Existe algum mecanismo para o usuário sinalizar erros do modelo?
- Os feedbacks negativos são armazenados de forma estruturada?
- Exemplos de uso estão disponíveis via `gr.Examples`?
- Mensagens de estado vazias (`"Aguardando..."`) cobrem o estado inicial?

---

## Referências

- [Gradio — Documentação oficial](https://www.gradio.app/docs)
- [Gradio — Streaming](https://www.gradio.app/guides/streaming-outputs)
- [Gradio — Flagging](https://www.gradio.app/guides/using-flagging)
- [Gradio — State](https://www.gradio.app/guides/state-in-blocks)
- [Hugging Face Spaces — Deploy de apps Gradio](https://huggingface.co/spaces)
- Ben Shneiderman — *Designing Human-Centered AI*
- Stuart Russell — *Human Compatible*
- Chip Huyen — *Designing Machine Learning Systems*
