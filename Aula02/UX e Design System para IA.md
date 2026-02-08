# Aula 2 — UX e Design System para IA

**Frase-guia:** “AI UX Design: Princípios de interface e usabilidade para sistemas inteligentes.”

---

## Objetivo da aula

Esta apostila detalha os conceitos, padrões e práticas para projetar interfaces que tornem sistemas de IA confiáveis, explicáveis e utilizáveis. O objetivo é levar o aluno além da funcionalidade pura ("funciona") para a maturidade de uso ("é utilizável, explicável e profissional"). São apresentados exemplos, trechos de código em Streamlit para aplicação prática e indicações explícitas de onde inserir imagens ilustrativas.

---

## Estrutura geral (2h)

* **Bloco 1 — Teoria de UX para IA:** 45 min
* **Bloco 2 — Design System aplicado ao Streamlit:** 30 min
* **Bloco 3 — Prática guiada (refatoração do app):** 45 min

---

# 1. Teoria — Fundamentos de UX para Sistemas de IA (45 min)

## 1.1 UX Tradicional vs UX para IA (10 min)

**Contexto:** Em produtos digitais tradicionais, interfaces refletem resultados determinísticos: o usuário envia um comando e recebe um resultado previsível. Em sistemas de IA, as respostas são probabilísticas, sujeitas a incertezas, vieses e eventual latência de processamento.

**Implicações de design:**

* É necessário comunicar que o resultado é uma **estimativa** — não uma verdade absoluta.
* A interface precisa expor **confiança**, **incerteza** e **processo**.
* Deve-se prever e mostrar **possibilidade de erro** e oferecer meios simples de correção.

**Exemplo ilustrativo (texto):**

> Um classificador de imagens que retorna "Cachorro — 72% de confiança" deixa o usuário consciente que há chance de erro e reduz decisões erradas (por exemplo: usar o resultado em triagens automáticas sem revisão humana).

**Imagem sugerida:**

![Comparação entre sistemas determinísticos e probabilísticos](images/ux_tradicional_vs_ia.png)

---

## 1.2 Pilar 1 — Transparência e Explainability (10 min)

**Problema:** Interfaces do tipo caixa-preta, que entregam apenas um rótulo final sem contexto, geram desconfiança e impedem correções.

**Pergunta central do usuário:**

> "Por que a IA chegou a esse resultado?"

**Princípios práticos:**

* Mostrar **o que** a IA está fazendo.
* Mostrar **quão confiante** ela está no resultado.
* Evitar respostas "mágicas" e preferir linguagem humana.

**Exemplos de UI:**

* Status passo a passo ("Analisando pixels…", "Classificando padrões…").
* Métricas de confiança.
* Labels claros como "Resultado estimado" e "Probabilidade".

**Imagem sugerida:**

![Card de resultado com explicação e barra de confiança](images/transparencia_explainability.png)

**Exemplo de código (Streamlit):**

```python
# Exibir rótulo + confiança
st.subheader("Resultado")
st.write("Rótulo estimado: **Cachorro**")
confidence = 0.72
st.metric("Confiança", f"{confidence*100:.0f}%")
st.progress(int(confidence * 100))
```

---

## 1.3 Pilar 2 — Gestão de Expectativa e Incerteza (15 min)

**Erro comum:** Apresentar resultados como binários (certo/errado).

**Boas práticas:**

* Diferenciar faixas de confiança:

  * **Alta confiança:** ≥ 85%
  * **Média confiança:** 60–85%
  * **Baixa confiança:** < 60%
* Comunicar risco visual e textualmente.
* Nunca prometer mais do que o modelo pode entregar (*never overpromise*).

A interface deve proteger o usuário quando o modelo está incerto, incentivando revisão humana.

**Imagem sugerida:**

![Estados de confiança: alta, média e baixa](images/gestao_incerteza.png)

---

## 1.4 Pilar 3 — Design para Latência e Feedback (10 min)

**Regra de ouro:** Usuários toleram espera se entenderem o que está acontecendo.

**Técnicas comuns:**

* Skeleton loading
* Spinners contextuais
* Barras de progresso
* Mensagens intermediárias

**Ligação direta com Streamlit:**

* `st.spinner`
* `st.progress`
* `st.status`

**Exemplo de código:**

```python
with st.spinner("Analisando a imagem e extraindo características..."):
    result = run_model(image)

st.success("Análise concluída")
```

**Imagem sugerida:**

![Exemplo de loading e feedback visual](images/latencia_feedback.png)

---

## 1.5 Human-in-the-loop (5 min)

UX também é um mecanismo de coleta de dados.

**Por quê:**

* Permite correção de erros.
* Gera dados para re-treinamento.
* Aumenta confiança do usuário.

**Exemplos:**

* 👍 / 👎
* Pergunta direta: "A IA acertou?"
* Logs de erro baseados em UI

**Imagem sugerida:**

![Exemplo de feedback humano na interface](images/human_in_the_loop.png)

---

# 2. Anatomia de um Design System no Streamlit (30 min)

## 2.1 O que é (e o que não é) um Design System (5 min)

**Não é:**

* Apenas CSS
* Apenas cores bonitas

**É:**

* Consistência
* Previsibilidade
* Reuso de padrões

**Imagem sugerida:**

![Camadas de um design system](images/design_system_anatomia.png)

---

## 2.2 Hierarquia Visual e Navegação (10 min)

**Boas decisões em Streamlit:**

* `st.sidebar`: configurações globais
* Área central: resultado e decisão
* Tabs: contextos diferentes, não etapas do fluxo

**Regra prática:**

* Se muda o modelo → sidebar
* Se muda o resultado → área principal

**Imagem sugerida:**

![Wireframe do layout Streamlit](images/hierarquia_visual.png)

---

## 2.3 Cores Semânticas (5 min)

Usar cor como significado, não como decoração:

* `st.success` → alta confiança
* `st.warning` → incerteza
* `st.error` → falha ou risco
* `st.info` → explicação

**Imagem sugerida:**

![Paleta semântica de cores](images/cores_semanticas.png)

---

## 2.4 Componentes de Feedback do Sistema (10 min)

**Quando usar:**

* `st.spinner` → espera curta
* `st.status` → múltiplas etapas
* `st.progress` → progresso mensurável
* `st.toast` → feedback rápido e não crítico

**Regra:** Feedback crítico nunca deve ser apenas um toast.

**Exemplo de código:**

```python
st.sidebar.header("Configurações")
model = st.sidebar.selectbox("Modelo", ["Base", "Avançado"])
threshold = st.sidebar.slider("Threshold", 0.0, 1.0, 0.75)
```

**Imagem sugerida:**

![Feedback visual no Streamlit](images/componentes_feedback.png)

---

# 3. Prática — Do Funcional ao Profissional (45 min)

## 3.1 Ponto de Partida (5 min)

App funcional, porém:

* Resultado estático
* Nenhum estado intermediário
* Nenhuma explicação

---

## 3.2 O que vamos implementar (10 min)

**Checklist de UX:**

* Empty State
* Loading State
* Confidence UI
* Sidebar como painel de controle
* Feedback humano

**Imagem sugerida:**

![Fluxo completo do app](images/fluxo_completo.png)

---

## 3.3 Refatoração Guiada do Código (30 min)

**Separação conceitual:**

1. Configuração
2. Entrada
3. Processamento
4. Saída
5. Feedback

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

## 3.4 Ponto de Chegada — O que o aluno aprende

Ao final da aula, o aluno consegue:

* Projetar UX pensando em incerteza
* Criar interfaces explicáveis
* Usar Streamlit de forma profissional

**Gancho para a próxima aula:**

> "Na próxima etapa vamos resolver reprocessamento com caching, arquitetura e performance."

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

## Observações finais

Este arquivo está pronto para uso direto em repositórios GitHub (`.md`), com imagens organizadas na pasta `images/` e blocos de código compatíveis com renderização Markdown padrão.
