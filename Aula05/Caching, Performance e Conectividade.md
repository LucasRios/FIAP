# 1 Modelo de Execução do Streamlit

## Conceito fundamental

Streamlit executa o script **de cima para baixo a cada interação**.

Isso significa:

- Toda modificação em widget → dispara rerun.
- Variáveis são recriadas.
- Objetos são reinstanciados.
- Código pesado pode ser reexecutado.

Arquitetura mental:

Estado atual → Script roda inteiro → UI é reconstruída

---

# 2 Caching Profundo

Caching é o pilar de performance no Streamlit moderno.

## O que é cache, de fato?

Cache é o mecanismo de **armazenar o resultado de uma execução custosa** para reutilizá-lo posteriormente sem recalcular.

Em termos simples:

> Se a entrada não mudou, o resultado também não precisa mudar.

No contexto do Streamlit isso é ainda mais importante, porque, sem cache, qualquer ajuste em um slider poderia:

- Recarregar um CSV grande.
- Reexecutar uma query SQL.
- Reprocessar um modelo de IA.
- Fazer múltiplas chamadas a API.

Isso gera:
- Lentidão perceptível.
- Consumo desnecessário de CPU.
- Custos maiores (em APIs pagas).
- Experiência ruim para o usuário.

---

## O efeito do cache no ciclo de execução

Lembre do fluxo padrão do Streamlit:

Quando aplicamos cache, o fluxo muda sutilmente:

1. Usuário interage.
2. Script roda novamente.
3. Função cacheada é chamada.
4. Streamlit verifica:
   - A função mudou?
   - Os parâmetros mudaram?
5. Se nada mudou → retorna resultado armazenado.
6. Se algo mudou → recalcula e atualiza o cache.

Ou seja:

> O rerun continua acontecendo.  
> O que muda é que partes do código deixam de ser reexecutadas de fato.

O cache não impede o rerun.  
Ele reduz o custo do rerun.

---

## Como o Streamlit decide reutilizar o cache?

Internamente, o Streamlit:

- Gera um hash da função.
- Gera um hash dos argumentos passados.
- Combina essas informações.
- Usa isso como chave de armazenamento.

Se qualquer elemento for diferente:

- Código da função
- Valor dos parâmetros
- Dependências explícitas

O cache é invalidado automaticamente.

Isso torna o sistema:

✔ Determinístico  
✔ Seguro  
✔ Reprodutível  

---

## O impacto direto na performance

Sem cache:

- Tempo de resposta cresce linearmente com a complexidade.
- Pequenas interações podem levar segundos.
- Modelos grandes tornam o app quase inutilizável.

Com cache:

- Processamentos pesados acontecem uma única vez.
- Interações subsequentes tornam-se quase instantâneas.
- O app passa a parecer reativo.

Em aplicações de IA, isso é ainda mais crítico:

- Carregar um modelo pode levar segundos.
- Rodar embeddings pode ser caro.
- Consultar APIs pode ter latência externa.

---

## Regra mental para uso consciente

Sempre que escrever uma função, pergunte:

- Isso é custoso?
- O resultado depende apenas desses parâmetros?
- Ele precisa ser recalculado a cada interação?

---

## 2.1 `st.cache_data`

Usado para:

- DataFrames
- Resultados de transformação
- Chamadas de API
- Queries SQL

Exemplo:

```python
@st.cache_data
def carregar_dados():
    return pd.read_csv("dados.csv")
```

Como funciona internamente?
	•	Streamlit cria hash da função + parâmetros.
	•	Armazena resultado em memória.
	•	Se entrada não mudar → retorna do cache.
	•	Se mudar → recalcula.

Características:
	•	Imutável
	•	Seguro para múltiplos usuários
	•	Ideal para dados

⸻

## 2.2 st.cache_resource

Usado para:
	•	Modelos de IA
	•	Conexões de banco
	•	Clientes de API
	•	Objetos pesados

Exemplo:

```python
@st.cache_resource
def carregar_modelo():
    return ModeloGigante()
```

Diferença conceitual:

cache_data	cache_resource
Guarda resultado	Guarda instância
Serializa	Mantém objeto vivo
Ideal para dados	Ideal para recursos

⸻

## 2.3 TTL (Time to Live)

TTL significa **Time to Live** — tempo de vida do cache.

Ele define **por quanto tempo o resultado armazenado pode ser reutilizado antes de ser considerado inválido**.

Exemplo:

```python
@st.cache_data(ttl=3600)
def carregar_api():
    return requests.get(url).json()
```

Aqui estamos dizendo:
	•	O resultado dessa função pode ser reutilizado por 3600 segundos (1 hora).
	•	Após esse período, na próxima chamada, o Streamlit ignora o valor armazenado.
	•	A função é executada novamente.
	•	O novo resultado substitui o antigo no cache.

⸻

O que acontece na prática?

Sem TTL:
	•	Se os parâmetros não mudarem, o cache pode durar indefinidamente.
	•	Mesmo que os dados externos tenham sido atualizados.

Com TTL:
	1.	A função é chamada.
	2.	O resultado é salvo junto com um timestamp.
	3.	Durante o período definido, o valor é reutilizado.
	4.	Quando o tempo expira:
	•	O próximo acesso dispara novo cálculo.
	•	O cache é atualizado automaticamente.

Importante:
O TTL não executa a função automaticamente ao expirar.
Ele apenas força o recálculo na próxima vez que a função for chamada.

⸻

Por que isso é essencial?

Streamlit é muito usado para:
	•	Dashboards de monitoramento
	•	Métricas operacionais
	•	Dados financeiros
	•	Integração com APIs externas

Esses dados mudam com o tempo.

Se você usar cache sem TTL:
	•	O app pode mostrar informações desatualizadas.
	•	O usuário pode tomar decisões com base em dados antigos.

TTL equilibra:

✔ Performance
✔ Atualização automática
✔ Redução de chamadas externas

⸻

Como escolher o valor de TTL?

Depende do tipo de dado:

Tipo de dado	TTL sugerido
Dados quase estáticos	Horas ou dias
Dados operacionais	Minutos
Monitoramento em tempo real	Segundos
APIs caras	TTL maior para reduzir custo

⸻

Relação entre TTL e custo

Em APIs pagas (OpenAI, serviços financeiros, etc.):
	•	Cada chamada tem custo.
	•	Sem TTL → cada interação pode gerar nova chamada.
	•	Com TTL → múltiplos usuários reutilizam o mesmo resultado durante o período.

Isso reduz drasticamente:
	•	Latência
	•	Consumo de recursos
	•	Custo financeiro

⸻

Mentalidade correta sobre TTL

Pergunta estratégica:

Com que frequência esse dado realmente precisa ser atualizado?

Se a resposta for:
	•	“A cada clique” → talvez não devesse ser cacheado.
	•	“A cada alguns minutos” → TTL é ideal.
	•	“Raramente muda” → TTL longo ou sem TTL.

⸻

TTL é o mecanismo que transforma cache em algo inteligente.

Sem TTL → performance máxima, risco de desatualização.
Com TTL → equilíbrio entre velocidade e confiabilidade.

⸻

## 2.4 Invalidação manual
```python
st.cache_data.clear()
``` 
Útil em:
	•	Atualizações administrativas
	•	Reset de ambiente
	•	Debug

⸻

## 2.5 Problemas comuns - modificar o objeto diretamente
 
Quando você usa cache, o Streamlit armazena o **resultado da função** e reutiliza exatamente aquele objeto nas próximas execuções.

Se você modificar esse objeto diretamente, estará alterando também a versão armazenada no cache.

Isso pode gerar:

- Efeitos colaterais difíceis de rastrear
- Dados “duplicados”
- Colunas sendo criadas múltiplas vezes
- Comportamento inconsistente entre usuários

---

### Errado

```python
@st.cache_data
def carregar_dados():
    return pd.read_csv("dados.csv")

df = carregar_dados()

# Aqui você está alterando o próprio objeto cacheado
df["nova_coluna"] = df["valor"] * 2
```

O que acontece:
	•	carregar_dados() retorna o mesmo objeto salvo no cache.
	•	Ao adicionar nova_coluna, você modifica o objeto original.
	•	No próximo rerun, essa coluna já existirá.
	•	Se repetir a operação, pode gerar erro ou duplicação.

⸻

### Correto
```python
df = carregar_dados().copy()
```

Agora você trabalha em uma cópia independente
```python
df["nova_coluna"] = df["valor"] * 2
```

O .copy() cria uma nova instância em memória.

O cache permanece intacto.
Você trabalha de forma isolada.

⸻

### Regra mental

Nunca modifique diretamente algo que veio de uma função cacheada.

Sempre trate como imutável.

⸻

## 2.5 Problemas comuns - Dependências invisíveis

O problema

O cache do Streamlit é baseado em:
	•	Código da função
	•	Parâmetros declarados

Se sua função depender de algo externo que não está nos parâmetros, o cache pode não perceber mudanças.

Isso gera comportamento incorreto.

⸻

### Errado

```python
fator = 10

@st.cache_data
def transformar(df):
    # Usa variável externa sem declarar como parâmetro
    return df["valor"] * fator
```

Se você mudar:

fator = 20

O cache pode continuar retornando o valor antigo, porque:
	•	O parâmetro fator não faz parte da assinatura da função.
	•	O hash da função não detecta essa mudança corretamente.

⸻

### Correto

```python
@st.cache_data
def transformar(df, fator):
    return df["valor"] * fator

resultado = transformar(df, fator)
```
Agora:
	•	O valor de fator faz parte da chave de cache.
	•	Se ele mudar → o cache é invalidado automaticamente.
	•	Comportamento previsível.

⸻

### Regra mental

Tudo que influencia o resultado deve ser parâmetro da função.

⸻

# 3 Performance Estrutural

⸻

## 3.1 Separação de responsabilidades

Misturar tudo em sequência cria acoplamento forte.

Evite

```python
modelo = carregar_modelo()
dados = carregar_dados()
resultado = modelo.processar(dados)

st.line_chart(resultado)
```

Problemas:
	•	Não está claro o que é dado, recurso ou visualização.
	•	Difícil testar partes isoladamente.
	•	Se algo mudar, tudo pode ser reexecutado.

⸻

Prefira estrutura em camadas
```python
Camada de Dados

@st.cache_data
def carregar_dados():
    return pd.read_csv("dados.csv")

Camada de Processamento

@st.cache_data
def processar(dados):
    modelo = carregar_modelo()
    return modelo.processar(dados)

Camada de Visualização

dados = carregar_dados()
resultado = processar(dados)

st.line_chart(resultado)
```

Agora:
	•	Cada parte tem responsabilidade clara.
	•	Cada camada pode ser cacheada de forma independente.
	•	O código escala melhor.

⸻

## 3.2 Evite recomputação dentro de widgets

Widgets disparam rerun.

Se você colocar processamento pesado logo após um widget, ele será reexecutado a cada interação.

⸻

## 3.3 Uso inteligente de session_state

Centralize estado:
```python
if "dados_filtrados" not in st.session_state:
    st.session_state.dados_filtrados = df
``` 
Isso evita recalcular filtros pesados a cada ajuste fino.

⸻

## 3.4 Lazy loading

Carregue apenas quando necessário:
```python
if st.button("Carregar dados"):
    dados = carregar_dados()
``` 
Evita custo inicial alto.

⸻

# 4 Conectividade

Aplicações reais precisam integrar:
	•	APIs REST
	•	Bancos SQL
	•	Serviços de IA
	•	Armazenamento em nuvem

⸻

## 4.1 Conectando APIs
```python
@st.cache_data(ttl=600)
def buscar_api():
    response = requests.get("https://api.exemplo.com")
    return response.json()
``` 
Boas práticas:
	•	Sempre usar cache.
	•	Tratar timeout.
	•	Validar status code.

⸻

## 4.2 Conexão com Banco de Dados

Padrão recomendado:
```python
@st.cache_resource
def conectar():
    return create_engine("postgresql://...")
``` 
Consulta:
```python
@st.cache_data
def rodar_query(query):
    return pd.read_sql(query, conectar())
``` 
Separar conexão (resource) de query (data).

⸻

## 4.3 Secrets Management

Nunca hardcode credenciais.

Use:
```python
.secrets.toml
``` 
Acesso:
```python
st.secrets["db_password"]
``` 
Essencial para produção.

⸻

## 4.4 Conectando modelos externos

Exemplo: OpenAI, AWS, Azure etc.

Use:
	•	cache_resource para cliente
	•	cache_data para respostas se apropriado
	•	TTL para evitar custo excessivo

⸻

# 5 Performance em Produção

## 5.1 Escalabilidade

Streamlit Community Cloud:
	•	Instâncias limitadas
	•	Recursos limitados
	•	Ideal para protótipo

Deploy corporativo:
	•	Docker
	•	Kubernetes
	•	Reverse proxy
	•	Autoscaling

⸻

## 5.2 Monitoramento

Observe:
	•	Tempo de resposta
	•	Uso de memória
	•	Frequência de rerun
	•	Logs de erro

⸻

## 5.3 Checklist de Aplicação Performática

•	Dados cacheados
•	Recursos cacheados
•	Sem mutação de cache
•	Sem recomputação desnecessária
•	Estado centralizado
•	Credenciais protegidas
•	TTL configurado para APIs

⸻

# Referências

Documentação base utilizada:
	•	Streamlit Caching: https://docs.streamlit.io/develop/concepts/architecture/caching
	•	Execution Flow: https://docs.streamlit.io/develop/concepts/architecture
	•	Session State: https://docs.streamlit.io/develop/api-reference/session-state
	•	Secrets Management: https://docs.streamlit.io/develop/concepts/connections/secrets-management
	•	Connecting to Data Sources: https://docs.streamlit.io/develop/concepts/connections

