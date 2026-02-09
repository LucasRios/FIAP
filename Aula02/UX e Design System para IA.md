# Aula 2 — UX e Design System para IA

AI UX Design: Princípios de interface e usabilidade para sistemas inteligentes

---

## Objetivo

Detalhar os conceitos, padrões e práticas para projetar interfaces que tornem sistemas de IA confiáveis, explicáveis e utilizáveis. O objetivo é além da funcionalidade pura ("funciona") para a maturidade de uso ("é utilizável, explicável e profissional").

---

# 1. Fundamentos de UX para Sistemas de IA

## UX Tradicional vs UX para IA

Em produtos digitais tradicionais, interfaces refletem resultados determinísticos: o usuário envia um comando e recebe um resultado previsível. Em sistemas de IA, as respostas são probabilísticas, sujeitas a incertezas, vieses e eventual latência de processamento.

**Implicações de design:**

* É necessário comunicar que o resultado é uma **estimativa** — não uma verdade absoluta.
* A interface precisa expor **confiança**, **incerteza** e **processo**.
* Deve-se prever e mostrar **possibilidade de erro** e oferecer meios simples de correção.

**Exemplo Determinístico:**

> Um Ecommerce onde o usuário escolhe um produto, é redirecionado ao carrinho, efetua o pagamento, receba uma resposta de que o pedido foi processado.

**Exemplo Probabilístico:**

> Um classificador de imagens que retorna "Cachorro — 72% de confiança" deixa o usuário consciente que há chance de erro e reduz decisões erradas

![Comparação entre sistemas determinísticos e probabilísticos](imagens/comparacao_deterministico_probabilistico.png)

---

# 2. Pilares de UX para Sistemas de IA 

## 2.1 Pilar 1 — Transparência e Explainability

Os problemas em Interfaces de sistemas de IA giram em torno de interfaces do tipo caixa-preta, que entregam apenas um rótulo final sem contexto, geram desconfiança e impedem correções.
Quando pensamos em interface de sistemas de IA devemos primeiro perguntar:

> "Por que a IA chegou a esse resultado?"

A partir disso conseguimos pensar melhores práticas, princípios e elementos que possam responder à essa pergunta de forma satisfatória

**Princípios práticos:**

* Mostrar **o que** a IA está fazendo.
* Mostrar **quão confiante** ela está no resultado.
* Evitar respostas "mágicas" e preferir linguagem humana.

**Exemplos de UI:**

* Status passo a passo ("Analisando pixels…", "Classificando padrões…").
* Métricas de confiança.
* Labels claros como "Resultado estimado" e "Probabilidade".

![Card de resultado com explicação e barra de confiança](imagens/transparencia_explainability.png)

**Exemplo no StreamLit:**

```python
# Exibir rótulo + confiança
st.subheader("Resultado")
st.write("Rótulo estimado: **Cachorro**")
confidence = 0.72
st.metric("Confiança", f"{confidence*100:.0f}%")
st.progress(int(confidence * 100))
```

---

## 2.2 Pilar 2 — Gestão de Expectativa e Incerteza

**Erro comum:** Apresentar resultados como binários (certo/errado).
Como mencionado no começo, a interface em sistemas de IA trabalham com resultados probabilísticos e não determinísticos, portanto devemos evitar qualquer resposta simplemente falando se está certo ou errado, devemos apresentar nossa probabilidade de resposta. Essa resposta pode vir acompanhada de elementos visuais que permitam destacar o "número bom" ou o "número ruim", mas não cravar se o resultado está certo ou errado.

**Boas práticas:**

* Diferenciar faixas de confiança:

  * **Alta confiança:** ≥ 85%
  * **Média confiança:** 60–85%
  * **Baixa confiança:** < 60%
    
* Comunicar risco visual e textualmente, utilizando gráficos de gauge, termômetro, e etc, além de textos objetivos explicando o que o número quer dizer.
  
* Nunca prometer mais do que o modelo pode entregar (*never overpromise*).

A interface deve proteger o usuário quando o modelo está incerto, incentivando revisão humana. (Human-in-the-loop)

![Estados de confiança: alta, média e baixa](imagens/gestao_de_expectativa_e_incerteza.png)

---

## 2.3 Pilar 3 — Design para Latência e Feedback

**Regra de ouro:** Usuários toleram a espera se entenderem o que está acontecendo.

**Técnicas comuns:**

* Skeleton loading | Spinners contextuais  `st.spinner`  
* Barras de progresso `st.progress`
* Mensagens intermediárias `st.status`
 
```python
with st.spinner("Analisando a imagem e extraindo características..."):
    result = run_model(image)

st.success("Análise concluída")
```

![Exemplo de loading e feedback visual](imagens/design_latencia.png)

---

## 3. Human-in-the-loop 

UX também é um mecanismo de coleta de dados com os usuários.

**Por quê:**

* Permite correção de erros.
* Gera dados para re-treinamento.
* Aumenta confiança do usuário.

**Exemplos:**

* 👍 / 👎
* Pergunta direta: "A IA acertou?"
* Logs de erro baseados em UI. Lista simples ou detalhada sobre os erros gerados pela IA a partir de determinadas entradas do usuário.

![Exemplo de feedback humano na interface](imagens/huma_in_the_loop.png)

---

# 4. Anatomia de um Design System no Streamlit

## 4.1 O que é (e o que não é) um Design System

**Não é:**

* Apenas CSS, Javascript com animações e etc.

Lembre-se: Deixe o trabalho visual com o Designer. O importante no FrontEnd em interfaces de sistema de IA é usarmos ferramentas que encapsulam o HTML/CSS/Javascript tradicional, permitindo consigamos extrair a melhor experiência para nossos usuários e nós mesmos, utilizando o próprio phyton

**É:**

* Consistência
* Previsibilidade
* Reuso de padrões

![Camadas de um design system](imagens/camadas_desing_system.png)

---

## 4.2 Hierarquia Visual e Navegação 

**Boas decisões em Streamlit:**

* `st.sidebar`: Para definirmos configurações globais
* Área central do nosso "bloquinho": usamos para mostrar resultados e decisões
* Tabs: usamos para diferenciar contextos (como input, métricas, configurações), não etapas do fluxo. Essas etapas podemos pensar como input/output. Eles podem permanecer na mesma Tab, sendo trabalhos em linhas e colunas diferentes na mesma Tab.

**Regra prática:**

* Se muda o modelo → sidebar
* Se muda o resultado → área principal
 
![Wireframe do layout Streamlit](imagens/hierarquia_visual_navegacao.png)

---

## 4.3 Cores Semânticas

Usar cor como significado, não como decoração:

* `st.success` → alta confiança
* `st.warning` → incerteza
* `st.error` → falha ou risco
* `st.info` → explicação
 
![Paleta semântica de cores](images/cores_semanticas.png)

---

## 4.4 Componentes de Feedback do Sistema

**Quando usar:**

* `st.spinner` → espera curta
* `st.status` → múltiplas etapas
* `st.progress` → progresso mensurável
* `st.toast` → feedback rápido e não crítico

**Regra:** Feedback crítico nunca deve ser apenas um toast. Neste caso devemos usar as cores Semânticas

**Exemplo de código:**

```python
st.sidebar.header("Configurações")
model = st.sidebar.selectbox("Modelo", ["Base", "Avançado"])
threshold = st.sidebar.slider("Threshold", 0.0, 1.0, 0.75)
```

![Feedback visual no Streamlit](images/componentes_feedback.png)

---

# 5. Prática — Do Funcional ao Profissional  

## 5.1 Ponto de Partida  

App funcional, porém:

* Resultado estático
* Nenhum estado intermediário
* Nenhuma explicação

---

## 5.2 O que vamos implementar 

**Checklist de UX:**
Tudo o que vimos na parte teórica. Sempre que for fazer uma interface, copie esse checklist, cole na sua IDE e pense se cada tópico faz sentido para o que você está programando, assim você conseguirá passar por todos os tópicos importantes no desenvolvimento de interfaces para sistemas de IA.

* Empty State (O que o usuário vê ao abrir a interface antes de qualquer ação: orienta, reduz dúvida e mostra como começar)
* Loading State (Como a interface comunica que a IA está processando e o que está acontecendo durante a espera)
* Confidence UI (Como o grau de confiança, incerteza ou risco do resultado é apresentado de forma clara e acionável)
* Explainability / Transparência (Como a interface explica por que a IA chegou àquele resultado (processo, critérios ou sinais))
* Design para Latência (Como a interface lida com esperas longas, múltiplas etapas e percepção de tempo do usuário)
* Sidebar como painel de controle (Onde ficam configurações que alteram o comportamento do sistema)
* Feedback humano (Como o usuário pode confirmar, corrigir ou discordar da decisão da IA)

![Fluxo completo do app](images/fluxo_completo.png)

---

## 5.3 Refatoração Guiada

**Exemplo de estrutura:**

```python
# Configuração
# Entrada
# Processamento
# Saída
# Feedback
```

**Uso conceitual de `st.session_state`:** manter estado entre re-runs.

**Exemplo de Confidence UI:**

```python
st.metric("Confiança", f"{score*100:.0f}%")
st.progress(int(score * 100))
```

---

## 5.4 Ponto de Chegada

* Projetar UX pensando em incerteza
* Criar interfaces explicáveis
* Usar Streamlit de forma profissional

---

# Apêndice — Trechos adicionais de código

## Empty State

```python
if not input:
    st.info("Envie uma imagem para iniciar")
```

## Feedback do usuário

```python
if st.button("👍"):
    log_feedback(True)
```

## Session State

```python
if 'last_result' not in st.session_state:
    st.session_state['last_result'] = None
```

---




