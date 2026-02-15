# Aula 2 — UX e Design System para IA

AI UX Design: Princípios de interface para sistemas inteligentes e probabilísticos

---

## Objetivo

Esta aula aprofunda como projetar interfaces para sistemas de IA que não apenas funcionam, mas comunicam corretamente incerteza, permitem supervisão humana e operam de forma confiável em produção. O foco deixa de ser “o modelo acertou?” e passa a ser “o usuário consegue entender, confiar e intervir no sistema?”.

A base conceitual parte principalmente de:
- Human Compatible — incerteza e cooperação humano-IA
- Interpretable Machine Learning — interpretabilidade e calibragem
- Designing Human-Centered AI — controle humano e confiabilidade
- Designing Machine Learning Systems — sistemas reais, latência e degradação

---

# 1. Fundamentos de UX para Sistemas de IA

## UX Tradicional vs UX para IA

Interfaces tradicionais operam sob previsibilidade: uma ação gera um resultado definido. Em um e-commerce, o pagamento aprovado confirma a compra. A relação entre ação e resposta é direta e estável.

Sistemas de IA não operam assim. Eles inferem. Eles estimam. Eles produzem respostas baseadas em padrões estatísticos aprendidos com dados históricos. Como argumenta Stuart Russell, um sistema inteligente adequado deve reconhecer que não possui certeza absoluta sobre o mundo. Logo, a interface também não pode agir como se tivesse.

Quando uma IA retorna “Cachorro — 72% de confiança”, o número não é decorativo. Ele representa incerteza epistemológica. A experiência do usuário precisa refletir isso.

**Implicações de design:**

* É necessário comunicar que o resultado é uma **estimativa** — não uma verdade absoluta.
* A interface precisa expor **confiança**, **incerteza** e **processo**.
* O erro é inevitável. A supervisão humana é estrutural, não opcional.
* Deve-se prever e mostrar **possibilidade de erro** e oferecer meios simples de correção.

**Exemplo Determinístico:**

> Um Ecommerce onde o usuário escolhe um produto, é redirecionado ao carrinho, efetua o pagamento, receba uma resposta de que o pedido foi processado.

**Exemplo Probabilístico:**

> Um classificador de imagens que retorna "Cachorro — 72% de confiança" deixa o usuário consciente que há chance de erro e reduz decisões erradas

![Comparação entre sistemas determinísticos e probabilísticos](imagens/comparacao_deterministico_probabilistico.png)

---

# 2. Pilares de UX para Sistemas de IA 

## 2.1 Pilar 1 — Transparência e Explainability (Molnar;Shneiderman)

Os problemas em Interfaces de sistemas de IA giram em torno de interfaces do tipo caixa-preta, que entregam apenas um rótulo final sem contexto, geram desconfiança e impedem correções.

Molnar diferencia explicações globais (como o modelo funciona no geral) de explicações locais (por que esta decisão específica foi tomada). Para UX, isso é decisivo.

Quando pensamos em interface de sistemas de IA devemos primeiro perguntar:

> "Por que a IA chegou a esse resultado?"

A partir disso conseguimos pensar melhores práticas, princípios e elementos que possam responder à essa pergunta de forma satisfatória

**Princípios práticos:**

* Mostrar **o que** a IA está fazendo.
* Mostrar **quão confiante** ela está no resultado.
* Evitar respostas "mágicas" e preferir linguagem humana.

Transparência, portanto, não é apenas mostrar um número de confiança. É expor processo. Mesmo que o usuário não compreenda os detalhes matemáticos, ele precisa perceber que existe um caminho lógico entre entrada e saída.

**Em termos práticos:**

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

## 2.2 Pilar 2 — Gestão de Expectativa e Incerteza (Russell; Molnar)

Sistemas avançados devem operar assumindo que suas crenças podem estar erradas. Essa lógica deve aparecer na interface.

**Erro comum:** Apresentar resultados como binários (certo/errado).
Como mencionado no começo, a interface em sistemas de IA trabalham com resultados probabilísticos e não determinísticos, portanto devemos evitar qualquer resposta simplemente falando se está certo ou errado, devemos apresentar nossa probabilidade de resposta. Essa resposta pode vir acompanhada de elementos visuais que permitam destacar o "número bom" ou o "número ruim", mas não cravar se o resultado está certo ou errado.

**Boas práticas:**

* Diferenciar faixas de confiança:

  * **Alta confiança:** ≥ 85%
  * **Média confiança:** 60–85%
  * **Baixa confiança:** < 60%
    
* Comunicar risco visual e textualmente, utilizando gráficos de gauge, termômetro, e etc, além de textos objetivos explicando o que o número quer dizer.
  
A responsabilidade não termina no número. A interface deve orientar comportamento.

Se a confiança for baixa:

- Sinalizar visualmente o risco.
- Recomendar revisão humana.
- Permitir correção manual.

* Nunca prometer mais do que o modelo pode entregar (*never overpromise*).
Isso é gestão de expectativa. Nunca prometer mais do que o modelo pode entregar. Um sistema que aparenta 100% de precisão gera uso imprudente.

A confiança do usuário não cresce quando o sistema parece perfeito. Ela cresce quando o sistema reconhece seus limites. (Molnar)
 
![Estados de confiança: alta, média e baixa](imagens/gestao_de_expectativa_e_incerteza.png)

---

## 2.3 Pilar 3 — Design para Latência e Feedback (Chip Huyen)

Problemas reais de produção: latência, distribuição de dados que muda ao longo do tempo, degradação de performance.

A interface precisa lidar com essas realidades.
Esse feedback reduz ansiedade e aumenta percepção de profissionalismo.
Sistemas de IA operam em pipeline. A interface deve refletir esse pipeline.

**Regra de ouro:** Usuários toleram a espera se entenderem o que está acontecendo. Eles rejeitam silêncio.

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

## 2.4. Pilar 4 — Human-in-the-loop (Shneiderman)

UX também é um mecanismo de coleta de dados com os usuários.
Sistemas confiáveis são aqueles que mantêm o humano no controle. Não como figura decorativa, mas como parte ativa do processo decisório.

É estruturar a experiência para permitir
* Confirmação de decisão
* Correção de erro
* Registro de discordância
* Ajuste de threshold

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

# 3. Anatomia de um Design System no Streamlit

## 3.1 O que é (e o que não é) um Design System

**Não é:**

* Apenas CSS, Javascript com animações e etc.

Lembre-se: Deixe o trabalho visual com o Designer. O importante no FrontEnd em interfaces de sistema de IA é usarmos ferramentas que encapsulam o HTML/CSS/Javascript tradicional, permitindo consigamos extrair a melhor experiência para nossos usuários e nós mesmos, utilizando o próprio phyton

**É:**

* Consistência
* Previsibilidade
* Reuso de padrões

![Camadas de um design system](imagens/camadas_desing_system.png)

---

## 3.2 Hierarquia Visual e Navegação 

**Boas decisões em Streamlit:**

* `st.sidebar`: Para definirmos configurações globais
* Área central do nosso "bloquinho": usamos para mostrar resultados e decisões
* Tabs: usamos para diferenciar contextos (como input, métricas, configurações), não etapas do fluxo. Essas etapas podemos pensar como input/output. Eles podem permanecer na mesma Tab, sendo trabalhos em linhas e colunas diferentes na mesma Tab.

**Regra prática:**

* Se muda o modelo → sidebar
* Se muda o resultado → área principal
 
![Wireframe do layout Streamlit](imagens/hierarquia_visual_navegacao.png)

---

## 3.3 Cores Semânticas

Usar cor como significado, não como decoração:

Quando a cor verde sempre significa alta confiança, o usuário aprende.
Quando amarelo sempre indica incerteza, o usuário internaliza.
Quando erro sempre aparece com o mesmo padrão visual, a previsibilidade reduz carga cognitiva.

* `st.success` → alta confiança
* `st.warning` → incerteza
* `st.error` → falha ou risco
* `st.info` → explicação
 
![Paleta semântica de cores](imagens/cores_semanticas.png)

---

## 3.4 Componentes de Feedback do Sistema

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

![Feedback visual no Streamlit](imagens/componentes_feedback.png)

---

# 4. Prática — Do Funcional ao Profissional  

**Checklist de UX:**
Tudo o que vimos na parte teórica. Sempre que for fazer uma interface, copie esse checklist, cole na sua IDE e pense se cada tópico faz sentido para o que você está programando, assim você conseguirá passar por todos os tópicos importantes no desenvolvimento de interfaces para sistemas de IA.

* Empty State (O que o usuário vê ao abrir a interface antes de qualquer ação: orienta, reduz dúvida e mostra como começar)
* Loading State (Como a interface comunica que a IA está processando e o que está acontecendo durante a espera)
* Confidence UI (Como o grau de confiança, incerteza ou risco do resultado é apresentado de forma clara e acionável)
* Explainability / Transparência (Como a interface explica por que a IA chegou àquele resultado (processo, critérios ou sinais))
* Design para Latência (Como a interface lida com esperas longas, múltiplas etapas e percepção de tempo do usuário)
* Sidebar como painel de controle (Onde ficam configurações que alteram o comportamento do sistema)
* Feedback humano (Como o usuário pode confirmar, corrigir ou discordar da decisão da IA)

---

## 4.3 Refatoração Guiada

**Exemplo de estrutura:**

```python
# Configuração
# Entrada
# Processamento
# Saída
# Confiança
# Feedback
```

**Uso conceitual de `st.session_state`:** manter estado entre re-runs.

**Exemplo de Confidence UI:**

```python
st.metric("Confiança", f"{score*100:.0f}%")
st.progress(int(score * 100))
```

---

## 4.4 Ponto de Chegada

* Projetar UX pensando em incerteza
* Criar interfaces explicáveis
* Usar Streamlit de forma mais profissional

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
# Referências
- Ben Shneiderman — Designing Human-Centered AI
- Christoph Molnar — Interpretable Machine Learning
- Stuart Russell — Human Compatible
- Chip Huyen — Designing Machine Learning Systems







