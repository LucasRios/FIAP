# Aula 3 — Interatividade Real
## Input de Dados, Estado e Callbacks no Streamlit

Nesta aula, avançamos do dashboard estático para a aplicação interativa de verdade. O objetivo não é apenas adicionar sliders e botões, mas compreender como o Streamlit executa, reexecuta e preserva (ou não) informações ao longo do uso.

Em sistemas de IA, interatividade não é detalhe estético:
é o mecanismo que permite ajustar hiperparâmetros, testar hipóteses, comparar resultados e criar ciclos de aprendizado humano + máquina.

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

Em aplicações de IA, isso é inaceitável.
Precisamos manter:

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

Para dominar interatividade, o aluno precisa internalizar este modelo mental:

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

Ao final desta aula, o aluno deve sair com o seguinte entendimento:

- Streamlit sempre reexecuta o script
- Variáveis normais não persistem
- st.session_state é a memória da aplicação
- Widgets definem estado
- Botões disparam ações
- Callbacks reagem a mudanças
- A UI é reflexo direto do estado
