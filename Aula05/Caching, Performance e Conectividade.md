# 1 Modelo de Execução do Streamlit (15 min)

## Conceito fundamental

Streamlit executa o script **de cima para baixo a cada interação**.

Isso significa:

- Toda modificação em widget → dispara rerun.
- Variáveis são recriadas.
- Objetos são reinstanciados.
- Código pesado pode ser reexecutado.

Arquitetura mental:

Estado atual → Script roda inteiro → UI é reconstruída

Não existe manipulação incremental de DOM.

Isso traz:

✔ Simplicidade  
✔ Previsibilidade  
❌ Risco de ineficiência se mal estruturado  

---

## Fluxo Interno Simplificado

1. Usuário interage.
2. Frontend envia evento.
3. Backend reexecuta o script.
4. Novo estado é reconciliado.
5. UI é atualizada.

Portanto:

> Performance em Streamlit é controle inteligente do que roda no rerun.

---

# 2️⃣ Caching Profundo

Caching é o pilar de performance no Streamlit moderno.

Desde as versões recentes, o sistema foi redesenhado.

Temos dois tipos principais:

- `st.cache_data`
- `st.cache_resource`

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

2.2 st.cache_resource

Usado para:
	•	Modelos de IA
	•	Conexões de banco
	•	Clientes de API
	•	Objetos pesados

Exemplo:

@st.cache_resource
def carregar_modelo():
    return ModeloGigante()

Diferença conceitual:

cache_data	cache_resource
Guarda resultado	Guarda instância
Serializa	Mantém objeto vivo
Ideal para dados	Ideal para recursos


⸻

2.3 TTL (Time to Live)

Controle de expiração:

@st.cache_data(ttl=3600)
def carregar_api():
    return requests.get(url).json()

Após 1 hora → invalida cache.

Essencial para:
	•	Dados externos
	•	APIs dinâmicas
	•	Dashboards de monitoramento

⸻

2.4 Invalidação manual

st.cache_data.clear()

Útil em:
	•	Atualizações administrativas
	•	Reset de ambiente
	•	Debug

⸻

2.5 Problemas comuns

1. Mutação de objetos

Nunca altere objeto cacheado diretamente.

Errado:

df = carregar_dados()
df["nova_coluna"] = ...

Certo:

df = carregar_dados().copy()


⸻

2. Dependências invisíveis

Se função depende de variável externa não declarada como parâmetro, o cache pode se comportar errado.

Sempre passe tudo como argumento.

⸻

3 Performance Estrutural

Caching resolve 70% dos problemas.

Os outros 30% vêm de arquitetura.

⸻

3.1 Separação de responsabilidades

Evite:

modelo = carregar_modelo()
dados = carregar_dados()
resultado = modelo.processar(dados)
st.line_chart(resultado)

Prefira:
	•	Camada de dados
	•	Camada de processamento
	•	Camada de visualização

⸻

3.2 Evite recomputação dentro de widgets

Errado:

coluna = st.selectbox("Coluna", df.columns)
df_processado = modelo.processar(df)
st.line_chart(df_processado[coluna])

Correto:

df_processado = processar(df)  # cacheado
coluna = st.selectbox("Coluna", df_processado.columns)
st.line_chart(df_processado[coluna])


⸻

3.3 Uso inteligente de session_state

Centralize estado:

if "dados_filtrados" not in st.session_state:
    st.session_state.dados_filtrados = df

Isso evita recalcular filtros pesados a cada ajuste fino.

⸻

3.4 Lazy loading

Carregue apenas quando necessário:

if st.button("Carregar dados"):
    dados = carregar_dados()

Evita custo inicial alto.

⸻

4 Conectividade

Aplicações reais precisam integrar:
	•	APIs REST
	•	Bancos SQL
	•	Serviços de IA
	•	Armazenamento em nuvem

⸻

4.1 Conectando APIs

@st.cache_data(ttl=600)
def buscar_api():
    response = requests.get("https://api.exemplo.com")
    return response.json()

Boas práticas:
	•	Sempre usar cache.
	•	Tratar timeout.
	•	Validar status code.

⸻

4.2 Conexão com Banco de Dados

Padrão recomendado:

@st.cache_resource
def conectar():
    return create_engine("postgresql://...")

Consulta:

@st.cache_data
def rodar_query(query):
    return pd.read_sql(query, conectar())

Separar conexão (resource) de query (data).

⸻

4.3 Secrets Management

Nunca hardcode credenciais.

Use:

.secrets.toml

Acesso:

st.secrets["db_password"]

Essencial para produção.

⸻

4.4 Conectando modelos externos

Exemplo: OpenAI, AWS, Azure etc.

Use:
	•	cache_resource para cliente
	•	cache_data para respostas se apropriado
	•	TTL para evitar custo excessivo

⸻

5 Performance em Produção

5.1 Escalabilidade

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

5.2 Monitoramento

Observe:
	•	Tempo de resposta
	•	Uso de memória
	•	Frequência de rerun
	•	Logs de erro

⸻

5.3 Checklist de Aplicação Performática
	•	Dados cacheados
	•	Recursos cacheados
	•	Sem mutação de cache
	•	Sem recomputação desnecessária
	•	Estado centralizado
	•	Credenciais protegidas
	•	TTL configurado para APIs

⸻

Referências

Documentação base utilizada:
	•	Streamlit Caching:
https://docs.streamlit.io/develop/concepts/architecture/caching
	•	Execution Flow:
https://docs.streamlit.io/develop/concepts/architecture
	•	Session State:
https://docs.streamlit.io/develop/api-reference/session-state
	•	Secrets Management:
https://docs.streamlit.io/develop/concepts/connections/secrets-management
	•	Connecting to Data Sources:
https://docs.streamlit.io/develop/concepts/connections

