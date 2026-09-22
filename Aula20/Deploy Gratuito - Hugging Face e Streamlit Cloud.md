# Aula 20 — Deploy Gratuito: a API no Hugging Face, o front no Streamlit Cloud

Na aula anterior o Forzy foi empacotado em containers. Hoje ele roda assim na sua máquina:

```
docker compose up
  ├── forzy-backend   → localhost:8000   FastAPI + SQLite + LangSmith
  └── forzy-frontend  → localhost:7860   Gradio
```

Os dois containers se enxergam porque estão na mesma rede do compose, e você os acessa porque as portas foram publicadas na sua máquina. Só que tudo isso morre no instante em que você fecha o terminal — e ninguém além de você jamais viu o projeto funcionando.

Hoje trocamos `localhost` por dois endereços públicos:

```
Streamlit Cloud                        Hugging Face Spaces
┌──────────────────────────┐   HTTPS   ┌──────────────────────────┐
│  Front-end               │ ────────▶ │  API FastAPI (Docker)    │
│  seu-app.streamlit.app   │           │  usuario-forzy-api       │
│                          │           │     .hf.space            │
│  secrets: API_URL,       │           │  secrets: API_KEY,       │
│           API_KEY        │           │           LANGSMITH_*    │
└──────────────────────────┘           └──────────────────────────┘
                                                    │
                                                    ▼
                                            LangSmith (traces)
```

---

# 1. Por que o Front e o Back Vão para Lugares Diferentes

A pergunta mais natural é: por que não colocar tudo no mesmo lugar?

A resposta está na natureza de cada plataforma gratuita. Nenhuma delas roda "qualquer coisa": cada uma tem um formato de aplicação que sabe executar.

| Plataforma | O que ela executa | O que ela **não** executa |
|---|---|---|
| **Streamlit Community Cloud** | Um app Streamlit, a partir de um `app.py` no GitHub | Gradio, FastAPI, Docker, qualquer outro processo |
| **Hugging Face Spaces (SDK gradio)** | Um app Gradio, a partir de um `app.py` | FastAPI como serviço próprio, Streamlit com back separado |
| **Hugging Face Spaces (SDK streamlit)** | Um app Streamlit | Igual ao anterior |
| **Hugging Face Spaces (SDK docker)** | **Qualquer** coisa que caiba num Dockerfile | Nada — é o mais flexível dos quatro |

Repare na consequência direta para o Forzy: **o FastAPI só tem um lugar gratuito para morar entre essas opções, que é um Space em modo Docker.** O Streamlit Cloud não roda FastAPI, e um Space em modo `gradio` ou `streamlit` executa exatamente um script de interface, não um servidor de API.

É por isso que a aula anterior precisava existir. Sem o Dockerfile, a API do Forzy simplesmente não teria como ser publicada aqui.

E o front? O front tem várias opções, e escolhemos pela tecnologia que ele usa:

- front em **Streamlit** → Streamlit Community Cloud (a casa natural dele);
- front em **Gradio** → Hugging Face Spaces com SDK `gradio` (a casa natural dele).

As duas rotas estão descritas nas seções 5 e 6. Escolha a que corresponde ao seu projeto — ou faça as duas, já que a API é a mesma e os dois fronts podem conviver apontando para ela.

## 1.1 A separação que já estava pronta

Talvez o ponto mais importante desta aula não seja técnico. Repare no que estamos prestes a fazer: colocar o front num provedor, o back em outro, e fazer os dois conversarem por HTTP, sem que nenhuma linha de regra de negócio precise ser movida ou duplicada.

Isso só é possível porque o Forzy foi separado em dois processos independentes. No Sprint original, com o Gradio acessando o `motor.db` diretamente, essa arquitetura seria impensável: o front teria que carregar o banco junto.

Guarde essa observação, porque ela reaparece nas aulas de mobile: **o produto é a API. O front é substituível.** Você vai comprovar isso literalmente ao trocar o Gradio por um Streamlit sem tocar no back-end.

---

# 2. Preparando o Repositório

Antes de qualquer deploy, o repositório precisa estar em ordem. Duas regras valem para as duas plataformas:

**O repositório precisa estar no GitHub, público.** As duas plataformas fazem o deploy a partir de um repositório Git. O Streamlit Cloud, no plano gratuito, só publica repositórios públicos.

**Nenhum segredo pode estar no código.** Isso deixa de ser boa prática e passa a ser uma questão concreta: um repositório público é indexado por buscadores, e existem robôs que varrem o GitHub procurando chaves de API expostas. Uma chave da Anthropic ou do LangSmith vazada é usada em minutos.

Rode esta verificação antes do primeiro push:

```bash
# Nenhum destes comandos deve encontrar nada em arquivos .py

grep -rn "lsv2_"            --include="*.py" .   # chaves do LangSmith
grep -rn "sk-ant"           --include="*.py" .   # chaves da Anthropic
grep -rn "API_KEY *= *[\"']" --include="*.py" .   # chave escrita no código
grep -rn "localhost"        --include="*.py" .   # endereços locais esquecidos
```

E confirme que o `.gitignore` cobre os arquivos sensíveis:

```text
# .gitignore
.env
*.env
.streamlit/secrets.toml
__pycache__/
*.pyc
.venv/
venv/
```

> **Se uma chave já foi commitada por engano**, não basta apagar o arquivo e commitar de novo: ela continua no histórico do Git, acessível a qualquer um. O caminho correto é **revogar a chave** no painel do serviço e gerar outra. Considere a chave antiga perdida.

## 2.1 O que vai para o repositório

Estrutura sugerida, com os dois fronts convivendo:

```
forzy/
├── docker-compose.yml         ← desenvolvimento local (aula anterior)
├── backend/                   ← publicado no Hugging Face Spaces (Docker)
│   ├── Dockerfile
│   ├── README.md              ← NOVO: metadados do Space
│   ├── requirements.txt
│   ├── main.py
│   ├── motor.db
│   ├── auth/ models/ providers/ routers/
│   └── .env.example
├── frontend/                  ← versão Gradio (Space com SDK gradio)
│   ├── app.py
│   ├── requirements.txt
│   └── ui/ state/ features/ pipelines/ providers/
└── frontend-streamlit/        ← versão Streamlit (Streamlit Cloud)
    ├── app.py
    ├── requirements.txt
    ├── .streamlit/config.toml
    └── ui/ state/ features/ pipelines/ providers/
```

Nenhuma dessas pastas depende das outras. É por isso que elas podem ser publicadas em plataformas diferentes.

---

# 3. Parte 1 — A API no Hugging Face Spaces

Esta é a parte que precisa vir primeiro, por um motivo prático: o front só pode ser configurado depois que você souber o endereço da API.

## 3.1 Criando a conta e o Space

1. Crie uma conta gratuita em [huggingface.co](https://huggingface.co).
2. No menu do seu perfil, escolha **New Space**.
3. Preencha:

```
Owner:        seu-usuario
Space name:   forzy-api
License:      mit
SDK:          Docker  →  Blank (sem template)
Hardware:     CPU basic (gratuito)
Visibility:   Public
```

**Por que Public?** Num Space privado, toda requisição precisa de um token do Hugging Face além da sua própria `API_KEY` — o que complicaria a configuração do front sem ganho real para esta aula. A API continua protegida pela `X-API-Key`: qualquer pessoa consegue ver a documentação em `/docs`, mas ninguém consegue ler ou gravar dados sem a chave.

Ao criar, o Hugging Face gera um repositório Git vazio em:

```
https://huggingface.co/spaces/seu-usuario/forzy-api
```

E a aplicação, quando estiver no ar, responderá em:

```
https://seu-usuario-forzy-api.hf.space
```

Repare no formato do endereço da aplicação: usuário e nome do Space unidos por hífen, seguidos de `.hf.space`. Guarde essa URL, porque ela vai virar o `API_URL` do front.

## 3.2 O `README.md` do Space — o arquivo de configuração disfarçado

Um Space é configurado por um bloco YAML no topo do `README.md`. Sem esse bloco, o Hugging Face não sabe qual SDK usar e o deploy falha.

Crie o arquivo `backend/README.md`:

```markdown
---
title: Forzy API
emoji: ⚙️
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 8000
pinned: false
---

# Forzy · Digital Twin — API

Back-end FastAPI do projeto Forzy: cadastro de motores industriais,
leitura de sensores e classificação de severidade segundo a ISO 10816.

Documentação interativa: `/docs`
Todos os endpoints exigem o header `X-API-Key`.
```

Duas linhas merecem atenção:

**`sdk: docker`** — diz ao Hugging Face para construir a imagem a partir do `Dockerfile` da raiz do Space, em vez de procurar um app Gradio ou Streamlit.

**`app_port: 8000`** — a porta que a sua aplicação escuta dentro do container. O Hugging Face assume **7860** quando essa linha não existe, porque é a porta padrão do Gradio. Como o nosso `Dockerfile` termina com `--port 8000`, precisamos declarar isso. As duas informações têm que bater: se o Space ficar preso em "Building" ou "Runtime error" sem log de erro claro, a porta é o primeiro suspeito.

> **Alternativa:** em vez de declarar `app_port`, você pode alterar o `CMD` do Dockerfile para `--port 7860` e não declarar nada. As duas formas funcionam. Declarar a porta é mais explícito e deixa o Dockerfile igual ao que roda no compose.

## 3.3 O Dockerfile — o que muda (e o que não muda)

Boa notícia: **o `backend/Dockerfile` da aula anterior funciona sem alteração nenhuma.** Aquelas duas decisões que pareciam detalhe agora se pagam:

```dockerfile
RUN useradd --create-home --uid 1000 forzy
...
USER forzy
```

O Hugging Face executa o container como um usuário sem privilégios de UID 1000. Um Dockerfile que roda como `root` e grava em `/app` quebra com erro de permissão no Space. O nosso já nasceu certo.

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

O `--host 0.0.0.0` é o mesmo motivo da aula anterior, agora ainda mais crítico: o roteador do Hugging Face fica fora do container e precisa alcançar o processo.

## 3.4 Enviando os arquivos

Um Space é um repositório Git. O envio é um `git push` comum:

```bash
# Clone o Space vazio numa pasta ao lado do seu projeto
git clone https://huggingface.co/spaces/seu-usuario/forzy-api
cd forzy-api

# Copie o conteúdo de backend/ para cá (Dockerfile, README.md, código, motor.db)
# ATENÇÃO: não copie o .env

git add .
git commit -m "deploy inicial da API do Forzy"
git push
```

Na primeira vez que você fizer `push`, o Hugging Face pede autenticação. A senha **não** é a da sua conta: é um **Access Token** com permissão de escrita, gerado em Settings → Access Tokens → New token (tipo *Write*).

Assim que o push termina, o Space começa a construir a imagem. Acompanhe pela aba **Logs → Build**, no próprio Space: você vai ver exatamente as mesmas etapas do `docker build` local, uma para cada instrução do Dockerfile. A primeira construção leva alguns minutos.

> **Alternativa sem clonar:** a aba **Files** do Space permite enviar arquivos pelo navegador. Funciona para um teste rápido, mas com o Forzy inteiro — que tem subpastas — o `git push` é muito mais prático.

## 3.5 Configurando os segredos

Enquanto a imagem constrói, configure as variáveis. No Space: **Settings → Variables and secrets**.

O Hugging Face separa dois tipos, e a diferença importa:

| Tipo | Visível para | Use para |
|---|---|---|
| **Variable** | Qualquer pessoa que abra o Space | `LANGSMITH_PROJECT`, `APP_VERSION` |
| **Secret** | Só para o processo em execução | `API_KEY`, `LANGSMITH_API_KEY` |

Cadastre:

```
Secret    API_KEY            = uma-chave-forte-de-producao
Secret    LANGSMITH_API_KEY  = lsv2_pt_...
Variable  LANGSMITH_TRACING  = true
Variable  LANGSMITH_PROJECT  = forzy-producao
```

Duas observações:

**Use uma chave de produção diferente da chave de desenvolvimento.** A chave local circula em `.env` de várias máquinas do grupo, aparece em prints de tela e em screenshots de aula. A de produção não deve.

**`LANGSMITH_PROJECT=forzy-producao`**, e não `forzy-digital-twin`. Separar os traces de produção dos de desenvolvimento evita que os seus testes locais poluam as métricas do que está no ar — e é exatamente assim que times de verdade organizam a observabilidade.

Depois de salvar, o Space reinicia sozinho. As variáveis chegam ao container do mesmo jeito que o `--env-file` fazia localmente: o `os.getenv("API_KEY")` do `auth/seguranca.py` continua lendo do ambiente, sem nenhuma alteração de código.

## 3.6 Testando a API no ar

Com o Space marcado como **Running**, teste antes de mexer no front:

```bash
# 1. A rota raiz não exige chave
curl https://seu-usuario-forzy-api.hf.space/

# Esperado: {"status":"ok","servico":"Forzy Digital Twin API"}

# 2. Sem a chave, os endpoints recusam
curl -i https://seu-usuario-forzy-api.hf.space/v1/equipamentos
# Esperado: HTTP/2 403 (ou 401)

# 3. Com a chave, respondem
curl -H "X-API-Key: uma-chave-forte-de-producao" \
     https://seu-usuario-forzy-api.hf.space/v1/equipamentos/tags
# Esperado: ["MTR-001","MTR-002",...]
```

E pelo navegador, `https://seu-usuario-forzy-api.hf.space/docs` abre o Swagger. Clique em **Authorize**, cole a chave de produção e teste `GET /v1/sensores/MTR-001/leitura-atual`.

**Só avance para a Parte 2 quando esses três testes passarem.** Depurar front e back ao mesmo tempo, sem saber de que lado está o problema, é a forma mais lenta de trabalhar — e foi o mesmo conselho da aula de refatoração.

## 3.7 As três limitações que você acabou de aceitar

O Space está no ar e é gratuito. Em troca, três coisas passam a ser verdade. Entendê-las é mais importante do que o deploy em si.

### O banco é efêmero

Lembra do experimento da aula anterior, em que o motor cadastrado sumia quando o container era removido e recriado? **No Hugging Face isso acontece sozinho.** O disco do container é descartável: quando o Space reinicia — por um novo push, por uma mudança de segredo, por hibernação ou por manutenção da plataforma — um container novo nasce da imagem, com o `motor.db` original.

Faça o teste e veja com os próprios olhos:

1. Cadastre o `MTR-099` pelo Swagger do Space.
2. Confirme com `GET /v1/equipamentos/MTR-099`.
3. Em Settings, clique em **Restart this Space**.
4. Consulte de novo. O motor sumiu.

Não é um defeito da plataforma, é o modelo dela. Um container de nuvem é descartável por definição, e nesse modelo o banco tem que morar fora dele.

O que um sistema real faria:

- **Volume persistente**: o Hugging Face oferece armazenamento permanente como recurso pago.
- **Banco gerenciado externo**: o SQLite dá lugar a um Postgres hospedado, que roda como serviço separado e sobrevive a qualquer coisa que aconteça com a aplicação.
- **Servidor próprio com volume**, que é o caminho da próxima aula, na AWS.

Para o Forzy em sala, aceite o comportamento e saiba explicá-lo. Se alguém perguntar na apresentação "e se eu cadastrar um motor?", a resposta certa não é "não pensei nisso" — é "no tier gratuito o disco é efêmero; a persistência exigiria volume ou banco gerenciado".

### A aplicação hiberna

Spaces gratuitos são pausados depois de um período sem acesso. O primeiro acesso depois disso não dá erro: ele **acorda** o Space, e essa requisição demora — de alguns segundos a mais de um minuto, porque o container precisa subir do zero.

Consequência prática para o front: um `timeout` de 10 segundos, que era generoso em rede local, passa a ser apertado. Por isso o `api_provider` da versão Streamlit usa 15 segundos. Vale aumentar também no Gradio.

E consequência para a apresentação: **abra o Space alguns minutos antes de apresentar**, para que ele já esteja acordado quando o professor ou o avaliador clicar.

### Você não controla a rede

Sem IP fixo, sem regra de firewall, sem escolher região, sem decidir quem acessa o quê. Para uma demonstração isso é irrelevante. Para um sistema que lê dados proprietários de uma planta industrial, é exatamente o tipo de coisa que o cliente exige controlar — e é o motivo da próxima aula ser sobre AWS.

---

# 4. O Front Precisa de Três Mudanças

Independentemente da plataforma escolhida, sair do `localhost` exige três ajustes no front. Eles são os mesmos nos dois caminhos.

## 4.1 O endereço da API

Localmente, `API_URL` era `http://localhost:8000` (ou `http://backend:8000` dentro do compose). Agora é a URL pública do Space:

```
API_URL = https://seu-usuario-forzy-api.hf.space
```

Repare que é **HTTPS**, sem porta. O roteador do Hugging Face recebe na 443 e encaminha internamente para a porta que você declarou em `app_port`. Isso também significa que o tráfego entre o front e a API passa a ser criptografado, o que não acontecia em `http://localhost`.

## 4.2 A chave precisa ser a mesma dos dois lados

A `API_KEY` configurada como segredo do Space e a `API_KEY` configurada no front têm que ter **exatamente** o mesmo valor. Um espaço em branco a mais, uma aspa copiada junto, e todas as chamadas voltam `401`.

Esse é, com folga, o erro mais comum do primeiro deploy.

## 4.3 O tempo de espera precisa crescer

Pelo motivo da hibernação, explicado acima: 10 segundos deixam de bastar.

---

# 5. Parte 2A — O Front Streamlit no Streamlit Community Cloud

Este é o caminho para a versão Streamlit do Forzy (pasta `frontend-streamlit/`).

## 5.1 O que mudou do Gradio para o Streamlit

Antes do deploy, vale entender o que foi reescrito — porque **quase nada foi**.

| Camada | Mudou? | O que aconteceu |
|---|---|---|
| `providers/api_provider.py` | Pouco | Mesmas funções, mesmas rotas. Ganhou leitura de `st.secrets` e memorização de respostas |
| `pipelines/*.py` | Pouco | Passaram a devolver `DataFrame` em vez de lista de listas, porque é o que o `st.dataframe` espera. O gráfico Plotly é idêntico |
| `state/app_state.py` | Sim | `gr.State` deu lugar a `st.session_state` |
| `ui/sidebar.py` | Sim | `gr.Sidebar` deu lugar a `st.sidebar` |
| `features/*/page.py` | Sim | Reescritas — é a camada de UI, afinal |
| **Back-end** | **Não** | **Nenhuma linha** |

A arquitetura em camadas se pagou: a reescrita ficou contida nas camadas que existem justamente para mudar.

### A diferença de fundo entre os dois modelos

A maior adaptação não é de sintaxe, é de modelo de execução. Vale entender, porque quase todo bug de quem vem do Gradio nasce daqui.

**No Gradio**, você monta a interface uma vez e registra eventos. Quando o usuário clica num botão, só a função daquele evento roda, e só os componentes listados em `outputs` são atualizados. O resto da tela nem é tocado.

**No Streamlit**, não existem eventos. Qualquer interação — um clique, uma escolha num seletor, uma tecla num campo — reexecuta **o script inteiro**, de cima para baixo, e redesenha a tela do zero. O `st.button()` não recebe uma função: ele devolve `True` no exato rerun em que foi clicado.

```python
# Gradio: registra um callback, atualiza um componente específico
botao.click(fn=carregar_dados, inputs=dropdown, outputs=tabela)

# Streamlit: o script reexecuta e você reage ao resultado do clique
if st.button("Carregar"):
    tabela = carregar_dados(tag)
```

Três consequências no Forzy:

**A cascata do dashboard ficou mais simples.** No Gradio eram dois eventos `.change()` para reescrever as opções dos dropdowns dependentes. No Streamlit, quando a linha do seletor de Áreas é executada, a planta escolhida logo acima já está na variável:

```python
planta = c1.selectbox("Planta", api_provider.listar_plantas())
areas  = api_provider.listar_areas(planta)      # já usa a planta escolhida
area   = c2.selectbox("Área", areas)
```

**O cache deixou de ser opcional.** Se o script inteiro roda de novo a cada clique, todas as chamadas HTTP da tela se repetem. Sem cache, escolher uma TAG no dashboard dispararia de novo as consultas de plantas, áreas e equipamentos — quatro requisições desnecessárias por clique, contra um Space que hiberna. Por isso as leituras do `api_provider` são memorizadas:

```python
@st.cache_data(ttl=120, show_spinner=False)
def listar_todos() -> list[dict]:
    return _get("/v1/equipamentos", feature="equipamentos") or []
```

O `ttl` (*time to live*) é o tempo, em segundos, que a resposta vale antes de ser buscada de novo. Os valores foram escolhidos pela natureza do dado: o cadastro muda pouco (120 s), a hierarquia da planta é praticamente fixa (600 s), a telemetria envelhece rápido (20 s).

Escritas **nunca** são memorizadas — o `salvar()` não tem decorador. E, logo depois de gravar, o cache precisa ser descartado, senão a lista continuaria mostrando os dados antigos:

```python
sucesso, mensagem = pipeline.salvar_equipamento(...)
if sucesso:
    api_provider.limpar_cache()   # st.cache_data.clear()
```

**A identificação de sessão melhorou.** No Gradio, o `X-Session-Id` era um UUID por **processo**: todos os usuários do app compartilhavam o mesmo identificador. No Streamlit, cada aba do navegador tem o seu `st.session_state`, então conseguimos um identificador por **usuário**:

```python
def _session_id() -> str:
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())
    return st.session_state["_session_id"]
```

No LangSmith, isso significa poder filtrar por `metadata.session_id` e reconstruir exatamente o que uma pessoa fez — o que antes era impossível.

## 5.2 `st.secrets` — o `.env` da nuvem

O Streamlit Cloud não tem arquivo `.env`. Ele injeta as configurações por um mecanismo próprio, o `st.secrets`, que lê um arquivo TOML.

Localmente, esse arquivo fica em `.streamlit/secrets.toml` (e **nunca** vai para o Git). Na nuvem, o mesmo conteúdo é colado no painel.

```toml
# .streamlit/secrets.toml — nunca commitar
API_URL = "https://seu-usuario-forzy-api.hf.space"
API_KEY = "uma-chave-forte-de-producao"
APP_VERSION = "2.0.0-streamlit"
```

Para que o mesmo código funcione nos dois ambientes, o `api_provider` procura a configuração em duas fontes, em ordem:

```python
def _config(chave: str, padrao: str = "") -> str:
    """
    1. st.secrets  — usado no Streamlit Community Cloud
    2. os.environ  — usado localmente (via .env) e no Docker

    Acessar st.secrets sem o arquivo secrets.toml levanta exceção,
    por isso a leitura fica protegida.
    """
    try:
        if chave in st.secrets:
            return str(st.secrets[chave])
    except Exception:
        pass
    return os.getenv(chave, padrao)
```

Esse padrão de "procurar em várias fontes, com uma ordem de precedência" é comum em aplicações que rodam em mais de um ambiente. Vale guardar.

Commite um `secrets.toml.example`, com valores fictícios, para quem clonar o projeto saber o que precisa preencher — mesma ideia do `.env.example`.

## 5.3 Rodando localmente antes de publicar

Não publique sem rodar. Na pasta `frontend-streamlit/`:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`. Aponte-o para a API do Space (não para o `localhost:8000`), assim você testa exatamente a configuração que vai para a nuvem:

```bash
# frontend-streamlit/.env
API_URL=https://seu-usuario-forzy-api.hf.space
API_KEY=uma-chave-forte-de-producao
APP_VERSION=2.0.0-streamlit
```

Percorra as quatro telas. Se tudo funcionar aqui, o deploy é quase burocracia.

## 5.4 O `requirements.txt`

```text
streamlit>=1.49.0
pandas>=2.0.0
plotly>=5.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

A versão mínima do Streamlit não é arbitrária. O front usa `width="stretch"` em botões, tabelas e gráficos — o parâmetro que substituiu o antigo `use_container_width`, disponível a partir da 1.49. Com uma versão mais antiga, o app quebra.

O `pandas` entrou porque as pipelines passaram a devolver `DataFrame`. O `gradio` saiu.

> **Onde colocar o arquivo:** o Streamlit Cloud procura o `requirements.txt` na mesma pasta do arquivo principal ou na raiz do repositório. Com o front numa subpasta, mantenha o arquivo **dentro dela**, ao lado do `app.py`.

## 5.5 Publicando

1. Faça o push do repositório para o GitHub.
2. Acesse [share.streamlit.io](https://share.streamlit.io) e entre com a conta do GitHub.
3. Autorize o acesso aos seus repositórios.
4. Clique em **Create app** → **Deploy a public app from GitHub**.
5. Preencha:

```
Repository:       seu-usuario/forzy
Branch:           main
Main file path:   frontend-streamlit/app.py
App URL:          forzy-digital-twin        (escolha um nome disponível)
```

6. Antes de confirmar, abra **Advanced settings → Secrets** e cole o conteúdo do seu `secrets.toml`:

```toml
API_URL = "https://seu-usuario-forzy-api.hf.space"
API_KEY = "uma-chave-forte-de-producao"
APP_VERSION = "2.0.0-streamlit"
```

7. Clique em **Deploy**.

A primeira publicação leva alguns minutos: a plataforma cria o ambiente, instala as dependências e inicia o app. Os logs aparecem na própria tela — é lá que você descobre um pacote faltando no `requirements.txt`.

Ao final, o app responde em:

```
https://forzy-digital-twin.streamlit.app
```

## 5.6 Atualizações automáticas

O Streamlit Cloud observa o repositório: **cada push na branch publicada reimplanta o app**. Não existe botão de "publicar de novo" — o `git push` é o deploy.

Os segredos são a exceção, e é importante entender por quê: eles ficam na plataforma, não no repositório. Mudar um segredo é feito em **Settings → Secrets**, e o app reinicia em seguida.

---

# 6. Parte 2B — O Front Gradio no Hugging Face Spaces

Este é o caminho para quem mantém a versão Gradio do Forzy. O front vai para um **segundo Space**, separado do da API.

## 6.1 Por que dois Spaces, e não um só

Seria possível rodar o FastAPI e o Gradio no mesmo container, com um `CMD` que sobe os dois processos. Você encontra essa receita em muitos tutoriais:

```dockerfile
# Funciona, mas não faça isso no Forzy
CMD ["sh", "-c", "uvicorn main:app --port 8000 & python app.py"]
```

Evite, por três motivos:

1. **Desfaz o trabalho da refatoração.** O objetivo de separar front e back foi poder escalar, atualizar e monitorar cada um de forma independente. Colocá-los no mesmo container junta tudo de novo.
2. **Esconde falhas.** Com dois processos no mesmo container, se o `uvicorn` morrer, o container continua "rodando" porque o Gradio segue de pé. Ninguém fica sabendo.
3. **Não é o que acontece em produção.** Front e API em servidores diferentes é o arranjo normal, e é o que você vai reproduzir na AWS.

Dois Spaces custam o mesmo que um: zero.

## 6.2 Criando o Space do front

Repita o processo da seção 3.1, com estas diferenças:

```
Space name:  forzy-app
SDK:         Gradio
Hardware:    CPU basic
Visibility:  Public
```

Com o SDK `gradio`, o Hugging Face não precisa de Dockerfile: ele instala o `requirements.txt` e executa o `app.py` sozinho.

O `README.md` do Space fica assim:

```markdown
---
title: Forzy Digital Twin
emoji: ⚙️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Forzy · Digital Twin

Interface de monitoramento de motores industriais.
Consome a API publicada em `seu-usuario-forzy-api.hf.space`.
```

**`sdk_version`** deve bater com a versão do Gradio que você testou localmente. Deixar a plataforma escolher a versão mais recente é pedir para o app quebrar num dia qualquer, por uma mudança de API de algum componente.

**`app_file: app.py`** indica o arquivo a executar.

## 6.3 O que ajustar no código Gradio

**Segredos.** O Hugging Face injeta variáveis de ambiente, exatamente como o `--env-file` fazia. O `load_dotenv()` do `api_provider` não encontra arquivo nenhum e segue adiante; o `os.getenv` lê do ambiente. **Nenhuma alteração de código é necessária.**

Em Settings → Variables and secrets do Space do front:

```
Secret    API_KEY      = uma-chave-forte-de-producao   (a mesma da API)
Variable  API_URL      = https://seu-usuario-forzy-api.hf.space
Variable  APP_VERSION  = 1.4.0
```

**Tempo de espera.** Aumente o `_TIMEOUT` no `api_provider` de 10 para 15 segundos, pelo motivo da hibernação.

**O `launch()`.** O seu `app.py` termina com:

```python
app.launch(share=False, inbrowser=True)
```

O `inbrowser=True` tenta abrir um navegador na máquina onde o processo roda — o que num servidor não faz sentido. Troque por:

```python
app.launch()
```

Sem argumentos, o Gradio respeita as variáveis `GRADIO_SERVER_NAME` e `GRADIO_SERVER_PORT` que o Hugging Face já define. É a mesma lição da aula anterior: valores fixos no código vencem as variáveis de ambiente, e é por isso que o `launch()` deve ficar sem parâmetros.

## 6.4 Publicando

```bash
git clone https://huggingface.co/spaces/seu-usuario/forzy-app
cd forzy-app
# copie o conteúdo de frontend/ (sem o .env)
git add .
git commit -m "deploy do front Gradio"
git push
```

O app responde em `https://seu-usuario-forzy-app.hf.space`.

---

# 7. E o CORS? E o HTTPS?

Duas perguntas que sempre aparecem no primeiro deploy.

## 7.1 O CORS continua não se aplicando

O `main.py` do Forzy libera a origem `http://localhost:7860`. Agora o front está em `streamlit.app` ou em `hf.space`. A API vai recusar?

Não. Pelo mesmo motivo da aula anterior: **quem chama a API é o servidor do front, não o navegador do usuário.** O `requests` roda dentro do processo Python do Streamlit ou do Gradio, e o CORS é uma regra que o navegador aplica a chamadas feitas por JavaScript numa página.

```
Navegador do usuário
    │  (abre a página)
    ▼
Servidor do front (Streamlit Cloud / HF Spaces)
    │  requests.get(...)  ← servidor → servidor: o CORS não entra aqui
    ▼
API FastAPI (HF Spaces)
```

Então por que manter a configuração de CORS? Porque ela vai passar a valer no dia em que um cliente chamar a API **de dentro do navegador ou de um app** — que é exatamente o que acontece nas aulas de mobile. Guarde a lista `allow_origins`: ela vai precisar ser atualizada lá.

## 7.2 HTTPS sem esforço

As duas plataformas entregam HTTPS pronto, com certificado válido e renovado automaticamente. Você não gerou certificado, não configurou nada, não pagou nada.

Registre isso como um privilégio do "grátis", porque ele acaba na próxima aula: numa máquina EC2, o HTTPS é problema seu, e resolvê-lo dá trabalho. E não é detalhe estético — sem HTTPS, um app mobile moderno se recusa a chamar a API.

---

# 8. Observabilidade Depois do Deploy

Aqui as aulas de observabilidade se pagam. Você não precisa adivinhar como o Forzy se comporta no ar: você consegue ver.

Abra o LangSmith no projeto `forzy-producao`, use o app publicado por alguns minutos e observe o que chega.

**O cliente aparece sozinho.** O header `X-Client-Platform` identifica de onde veio cada chamada. A versão Streamlit envia `streamlit-cloud`; a Gradio, `gradio-desktop`. Filtrando por `metadata.client_platform`, você compara o comportamento dos dois fronts — que consomem a **mesma** API, com os **mesmos** endpoints.

**A latência real fica visível.** Compare a duração dos traces locais com os de produção. A diferença é a soma de: rede pública, a máquina modesta do tier gratuito e, na primeira chamada após hibernação, o tempo de subir o container. É a primeira vez no curso que você mede o custo do ambiente, e não do código.

**A sessão vira uma linha do tempo.** Filtrando por `metadata.session_id`, você reconstrói tudo o que um usuário fez, em ordem. Quando alguém disser "o dashboard travou", isso deixa de ser um relato e vira um trace.

**A versão distingue um deploy do outro.** Mude `APP_VERSION` de `2.0.0-streamlit` para `2.1.0`, publique e compare latência e taxa de erro entre as duas versões. É o começo de uma prática que times usam a sério: nenhum deploy é considerado bom porque "subiu" — ele é avaliado pelos números depois de subir.

**O efeito do cache pode ser medido.** Abra a página de Equipamentos no app Streamlit publicado, clique em algumas linhas e conte os traces de `endpoint_listar_equipamentos` no LangSmith. Depois comente o decorador `@st.cache_data` da função `listar_todos`, publique e repita. A diferença no número de traces é o trabalho que o cache poupou da API.

> **A ideia para levar:** deploy sem observabilidade é deploy às cegas. O header `X-App-Version`, que na aula de instrumentação parecia um detalhe, agora é o que separa "a versão nova está no ar" de "a versão nova está melhor".

---

# 9. Roteiro de Verificação

Percorra esta lista antes de considerar o deploy concluído:

1. `https://seu-usuario-forzy-api.hf.space/` responde `{"status": "ok", ...}`.
2. `/docs` abre e, com a chave de produção, `GET /v1/equipamentos` devolve os motores.
3. Sem a chave, o mesmo endpoint recusa a requisição.
4. O front publicado abre e a lista de equipamentos carrega.
5. Selecionar uma linha e clicar em "Ver Dados de Sensores" leva à tela de sensores com a TAG já escolhida.
6. O Dashboard navega Planta → Área → Equipamento e desenha o gráfico.
7. O cadastro de um motor novo retorna sucesso e aparece na lista.
8. Reiniciar o Space e consultar o motor cadastrado: ele sumiu — comportamento esperado, e você sabe explicá-lo.
9. No LangSmith, o projeto `forzy-producao` recebe traces com `client_platform`, `feature`, `session_id` e `app_version` preenchidos.
10. Nenhum `.env`, `secrets.toml` ou chave aparece no repositório do GitHub nem no do Space.
11. Abra os dois links no celular. Tudo funciona, porque é HTTPS e é web.

---

# 10. Problemas Comuns

| Sintoma | Causa provável | Como resolver |
|---|---|---|
| Space preso em "Building" ou com "Runtime error" sem log claro | Porta divergente entre o `app_port` do README e o `--port` do Dockerfile | Igualar os dois; na dúvida, usar 7860 nos dois lugares |
| Space constrói mas fica "unhealthy" | Servidor escutando em `127.0.0.1` | Conferir `--host 0.0.0.0` no `CMD` |
| `Permission denied` no log de build do Space | Container rodando como `root` ou gravando em pasta sem permissão | Conferir `useradd --uid 1000` e `USER` no Dockerfile |
| Front publicado mostra a lista vazia | `API_URL` errado, ou faltou o `https://`, ou sobrou uma `/` no fim | Testar a URL com `curl` antes de configurar o front |
| Todas as chamadas voltam `401` | `API_KEY` diferente entre o Space da API e o front | Reconfigurar os dois segredos com o mesmo valor, sem espaços extras |
| Primeira chamada do dia dá timeout | Space hibernado | Aumentar o `_TIMEOUT` para 15 s e abrir o Space antes de apresentar |
| `ModuleNotFoundError` no log de deploy | Biblioteca ausente do `requirements.txt` | Adicionar e fazer push |
| Streamlit Cloud não encontra o app | `Main file path` incorreto | Usar o caminho a partir da raiz do repositório: `frontend-streamlit/app.py` |
| `st.secrets` não encontra a chave | Segredos não salvos no painel, ou TOML mal formatado | Conferir em Settings → Secrets: valores entre aspas, um por linha |
| App Streamlit lento a cada clique | Sem cache, refazendo todas as chamadas a cada rerun | Conferir os decoradores `@st.cache_data` no `api_provider` |
| Salvou um motor mas a lista não mudou | Cache servindo a resposta antiga | Chamar `api_provider.limpar_cache()` depois de toda escrita |
| `use_container_width` mostra aviso de descontinuado | Parâmetro substituído por `width` | Usar `width="stretch"` e exigir `streamlit>=1.49.0` |
| Traces não chegam ao LangSmith | `LANGSMITH_*` não configuradas no Space | Conferir os segredos e reiniciar o Space |
| Motor cadastrado sumiu | Disco efêmero do tier gratuito | Comportamento esperado; ver a seção 3.7 |

---

# 11. Exercícios

**1. O erro mais comum, provocado de propósito.** Altere o segredo `API_KEY` do Space da API para um valor diferente do que está no front. Abra o app publicado e descreva: qual mensagem o usuário vê? Ela é suficiente para alguém de fora entender o que houve? Se não for, melhore o tratamento de erro do `api_provider` para o caso `401` e publique de novo.

**2. Medindo a hibernação.** Deixe o Space sem acesso por algumas horas. Depois, cronometre a primeira requisição (`curl -w "%{time_total}\n" -o /dev/null -s <url>`) e uma segunda logo em seguida. Anote os dois tempos e explique a diferença. Com base no número que você mediu, o `_TIMEOUT` de 15 s é suficiente?

**3. Persistência.** O `motor.db` é efêmero no tier gratuito. Descreva — sem implementar — como você resolveria isso de três formas: com volume persistente pago, com um banco gerenciado externo e com um servidor próprio. Para cada uma, aponte um custo e uma desvantagem.

**4. Dois fronts, uma API.** Publique as duas versões do front (Streamlit e Gradio) apontando para a mesma API. Use as duas por alguns minutos e, no LangSmith, monte um comparativo filtrando por `metadata.client_platform`: número de requisições por feature e latência média. As duas fazem o mesmo número de chamadas para executar a mesma tarefa? Se não, por quê?

**5. O custo de não ter cache.** Comente o decorador `@st.cache_data` da função `listar_todos` do `api_provider`, publique e navegue pelo app. Conte os traces de `endpoint_listar_equipamentos` no LangSmith antes e depois. Quantas requisições o cache poupou? Em que situação o cache seria um problema, e não uma vantagem?

**6. Versionamento de deploy.** Mude `APP_VERSION` para `2.1.0`, adicione um atraso artificial de 1 segundo em algum provider do back-end e publique. No LangSmith, compare a latência entre as duas versões filtrando por `metadata.app_version`. Você conseguiria detectar essa piora **sem** o header de versão?

---

# 12. O que Você Tem ao Final desta Aula

- Um endereço HTTPS público para a API do Forzy, com Swagger acessível e endpoints protegidos por chave.
- Um endereço HTTPS público para a interface, apontando para essa API.
- Segredos configurados nos painéis das plataformas, fora do repositório.
- Deploy automático: `git push` publica a versão nova nas duas plataformas.
- Traces de produção separados dos de desenvolvimento, identificados por cliente, feature, sessão e versão.
- Duas interfaces diferentes consumindo a mesma API — a demonstração prática de que o front é substituível e a API é o produto.
- Clareza sobre as três limitações que você aceitou: disco efêmero, hibernação e ausência de controle de rede. São elas que motivam a próxima aula, sobre AWS.

---

# Referências

- [Hugging Face Spaces — Documentação](https://huggingface.co/docs/hub/spaces)
- [Hugging Face Spaces — Docker](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Hugging Face Spaces — Configuração pelo README](https://huggingface.co/docs/hub/spaces-config-reference)
- [Hugging Face Spaces — Variáveis e segredos](https://huggingface.co/docs/hub/spaces-overview#managing-secrets)
- [Hugging Face Spaces — Armazenamento persistente](https://huggingface.co/docs/hub/spaces-storage)
- [Streamlit Community Cloud — Documentação](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Streamlit — Segredos (`st.secrets`)](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [Streamlit — Cache de dados (`st.cache_data`)](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [Streamlit — Modelo de execução (rerun)](https://docs.streamlit.io/develop/concepts/architecture/run-your-app)
- [Gradio — Publicando no Hugging Face Spaces](https://www.gradio.app/guides/sharing-your-app)
- [FastAPI — Deploy com Docker](https://fastapi.tiangolo.com/deployment/docker/)
