# Aula 3 — Interatividade Real
## Input de Dados, Estado e Callbacks no Streamlit

Avançamos do dashboard estático para a aplicação interativa de verdade. O objetivo não é apenas adicionar sliders e botões, mas compreender como o Streamlit executa, reexecuta e preserva (ou não) informações ao longo do uso.

Em sistemas de IA, interatividade não é detalhe estético:
É o mecanismo que permite ajustar hiperparâmetros, testar hipóteses, comparar resultados e criar ciclos de aprendizado humano + máquina.

O ponto central desta aula é entender estado.

---

## 1. O Desafio da “Amnésia” do Streamlit

Como visto nas aulas anteriores, o Streamlit funciona sob um modelo simples e radical:

Qualquer interação do usuário provoca a reexecução completa do script, do topo ao fim.

Exemplos:

- Mover um slider → re-run
- Digitar um texto → re-run
- Clicar em um botão → re-run

Esse comportamento é intencional e traz previsibilidade, mas gera um problema fundamental.

### O problema da amnésia

Variáveis Python comuns não sobrevivem ao re-run.

Exemplo clássico:

```python
historico = []

if st.button("Executar"):
    historico.append("nova execução")

st.write(historico)
```

Mesmo clicando várias vezes, a lista sempre volta vazia.
Isso acontece porque, a cada interação, o script começa do zero e historico é recriado.

Em aplicações de IA, precisamos conseguir manter:

- histórico de execuções
- resultados anteriores
- parâmetros já testados
- feedback do usuário

Para isso, precisamos de memória persistente.

---

## 2. Widgets de Entrada: o toolkit de controle da IA

Antes de falar em estado, precisamos entender os inputs.
Cada widget em Streamlit não é apenas um elemento visual — ele representa um controle semântico do sistema de IA.

### Widgets e seus papéis em IA

| Widget | Papel no Sistema de IA | Exemplos |
|---------|------------------------|----------|
| st.slider | Parâmetros contínuos | learning rate, threshold |
| st.select_slider | Escalas ordenadas | nível de verbosidade |
| st.number_input | Parâmetros exatos | épocas, número de vizinhos |
| st.multiselect | Seleção de features | colunas do dataset |
| st.file_uploader | Ingestão de dados | CSV, imagens, áudio |
| st.text_input / st.text_area | Linguagem natural | prompts, descrições |

Exemplo:

```python
learning_rate = st.slider(
    "Taxa de Aprendizado",
    0.001, 0.1, 0.01
)
```

Esse código cria:

- um elemento visual
- uma variável Python sincronizada com a UI

Em Streamlit, interface e lógica são a mesma coisa.
Não existe separação rígida entre front-end e back-end.

---

## 3. O Ciclo de Vida da Aplicação Streamlit

Para dominar interatividade, precisamos então internalizar este modelo mental:

1. O script sempre começa do topo
2. Widgets capturam valores do usuário
3. O código usa esses valores
4. O script termina
5. Nova interação → tudo recomeça

Sem estado explícito, nada é lembrado.

Esse modelo é simples, mas exige disciplina arquitetural.

---

## 4. st.session_state: a memória da aplicação

O st.session_state é o mecanismo que transforma um “site” em uma aplicação interativa real.

Ele funciona como um dicionário persistente, mantido entre re-runs enquanto a sessão do usuário estiver ativa.

Uma analogia útil:

Pense no session_state como um quadro branco que o Streamlit não apaga quando o script reinicia.

### Padrão essencial: inicialização

```python
if "contador_treinos" not in st.session_state:
    st.session_state.contador_treinos = 0
```

Esse padrão garante que:

- o valor exista desde o primeiro run
- ele não seja sobrescrito nos próximos

### Uso prático

```python
if st.button("Simular Treinamento"):
    st.session_state.contador_treinos += 1

st.write(
    f"Treinos nesta sessão: {st.session_state.contador_treinos}"
)
```

Agora o valor persiste corretamente.

---

## 5. Inputs como estado (uso de key)

Widgets podem ser diretamente ligados ao estado usando o argumento key.

Exemplo:

```python
st.slider(
    "Epochs",
    1, 100, 10,
    key="epochs"
)
```

Agora, em qualquer parte do código:

```python
st.session_state.epochs
```

contém o valor atual do slider.

Esse padrão cria uma arquitetura limpa:

- Sidebar → controla estado global
- Área principal → consome estado
- A UI inteira reage de forma previsível

---

## 6. Botões: gatilhos, não estado

Um erro comum é tratar botões como variáveis persistentes.

Importante:

st.button retorna True apenas no ciclo em que foi clicado

No próximo re-run, volta a False

Isso é desejável.

Botões representam ações pontuais, como:

- iniciar treinamento
- rodar inferência
- salvar resultado

### Regra prática:

- Configuração → slider, selectbox, input
- Ação → button

---

## 7. Callbacks: reagindo imediatamente a mudanças

Em alguns cenários, queremos reagir no momento da mudança, antes mesmo de renderizar o resto da tela.

Para isso, usamos callbacks com on_change ou on_click.

### Por que callbacks são úteis em sistemas de IA?

- Validação de combinações inválidas
- Reset de resultados ao trocar modelo
- Registro de logs para auditoria
- Limpeza de estado inconsistente

Exemplo:

```python
def reset_predicao():
    st.session_state.predicao_pronta = False
    st.toast("Configuração alterada. Execute novamente.")

st.slider(
    "Learning Rate",
    0.01, 0.1,
    key="lr",
    on_change=reset_predicao
)
```

Importante:

- Callbacks devem ser leves
- Não devem executar treinos ou chamadas pesadas

Para tarefas custosas, o botão continua sendo a abordagem correta.

---

## 8. Interatividade Real: mantendo histórico sem perder contexto

O grande objetivo desta aula é chegar a um sistema onde:

- o usuário altera hiperparâmetros
- executa múltiplas vezes
- a UI reage
- o histórico é preservado

Isso só é possível com st.session_state.

Exemplo conceitual:

```python
if "historico_loss" not in st.session_state:
    st.session_state.historico_loss = []
```

Cada nova execução adiciona dados ao histórico, sem apagar os anteriores, permitindo:

- comparação visual
- análise de evolução
- aprendizado incremental

Esse padrão é a base de simuladores, trainers e dashboards de IA profissionais.

---

## 9. Modelo mental final (takeaway da aula)

- Streamlit sempre reexecuta o script
- Variáveis normais não persistem
- st.session_state é a memória da aplicação
- Widgets definem estado
- Botões disparam ações
- Callbacks reagem a mudanças
- A UI é reflexo direto do estado

Aplicação dos conceitos de estado e callback sobre o exemplo da Aula 02

No Visual Code
```python
import streamlit as st
import random
import time
import numpy as np

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(page_title="AI UX Demo", layout="wide")

# ==========================================================
#region INICIALIZAÇÃO DE ESTADO
# ==========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

if "analysis_ran" not in st.session_state:
    st.session_state.analysis_ran = False

if "config_version" not in st.session_state:
    st.session_state.config_version = 0
#endregion
# ==========================================================

# ==========================================================
# CALLBACK — RESET AO ALTERAR CONFIGURAÇÃO
# ==========================================================
def reset_analysis():
    st.session_state.analysis_ran = False
    st.session_state.last_result = None
    st.session_state.config_version += 1
    st.toast("Configuração alterada. Execute novamente.")


# ==========================================================
# SIMULAÇÃO DO MODELO
# ==========================================================
def simulate_model(model_type, threshold):
    base_score = random.uniform(0.4, 0.95)

    if model_type == "Avançado":
        base_score += 0.05

    score = min(base_score, 0.99)
    label = "Cachorro" if score >= threshold else "Gato"

    explanation = {
        "Formato das orelhas": np.round(random.uniform(0.1, 0.4), 2),
        "Textura do pelo": np.round(random.uniform(0.1, 0.4), 2),
        "Formato do focinho": np.round(random.uniform(0.1, 0.4), 2),
    }

    return label, score, explanation


# ==========================================================
# SIDEBAR — CONTROLE DO SISTEMA (Widgets como estado)
# ==========================================================
st.sidebar.header("Configurações do Modelo")

# --------------------------------------------------
# region CONTROLES  — Widgets que alteram o estado e resetam a análise
# --------------------------------------------------

st.sidebar.selectbox(
    "Modelo",
    ["Base", "Avançado"],
    key="model_type",
    on_change=reset_analysis
)

st.sidebar.slider(
    "Threshold de decisão",
    0.0, 1.0, 0.75,
    key="threshold",
    on_change=reset_analysis
)

st.sidebar.checkbox(
    "Simular latência",
    value=True,
    key="simulate_latency"
)

st.sidebar.select_slider(
    "Nível de Verbosidade",
    options=["Baixa", "Média", "Alta", "Extrema"],
    key="verbosity_demo",
    on_change=reset_analysis
)

st.sidebar.number_input(
    "Número de Épocas",
    min_value=1,
    max_value=1000,
    value=10,
    step=1,
    key="epochs_demo",
    on_change=reset_analysis
)
 
st.sidebar.multiselect(
    "Selecionar Features do Modelo",
    ["Orelhas", "Pelo", "Focinho", "Cauda", "Porte"],
    default=["Orelhas", "Pelo"],
    key="features_demo",
    on_change=reset_analysis
)
 
st.sidebar.text_input(
    "Prompt do Sistema",
    placeholder="Descreva como o modelo deve classificar...",
    key="prompt_demo",
    on_change=reset_analysis
)

st.sidebar.text_area(
    "Observações adicionais",
    placeholder="Instruções complementares...",
    key="notes_demo",
    on_change=reset_analysis
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "Este app simula comportamento probabilístico, "
    "explicabilidade e human-in-the-loop."
)
#endregion
# ==========================================================


# ==========================================================
# 1 - EMPTY STATE
# ==========================================================
st.title("Classificador de Imagem (Simulado)")

uploaded = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg"])

if not uploaded:
    st.info("Envie uma imagem para iniciar a análise.")
    st.stop()

# ==========================================================
# BOTÃO COMO GATILHO (AÇÃO, NÃO ESTADO)
# ==========================================================
if st.button("Executar Análise"):
    st.session_state.analysis_ran = True

# ==========================================================
# EXECUÇÃO CONTROLADA PELO ESTADO
# ==========================================================
if st.session_state.analysis_ran:

    # -------------------------------
    # 2 - LOADING STATE / LATÊNCIA
    # -------------------------------
    if st.session_state.simulate_latency:
        with st.spinner("Extraindo características..."):
            time.sleep(1)

        with st.spinner("Classificando padrões..."):
            time.sleep(1)

        with st.spinner("Obtendo resultados..."):
            progress_bar = st.progress(0)
            total_steps = 100
            for i in range(total_steps):
                time.sleep(0.02)
                progress_bar.progress(i + 1)

        st.toast("Resultados consolidados.")
 
    label, score, explanation = simulate_model(
        st.session_state.model_type,
        st.session_state.threshold
    )

    confidence_percent = int(score * 100)

    st.session_state.last_result = {
        "label": label,
        "score": score,
        "explanation": explanation
    }

    st.session_state.history.append({
        "label": label,
        "score": score
    })

    # ==========================================================
    # TABS DE RESULTADOS
    # ==========================================================
    tab_predicao, tab_monitoramento = st.tabs(
        ["Predição & Validação Humana", "Monitoramento & Histórico"]
    )

    # ==========================================================
    # TAB 1 — PREDIÇÃO
    # ==========================================================
    with tab_predicao:

        # -------------------------------
        # 3 - CONFIDENCE UI
        # -------------------------------
        st.subheader("Resultado da Classificação")

        row1_col1, row1_col2 = st.columns([1, 2])

        with row1_col1:
            st.metric("Classe Prevista", label)
            st.metric("Confiança", f"{confidence_percent}%")
            st.progress(confidence_percent)

        with row1_col2:
            if score >= 0.85:
                st.success("Alta confiança na previsão.")
            elif score >= 0.60:
                st.warning("Confiança moderada. Revisão recomendada.")
            else:
                st.error("Baixa confiança. Revisão humana necessária.")

        st.markdown("---")

        # -------------------------------
        # 4 - EXPLICABILIDADE
        # -------------------------------
        st.subheader("Explicabilidade Local")

        exp_col1, exp_col2 = st.columns(2)

        features = list(explanation.items())

        with exp_col1:
            for feature, weight in features[:2]:
                st.write(feature)
                st.progress(int(weight * 100))

        with exp_col2:
            for feature, weight in features[2:]:
                st.write(feature)
                st.progress(int(weight * 100))

        st.markdown("---")

        # -------------------------------
        # 5 - HUMAN IN THE LOOP
        # -------------------------------
        st.subheader("Validação Humana")

        feedback_col1, feedback_col2 = st.columns(2)

        with feedback_col1:
            if st.button("IA acertou"):
                st.session_state.feedback_log.append({
                    "result": label,
                    "score": score,
                    "correct": True
                })
                st.success("Feedback registrado.")

        with feedback_col2:
            if st.button("IA errou"):
                st.session_state.feedback_log.append({
                    "result": label,
                    "score": score,
                    "correct": False
                })
                st.error("Feedback registrado.")

    # ==========================================================
    # TAB 2 — MONITORAMENTO & HISTÓRICO
    # ==========================================================
    with tab_monitoramento:

        st.subheader("Monitoramento do Sistema")

        total = len(st.session_state.feedback_log)

        if total > 0:
            correct = sum(1 for f in st.session_state.feedback_log if f["correct"])
            accuracy = correct / total

            monitor_col1, monitor_col2 = st.columns(2)

            with monitor_col1:
                st.metric("Feedbacks recebidos", total)

            with monitor_col2:
                st.metric("Acurácia percebida", f"{int(accuracy*100)}%")

            if accuracy < 0.7:
                st.warning("Possível degradação do modelo detectada.")
        else:
            st.info("Ainda não há feedback suficiente para monitoramento.")

        st.markdown("---")

        # -------------------------------
        # HISTÓRICO
        # -------------------------------
        st.subheader("Histórico de Decisões")

        history_cols = st.columns(2)
        recent = st.session_state.history[-6:]

        for i, item in enumerate(recent):
            with history_cols[i % 2]:
                st.write(f"{item['label']} — {int(item['score']*100)}%")

else:
    st.info("Configure os parâmetros e clique em **Executar Análise**.")
```

No Collab
```python
!pip install -q streamlit
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
```

```python
%%writefile app.py
import streamlit as st
import random
import time
import numpy as np

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(page_title="AI UX Demo", layout="wide")

# ==========================================================
#region INICIALIZAÇÃO DE ESTADO
# ==========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

if "analysis_ran" not in st.session_state:
    st.session_state.analysis_ran = False

if "config_version" not in st.session_state:
    st.session_state.config_version = 0
#endregion
# ==========================================================

# ==========================================================
# CALLBACK — RESET AO ALTERAR CONFIGURAÇÃO
# ==========================================================
def reset_analysis():
    st.session_state.analysis_ran = False
    st.session_state.last_result = None
    st.session_state.config_version += 1
    st.toast("Configuração alterada. Execute novamente.")


# ==========================================================
# SIMULAÇÃO DO MODELO
# ==========================================================
def simulate_model(model_type, threshold):
    base_score = random.uniform(0.4, 0.95)

    if model_type == "Avançado":
        base_score += 0.05

    score = min(base_score, 0.99)
    label = "Cachorro" if score >= threshold else "Gato"

    explanation = {
        "Formato das orelhas": np.round(random.uniform(0.1, 0.4), 2),
        "Textura do pelo": np.round(random.uniform(0.1, 0.4), 2),
        "Formato do focinho": np.round(random.uniform(0.1, 0.4), 2),
    }

    return label, score, explanation


# ==========================================================
# SIDEBAR — CONTROLE DO SISTEMA (Widgets como estado)
# ==========================================================
st.sidebar.header("Configurações do Modelo")

# --------------------------------------------------
# region CONTROLES  — Widgets que alteram o estado e resetam a análise
# --------------------------------------------------

st.sidebar.selectbox(
    "Modelo",
    ["Base", "Avançado"],
    key="model_type",
    on_change=reset_analysis
)

st.sidebar.slider(
    "Threshold de decisão",
    0.0, 1.0, 0.75,
    key="threshold",
    on_change=reset_analysis
)

st.sidebar.checkbox(
    "Simular latência",
    value=True,
    key="simulate_latency"
)

st.sidebar.select_slider(
    "Nível de Verbosidade",
    options=["Baixa", "Média", "Alta", "Extrema"],
    key="verbosity_demo",
    on_change=reset_analysis
)

st.sidebar.number_input(
    "Número de Épocas",
    min_value=1,
    max_value=1000,
    value=10,
    step=1,
    key="epochs_demo",
    on_change=reset_analysis
)
 
st.sidebar.multiselect(
    "Selecionar Features do Modelo",
    ["Orelhas", "Pelo", "Focinho", "Cauda", "Porte"],
    default=["Orelhas", "Pelo"],
    key="features_demo",
    on_change=reset_analysis
)
 
st.sidebar.text_input(
    "Prompt do Sistema",
    placeholder="Descreva como o modelo deve classificar...",
    key="prompt_demo",
    on_change=reset_analysis
)

st.sidebar.text_area(
    "Observações adicionais",
    placeholder="Instruções complementares...",
    key="notes_demo",
    on_change=reset_analysis
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Sobre")
st.sidebar.info(
    "Este app simula comportamento probabilístico, "
    "explicabilidade e human-in-the-loop."
)
#endregion
# ==========================================================


# ==========================================================
# 1 - EMPTY STATE
# ==========================================================
st.title("Classificador de Imagem (Simulado)")

uploaded = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg"])

if not uploaded:
    st.info("Envie uma imagem para iniciar a análise.")
    st.stop()

# ==========================================================
# BOTÃO COMO GATILHO (AÇÃO, NÃO ESTADO)
# ==========================================================
if st.button("Executar Análise"):
    st.session_state.analysis_ran = True

# ==========================================================
# EXECUÇÃO CONTROLADA PELO ESTADO
# ==========================================================
if st.session_state.analysis_ran:

    # -------------------------------
    # 2 - LOADING STATE / LATÊNCIA
    # -------------------------------
    if st.session_state.simulate_latency:
        with st.spinner("Extraindo características..."):
            time.sleep(1)

        with st.spinner("Classificando padrões..."):
            time.sleep(1)

        with st.spinner("Obtendo resultados..."):
            progress_bar = st.progress(0)
            total_steps = 100
            for i in range(total_steps):
                time.sleep(0.02)
                progress_bar.progress(i + 1)

        st.toast("Resultados consolidados.")
 
    label, score, explanation = simulate_model(
        st.session_state.model_type,
        st.session_state.threshold
    )

    confidence_percent = int(score * 100)

    st.session_state.last_result = {
        "label": label,
        "score": score,
        "explanation": explanation
    }

    st.session_state.history.append({
        "label": label,
        "score": score
    })

    # ==========================================================
    # TABS DE RESULTADOS
    # ==========================================================
    tab_predicao, tab_monitoramento = st.tabs(
        ["Predição & Validação Humana", "Monitoramento & Histórico"]
    )

    # ==========================================================
    # TAB 1 — PREDIÇÃO
    # ==========================================================
    with tab_predicao:

        # -------------------------------
        # 3 - CONFIDENCE UI
        # -------------------------------
        st.subheader("Resultado da Classificação")

        row1_col1, row1_col2 = st.columns([1, 2])

        with row1_col1:
            st.metric("Classe Prevista", label)
            st.metric("Confiança", f"{confidence_percent}%")
            st.progress(confidence_percent)

        with row1_col2:
            if score >= 0.85:
                st.success("Alta confiança na previsão.")
            elif score >= 0.60:
                st.warning("Confiança moderada. Revisão recomendada.")
            else:
                st.error("Baixa confiança. Revisão humana necessária.")

        st.markdown("---")

        # -------------------------------
        # 4 - EXPLICABILIDADE
        # -------------------------------
        st.subheader("Explicabilidade Local")

        exp_col1, exp_col2 = st.columns(2)

        features = list(explanation.items())

        with exp_col1:
            for feature, weight in features[:2]:
                st.write(feature)
                st.progress(int(weight * 100))

        with exp_col2:
            for feature, weight in features[2:]:
                st.write(feature)
                st.progress(int(weight * 100))

        st.markdown("---")

        # -------------------------------
        # 5 - HUMAN IN THE LOOP
        # -------------------------------
        st.subheader("Validação Humana")

        feedback_col1, feedback_col2 = st.columns(2)

        with feedback_col1:
            if st.button("IA acertou"):
                st.session_state.feedback_log.append({
                    "result": label,
                    "score": score,
                    "correct": True
                })
                st.success("Feedback registrado.")

        with feedback_col2:
            if st.button("IA errou"):
                st.session_state.feedback_log.append({
                    "result": label,
                    "score": score,
                    "correct": False
                })
                st.error("Feedback registrado.")

    # ==========================================================
    # TAB 2 — MONITORAMENTO & HISTÓRICO
    # ==========================================================
    with tab_monitoramento:

        st.subheader("Monitoramento do Sistema")

        total = len(st.session_state.feedback_log)

        if total > 0:
            correct = sum(1 for f in st.session_state.feedback_log if f["correct"])
            accuracy = correct / total

            monitor_col1, monitor_col2 = st.columns(2)

            with monitor_col1:
                st.metric("Feedbacks recebidos", total)

            with monitor_col2:
                st.metric("Acurácia percebida", f"{int(accuracy*100)}%")

            if accuracy < 0.7:
                st.warning("Possível degradação do modelo detectada.")
        else:
            st.info("Ainda não há feedback suficiente para monitoramento.")

        st.markdown("---")

        # -------------------------------
        # HISTÓRICO
        # -------------------------------
        st.subheader("Histórico de Decisões")

        history_cols = st.columns(2)
        recent = st.session_state.history[-6:]

        for i, item in enumerate(recent):
            with history_cols[i % 2]:
                st.write(f"{item['label']} — {int(item['score']*100)}%")

else:
    st.info("Configure os parâmetros e clique em **Executar Análise**.")
```

```python
import subprocess
import threading
import time

def run_streamlit():
    subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501"])

def run_tunnel():
    p = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    for line in p.stdout:
        if "trycloudflare.com" in line:
            print("\n--- SEU APP ESTÁ RODANDO AQUI ---")
            print(line.strip())
            print("---------------------------------\n")
            break

threading.Thread(target=run_streamlit).start()
time.sleep(5)
run_tunnel()
```
