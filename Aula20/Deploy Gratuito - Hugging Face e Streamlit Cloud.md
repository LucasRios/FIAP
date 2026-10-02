# Aula 20 — Deploy Gratuito: a API no Render, o front no Streamlit Cloud

Na aula anterior o Forzy foi empacotado em containers. Hoje ele roda assim na sua máquina:

```
docker compose up
  ├── forzy-backend   → localhost:8000   FastAPI + SQLite + LangSmith
  └── forzy-frontend  → localhost:7860   Gradio
```

Os dois containers se enxergam porque estão na mesma rede do compose, e você os acessa porque as portas foram publicadas na sua máquina. Só que tudo isso morre no instante em que você fecha o docker — e ninguém além de você jamais viu o projeto funcionando.

Hoje trocamos `localhost` por dois endereços públicos:

```
Streamlit Cloud                        Render
┌──────────────────────────┐   HTTPS   ┌──────────────────────────┐
│  Front-end               │ ────────▶ │  API FastAPI             │
│  forzy.streamlit.app     │           │  forzy-api               │
│                          │           │     .onrender.com        │
│  secrets: API_URL,       │           │  env: API_KEY,           │
│           API_KEY        │           │       LANGSMITH_*        │
└──────────────────────────┘           └──────────────────────────┘
                                                    │
                                                    ▼
                                            LangSmith (traces)
```

E a API vai subir **duas vezes**, na mesma plataforma: uma sem Docker nenhum, outra com o Dockerfile que você escreveu na aula passada. Comparar os dois deploys é o ponto central da aula.

---

# 1. Onde Cada Coisa Pode Morar Hoje

Nenhuma plataforma gratuita roda "qualquer coisa". Cada uma sabe executar um formato de aplicação, e é isso que decide onde cada parte do Forzy vai parar.

| Plataforma | Gratuito sem cartão | Aceita Dockerfile | Deploy nativo Python | Hibernação |
|---|---|---|---|---|
| **Render** | sim | **sim** | **sim** | 15 min, acorda em 30–50 s |
| **Streamlit Community Cloud** | sim | não | só Streamlit | sim |
| **Hugging Face Spaces** (sdk gradio/streamlit) | sim | **não mais** | só Gradio/Streamlit | sim |
| Google Cloud Run | exige cartão | sim | via buildpacks | sim, acorda em 5–15 s |
| Koyeb | sim | sim | sim | variável |
| Railway | só US$ 1/mês de crédito | sim | sim | para quando o crédito acaba |

A escolha desta aula:

- **API FastAPI → Render.** É a única opção da lista que aceita, de graça e sem cartão, tanto um Dockerfile quanto código Python puro.
- **Front Streamlit → Streamlit Community Cloud.** A casa natural dele.
- **Front Gradio → Hugging Face Spaces com SDK `gradio`.** Continua gratuito; só o SDK Docker virou pago.

## 1.1 A separação que já estava pronta

Talvez o ponto mais importante desta aula não seja técnico. Repare no que estamos prestes a fazer: colocar o front num provedor, o back em outro, e fazer os dois conversarem por HTTP, sem que nenhuma linha de regra de negócio precise ser movida ou duplicada.

Isso só é possível porque o Forzy foi separado em dois processos independentes. No Sprint original, com o Gradio acessando o `motor.db` diretamente, essa arquitetura seria impensável: o front teria que carregar o banco junto.

Guarde essa observação, porque ela reaparece na aula de mobile: **o produto é a API. O front é substituível.**

---

# 2. Preparando o Repositório

Antes de qualquer deploy, duas regras valem para todas as plataformas.

**O repositório precisa estar no GitHub, público.** Todas elas fazem o deploy a partir de um repositório Git, e o Streamlit Cloud, no plano gratuito, só publica repositórios públicos.

**Nenhum segredo pode estar no código.** Isso deixa de ser boa prática e passa a ser uma questão concreta: um repositório público é indexado por buscadores, e existem robôs que varrem o GitHub procurando chaves de API expostas. Uma chave vazada é usada em minutos.

Rode esta verificação antes do primeiro push:

```bash
# Nenhum destes comandos deve encontrar nada em arquivos .py

grep -rn "lsv2_"             --include="*.py" .   # chaves do LangSmith
grep -rn "sk-ant"            --include="*.py" .   # chaves da Anthropic
grep -rn "API_KEY *= *[\"']" --include="*.py" .   # chave escrita no código
grep -rn "localhost"         --include="*.py" .   # endereços locais esquecidos
```

E confirme que o `.gitignore` cobre os arquivos sensíveis — inclusive as variações, porque `.env` sozinho não cobre um `.env.bak` deixado para trás:

```text
# .gitignore
.env
.env.*
*.env
*.bak
.streamlit/secrets.toml
__pycache__/
*.pyc
.venv/
venv/
```

> **Se uma chave já foi commitada por engano**, não basta apagar o arquivo e commitar de novo: ela continua no histórico do Git, acessível a qualquer um. O caminho correto é **revogar a chave** no painel do serviço e gerar outra. Considere a chave antiga perdida.

## 2.1 O que vai para o repositório

```
forzy/
├── docker-compose.yml         ← desenvolvimento local (aula anterior)
├── backend/                   ← publicado no Render (nos dois modos)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── motor.db
│   ├── auth/ models/ providers/ routers/
│   └── .env.example
├── frontend/                  ← versão Gradio (HF Spaces, SDK gradio)
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

# 3. Parte 1 — A API no Render, sem Docker

Esta parte vem primeiro por um motivo prático: o front só pode ser configurado depois que você souber o endereço da API.

E começamos **sem Docker** de propósito. Assim fica claro, por contraste, o que o Dockerfile acrescenta na Parte 2.

## 3.1 Criando a conta e o serviço

1. Acesse [render.com](https://render.com) e crie a conta entrando com o GitHub. **Não é pedido cartão de crédito** para o plano gratuito.
2. No painel, escolha **New → Web Service**.
3. Conecte o repositório do Forzy e autorize o acesso.
4. Preencha:

```
Name:              forzy-api
Language:          Python 3
Branch:            main
Root Directory:    backend
Start Command:     uvicorn main:app --host 0.0.0.0 --port $PORT
Instance Type:     Free
Health Check Path: /
```

Cinco campos merecem explicação.

**`Root Directory: backend`** — diz ao Render que a aplicação vive numa subpasta. Sem isso, ele procuraria o `requirements.txt` na raiz do repositório e não encontraria nada.

**`Health Check Path: /`** — o Render chama essa rota periodicamente para saber se a aplicação está viva. É exatamente o mesmo papel do `HEALTHCHECK` do Dockerfile, agora feito pela plataforma. Usamos `/` porque é a única rota do Forzy que não exige `X-API-Key`.

**`Instance Type: Free`** — 512 MB de memória e 750 horas por mês. Uma instância rodando o mês inteiro usa cerca de 730 horas, então cabe.

## 3.2 A versão do Python

O runtime nativo escolhe uma versão padrão do Python, que muda com o tempo. Como o Forzy usa sintaxe que exige 3.10 ou superior (`list[dict]`, `dict | None`), e como você testou tudo numa versão específica, fixe-a. Crie o arquivo:

```text
# backend/.python-version
3.12.10
```

Este arquivo é o equivalente, no runtime nativo, à linha `FROM python:3.12.10` do Dockerfile. Repare na diferença de alcance: o Dockerfile fixa o sistema operacional inteiro; o `.python-version` fixa só o interpretador. Volte a esse ponto na seção 6.

## 3.3 Configurando as variáveis de ambiente

Ainda na tela de criação, abra **Environment Variables** e cadastre:

```
API_KEY            = uma-chave-forte-de-producao
LANGSMITH_API_KEY  = lsv2_pt_...
LANGSMITH_TRACING  = true
LANGSMITH_PROJECT  = forzy-producao
```

Duas observações importantes.

**Use uma chave de produção diferente da chave de desenvolvimento.** A chave local circula em arquivos `.env` de várias máquinas do grupo, aparece em prints de tela e em screenshots de aula. A de produção não deve.

**`LANGSMITH_PROJECT=forzy-producao`**, e não `forzy-digital-twin`. Separar os traces de produção dos de desenvolvimento evita que os seus testes locais poluam as métricas do que está no ar — e é exatamente assim que times de verdade organizam a observabilidade.

As variáveis chegam à aplicação do mesmo jeito que o `--env-file` fazia localmente. O `os.getenv("API_KEY")` do `auth/seguranca.py` continua lendo do ambiente, sem nenhuma alteração de código.

> O `load_dotenv()` do `main.py` não encontra arquivo `.env` nenhum no servidor — e isso não é problema. Ele simplesmente não carrega nada e segue adiante, porque as variáveis já estão no ambiente.

## 3.4 Publicando e testando

Clique em **Create Web Service**. O Render clona o repositório, roda o build e sobe a aplicação. Acompanhe pela aba **Logs**: é lá que aparece um pacote faltando no `requirements.txt` ou um erro de import.

Ao final, a API responde em:

```
https://forzy-api.onrender.com
```

Teste antes de mexer no front:

```bash
# 1. A rota raiz não exige chave
curl https://forzy-api.onrender.com/
# Esperado: {"status":"ok","servico":"Forzy Digital Twin API"}

# 2. Sem a chave, os endpoints recusam
curl -i https://forzy-api.onrender.com/v1/equipamentos
# Esperado: HTTP/2 403 (ou 401)

# 3. Com a chave, respondem
curl -H "X-API-Key: uma-chave-forte-de-producao" \
     https://forzy-api.onrender.com/v1/equipamentos/tags
# Esperado: ["MTR-001","MTR-002",...]
```

Pelo navegador, `https://forzy-api.onrender.com/docs` abre o Swagger. Clique em **Authorize**, cole a chave de produção e teste `GET /v1/sensores/MTR-001/leitura-atual`.

**Só avance quando esses três testes passarem.** Depurar front e back ao mesmo tempo, sem saber de que lado está o problema, é a forma mais lenta de trabalhar.

> **A primeira chamada pode demorar.** Se o serviço estiver hibernado, o `curl` pode levar quase um minuto para responder. Isso é esperado e está explicado na seção 7.

---

# 4. Parte 2 — A Mesma API no Render, com Docker

Agora publique a **mesma aplicação, do mesmo repositório**, num segundo serviço — desta vez usando o Dockerfile da Aula 19. Os dois vão conviver, e comparar os dois é o objetivo.

## 4.1 O Dockerfile precisa aprender sobre `$PORT`

Há um ajuste obrigatório. O Dockerfile da aula passada termina assim:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

A porta está fixa em 8000. Na sua máquina isso funciona, porque você escolhe as portas. No Render, a porta é escolhida pela plataforma — e o container vai subir, parecer saudável nos logs e nunca receber uma requisição.

A correção parece pequena, mas passa por um conceito do Docker que vale entender.

```dockerfile
# Porta padrão para uso local; a plataforma sobrescreve quando quiser outra
ENV PORT=8000

# Forma shell (sh -c): necessária para que ${PORT} seja expandido.
# O `exec` faz o uvicorn substituir o shell e virar o processo principal,
# de modo que ele receba o sinal de encerramento quando a plataforma o desligar.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
```

**Por que a forma shell.** O `CMD` em formato de lista JSON é a *forma exec*: o Docker executa o programa diretamente, sem passar por um interpretador de comandos. Como não há shell, **não há quem expanda `${PORT}`** — a string `${PORT}` chegaria literalmente ao uvicorn, que reclamaria de um número de porta inválido. Escrever `CMD ["sh", "-c", "..."]` coloca um shell no caminho, e aí a variável é resolvida.

**Por que o `exec`.** Sem ele, o `sh` fica sendo o processo número 1 do container e o uvicorn vira filho dele. Quando a plataforma manda o container parar, o sinal chega ao `sh`, que não o repassa, e o uvicorn é morto à força alguns segundos depois, no meio do que estivesse fazendo. O `exec` faz o uvicorn **substituir** o shell, assumindo o lugar dele — então o sinal chega direto a quem precisa tratá-lo.

O `HEALTHCHECK` tem o mesmo problema de porta fixa, e a correção é a mesma ideia:

```dockerfile
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ['PORT'] + '/')" || exit 1
```

Nada disso quebra o uso local: como o `ENV PORT=8000` define o padrão, `docker compose up` e `docker run -p 8000:8000` continuam funcionando exatamente como antes.

## 4.2 Criando o segundo serviço

No Render, **New → Web Service**, mesmo repositório, e agora:

```
Name:              forzy-api-docker
Language:          Docker
Branch:            main
Root Directory:    backend
Dockerfile Path:   ./backend/Dockerfile
Instance Type:     Free
Health Check Path: /
```

Repare no que **desapareceu** da tela: não há Build Command, não há Start Command, não há arquivo de versão do Python. Todas essas informações já estão dentro do Dockerfile. A plataforma não precisa perguntar nada — ela só constrói a imagem e a executa.

Cadastre as mesmas variáveis de ambiente da seção 4.3 e publique.

Acompanhe os logs de build: você vai ver exatamente as mesmas etapas do `docker build` local, uma para cada instrução do Dockerfile. É a mesma imagem que roda na sua máquina, construída num servidor.

Teste com os mesmos três comandos `curl`, trocando a URL para `https://forzy-api-docker.onrender.com`. O resultado deve ser idêntico ao do serviço sem Docker — porque é a mesma aplicação.

---

# 5. O Que os Dois Modos Ensinam

Você tem agora duas URLs que servem a mesma API. A diferença não está no que elas fazem, e sim em **quem decidiu cada coisa**.

| Decisão | Sem Docker | Com Docker |
|---|---|---|
| Sistema operacional | A plataforma escolhe | Você escolhe (`FROM`) |
| Versão do Python | `.python-version`, dentro do que a plataforma oferece | Você escolhe, qualquer uma |
| Bibliotecas de sistema | O que a plataforma já tiver | Você instala (`RUN apt-get ...`) |
| Instalação das dependências | Build Command, na plataforma | `RUN pip install`, no Dockerfile |
| Comando de inicialização | Start Command, na plataforma | `CMD`, no Dockerfile |
| Usuário que executa | Definido pela plataforma | Você define (`USER forzy`) |
| Verificação de saúde | Health Check Path, na plataforma | `HEALTHCHECK` + a plataforma |
| Roda igual na sua máquina? | Não — é a configuração do painel | **Sim — é a mesma imagem** |
| Trocar de provedor | Reconfigurar tudo no painel novo | Apontar para o mesmo Dockerfile |

Leia a tabela de baixo para cima e a conclusão aparece sozinha.

**Sem Docker, a configuração da sua aplicação mora no painel de um fornecedor.** Ela não está no Git, ninguém revisa em pull request, e quem for reproduzir o ambiente precisa de acesso àquela conta. Se a plataforma sumir, a configuração some junto.

**Com Docker, ela mora no repositório.** Versionada, revisável, e igual em qualquer lugar que aceite containers.

Em troca, o Docker cobra: mais um arquivo para manter, builds mais lentos, e um conceito a mais para aprender. Para um projeto pequeno e estável, o runtime nativo é perfeitamente adequado e mais simples. É uma escolha de engenharia, não uma questão de certo e errado.

> **O critério prático:** quanto mais o seu ambiente se afasta de "Python e algumas bibliotecas" — uma versão específica de uma biblioteca de sistema, um binário externo, um processo auxiliar —, mais o Dockerfile deixa de ser luxo e vira necessidade.

---

# 6. O Preço do Gratuito

O serviço está no ar e não custa nada. Em troca, três coisas passam a ser verdade. Entendê-las importa mais do que o deploy em si.

## 6.1 O disco é efêmero

Lembra do experimento da aula anterior, em que o motor cadastrado sumia quando o container era removido e recriado? **No plano gratuito do Render isso acontece sozinho.** O sistema de arquivos é efêmero: a cada novo deploy, a cada reinício e a cada saída da hibernação, a aplicação recomeça do zero, com o `motor.db` que veio do repositório.

Não é um defeito da plataforma, é o modelo dela. Um container de nuvem é descartável por definição, e nesse modelo o banco tem que morar fora dele.

O que um sistema real faria:

- **Disco persistente**: o Render oferece discos anexáveis, mas só em planos pagos.
- **Banco gerenciado externo**: o SQLite dá lugar a um Postgres hospedado, que roda como serviço separado e sobrevive a qualquer coisa que aconteça com a aplicação. O Render oferece um Postgres gratuito, com validade limitada.
- **Servidor próprio com volume**, que é o caminho da próxima aula, na AWS.

## 6.2 A aplicação hiberna — e isso quebra o front

O Render pausa um serviço gratuito depois de **15 minutos sem receber requisições**. O próximo acesso não dá erro: ele **acorda** o serviço, e isso leva de **30 a 50 segundos**, porque a aplicação precisa subir do zero.

Esse número tem uma consequência séria, e ela não é óbvia: **o timeout de 15 segundos do `api_provider` é menor que o tempo de acordar.** Ou seja, a primeira visita do dia ao front publicado vai falhar. Sempre. O usuário vê uma tela vazia e uma mensagem de erro de conexão, embora não haja nada errado.

A correção é tratar a primeira chamada como um caso à parte:

```python
# providers/api_provider.py
_TIMEOUT = 15          # chamadas normais, com o serviço já de pé
_TIMEOUT_ACORDAR = 75  # primeira chamada: a plataforma pode estar hibernada


def acordar_api() -> bool:
    """
    Tira a API da hibernação antes da primeira tela.

    Roda uma única vez por sessão, contra a rota `/` (que não exige chave),
    com um tempo de espera bem maior. As chamadas seguintes usam o timeout
    normal, porque a partir daí o serviço já está de pé.
    """
    if st.session_state.get("_api_acordada"):
        return True
    try:
        requests.get(f"{API_URL}/", timeout=_TIMEOUT_ACORDAR)
        st.session_state["_api_acordada"] = True
        return True
    except requests.RequestException:
        return False
```

E no `app.py`, antes de desenhar qualquer tela:

```python
if not st.session_state.get("_api_acordada"):
    with st.spinner("Acordando a API… (o plano gratuito hiberna após alguns minutos sem acesso)"):
        api_provider.acordar_api()
```

O ganho não é só técnico. Com o `st.spinner`, o usuário **vê** o custo do tier gratuito, em vez de encarar um erro sem explicação. Comunicar uma limitação conhecida é diferente de falhar.

## 6.3 Você não controla a rede

Sem IP fixo, sem regra de firewall, sem escolher região, sem decidir quem acessa o quê. O Render hospeda nos Estados Unidos; o Streamlit Cloud também.

Para uma demonstração isso é irrelevante. Para um sistema que lê dados proprietários de uma planta industrial, é exatamente o tipo de coisa que o cliente exige controlar — e é o motivo da próxima aula ser sobre AWS.

---

# 7. O Front Precisa de Três Mudanças

Independentemente da plataforma escolhida, sair do `localhost` exige três ajustes. Eles são os mesmos nos dois caminhos.

**O endereço da API.** Localmente era `http://localhost:8000` (ou `http://backend:8000` dentro do compose). Agora é a URL pública, em HTTPS e sem porta:

```
API_URL = https://forzy-api.onrender.com
```

**A chave precisa ser idêntica dos dois lados.** A `API_KEY` da API e a do front têm que ter **exatamente** o mesmo valor. Um espaço a mais, uma aspa copiada junto, e todas as chamadas voltam `401`. Esse é, com folga, o erro mais comum do primeiro deploy — e o mais difícil de enxergar, porque espaço em branco é invisível. Por isso o `api_provider` se defende na origem:

```python
# .strip() protege contra espaço ou tabulação no fim da linha do .env.
# rstrip("/") evita que uma barra no fim da URL gere caminhos como //v1/plantas.
API_URL = _config("API_URL", "http://localhost:8000").strip().rstrip("/")
API_KEY = _config("API_KEY", "chave-local-dev").strip()
```

---

# 8. Parte 3A — O Front Streamlit no Streamlit Community Cloud

Este é o caminho para a versão Streamlit do Forzy (pasta `frontend-streamlit/`).

## 8.1 O que mudou do Gradio para o Streamlit

**No Gradio**, você monta a interface uma vez e registra eventos. Quando o usuário clica num botão, só a função daquele evento roda, e só os componentes listados em `outputs` são atualizados. O resto da tela nem é tocado.

**No Streamlit**, não existem eventos. Qualquer interação — um clique, uma escolha num seletor, uma tecla num campo — reexecuta **o script inteiro**, de cima para baixo, e redesenha a tela do zero. O `st.button()` não recebe uma função: ele devolve `True` no exato rerun em que foi clicado.

## 8.2 `st.secrets` — o `.env` da nuvem

O Streamlit Cloud não tem arquivo `.env`. Ele injeta as configurações por um mecanismo próprio, o `st.secrets`, que lê um arquivo TOML.

Localmente, esse arquivo fica em `.streamlit/secrets.toml` (e **nunca** vai para o Git). Na nuvem, o mesmo conteúdo é colado no painel.

```toml
# .streamlit/secrets.toml — nunca commitar
API_URL = "https://forzy-api.onrender.com"
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

## 8.3 Rodando localmente antes de publicar

Não publique sem rodar. Na pasta `frontend-streamlit/`:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`. Aponte-o para a API publicada (não para o `localhost:8000`), assim você testa exatamente a configuração que vai para a nuvem:

```bash
# frontend-streamlit/.env
API_URL=https://forzy-api.onrender.com
API_KEY=uma-chave-forte-de-producao
APP_VERSION=2.0.0-streamlit
```

Percorra as quatro telas. Se tudo funcionar aqui, o deploy é quase burocracia.

## 8.4 O `requirements.txt`

```text
streamlit==1.49.0
pandas==2.3.3
plotly==7.1.0
requests==2.34.2
python-dotenv==1.2.3
```

> **Onde colocar o arquivo:** o Streamlit Cloud procura o `requirements.txt` na mesma pasta do arquivo principal ou na raiz do repositório. Com o front numa subpasta, mantenha o arquivo **dentro dela**, ao lado do `app.py`.

## 8.5 Publicando

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

6. Antes de confirmar, abra **Advanced settings → Secrets** e cole o conteúdo do seu `secrets.toml`.
7. Clique em **Deploy**.

A primeira publicação leva alguns minutos: a plataforma cria o ambiente, instala as dependências e inicia o app. Os logs aparecem na própria tela — é lá que você descobre um pacote faltando no `requirements.txt`.

Ao final, o app responde em `https://forzy-digital-twin.streamlit.app`.

## 8.6 Atualizações automáticas

O Streamlit Cloud observa o repositório: **cada push na branch publicada reimplanta o app**. Não existe botão de "publicar de novo" — o `git push` é o deploy. O Render funciona da mesma forma.

Os segredos são a exceção, e é importante entender por quê: eles ficam na plataforma, não no repositório. Mudar um segredo é feito no painel, e o serviço reinicia em seguida.

---

# 9. Parte 3B — O Front Gradio no Hugging Face Spaces

Este é o caminho para quem mantém a versão Gradio do Forzy. O SDK `gradio` **continua gratuito** — só o SDK Docker passou a exigir plano pago.

## 9.1 Criando o Space

1. Crie uma conta gratuita em [huggingface.co](https://huggingface.co).
2. No menu do seu perfil, escolha **New Space**.
3. Preencha:

```
Space name:  forzy-app
License:     mit
SDK:         Gradio
Hardware:    CPU basic (gratuito)
Visibility:  Public
```

Com o SDK `gradio`, o Hugging Face instala o `requirements.txt` e executa o `app.py` sozinho — nenhum Dockerfile é necessário.

## 9.2 O `README.md` do Space

Um Space é configurado por um bloco YAML no topo do `README.md`. Sem esse bloco, o deploy falha.

```markdown
---
title: Forzy Digital Twin
emoji: ⚙️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.28.0
app_file: app.py
pinned: false
---

# Forzy · Digital Twin

Interface de monitoramento de motores industriais.
Consome a API publicada em `forzy-api.onrender.com`.
```

**`sdk_version`** deve bater com a versão do Gradio que você testou localmente. Deixar a plataforma escolher a mais recente é pedir para o app quebrar num dia qualquer, por uma mudança de API de algum componente.

## 9.3 O que ajustar no código

**Segredos.** O Hugging Face injeta variáveis de ambiente, exatamente como o `--env-file` fazia. Nenhuma alteração de código é necessária. Em Settings → Variables and secrets:

```
Secret    API_KEY      = uma-chave-forte-de-producao   (a mesma da API)
Variable  API_URL      = https://forzy-api.onrender.com
Variable  APP_VERSION  = 1.4.0
```

A plataforma separa **Variable** (visível para qualquer um que abra o Space) de **Secret** (só para o processo em execução). Chave vai em Secret; o resto pode ser Variable.

**O `launch()`.** O seu `app.py` termina com:

```python
app.launch(share=False, inbrowser=True)
```

O `inbrowser=True` tenta abrir um navegador na máquina onde o processo roda — o que num servidor não faz sentido. Troque por:

```python
app.launch()
```

Sem argumentos, o Gradio respeita as variáveis `GRADIO_SERVER_NAME` e `GRADIO_SERVER_PORT` que o Hugging Face já define. É a mesma lição da aula anterior: valores fixos no código vencem as variáveis de ambiente.

**Tempo de espera e despertar.** Aplique a mesma lógica da seção 7.2. No Gradio não há `st.session_state`, então use uma variável de módulo:

```python
# frontend/providers/api_provider.py
_TIMEOUT = 15
_TIMEOUT_ACORDAR = 75
_acordada = False


def acordar_api() -> bool:
    """Tira a API da hibernação. Chamada uma vez, antes de app.launch()."""
    global _acordada
    if _acordada:
        return True
    try:
        requests.get(f"{API_URL}/", timeout=_TIMEOUT_ACORDAR)
        _acordada = True
        return True
    except requests.RequestException:
        return False
```

```python
# frontend/app.py — antes de montar a interface
import providers.api_provider as api_provider
api_provider.acordar_api()
```

## 9.4 Publicando

Um Space é um repositório Git:

```bash
git clone https://huggingface.co/spaces/seu-usuario/forzy-app
cd forzy-app
# copie o conteúdo de frontend/ (sem o .env)
git add .
git commit -m "deploy do front Gradio"
git push
```

Na primeira vez, o Hugging Face pede autenticação. A senha **não** é a da sua conta: é um **Access Token** com permissão de escrita, gerado em Settings → Access Tokens.

O app responde em `https://seu-usuario-forzy-app.hf.space`.

---

# 10. E o CORS? E o HTTPS?

Duas perguntas que sempre aparecem no primeiro deploy.

## 10.1 O CORS continua não se aplicando

O `main.py` do Forzy libera a origem `http://localhost:7860`. Agora o front está em `streamlit.app` ou em `hf.space`. A API vai recusar?

Não. Pelo mesmo motivo da aula anterior: **quem chama a API é o servidor do front, não o navegador do usuário.** O `requests` roda dentro do processo Python do Streamlit ou do Gradio, e o CORS é uma regra que o navegador aplica a chamadas feitas por JavaScript numa página.

```
Navegador do usuário
    │  (abre a página)
    ▼
Servidor do front (Streamlit Cloud / HF Spaces)
    │  requests.get(...)  ← servidor → servidor: o CORS não entra aqui
    ▼
API FastAPI (Render)
```

Então por que manter a configuração de CORS? Porque ela vai passar a valer no dia em que um cliente chamar a API **de dentro do navegador ou de um app** — que é exatamente o que acontece na aula de mobile. Guarde a lista `allow_origins`: ela vai precisar ser atualizada lá.

## 10.2 HTTPS sem esforço

As duas plataformas entregam HTTPS pronto, com certificado válido e renovado automaticamente. Você não gerou certificado, não configurou nada, não pagou nada.

Registre isso como um privilégio do "grátis", porque ele acaba na próxima aula: numa máquina EC2, o HTTPS é problema seu, e resolvê-lo dá trabalho. E não é detalhe estético — sem HTTPS, um app mobile moderno se recusa a chamar a API.

---

# 11. Observabilidade Depois do Deploy

Aqui as aulas de observabilidade se pagam. Você não precisa adivinhar como o Forzy se comporta no ar: você consegue ver.

Abra o LangSmith no projeto `forzy-producao`, use o app publicado por alguns minutos e observe o que chega.

**O cliente aparece sozinho.** O header `X-Client-Platform` identifica de onde veio cada chamada. A versão Streamlit envia `streamlit-cloud`; a Gradio, `gradio-desktop`. Filtrando por `metadata.client_platform`, você compara o comportamento dos dois fronts — que consomem a **mesma** API, com os **mesmos** endpoints.

**Os dois deploys da API podem ser comparados.** Você tem dois serviços, um com Docker e outro sem, servindo a mesma aplicação. Aponte o front para um, use, aponte para o outro, use de novo, e compare as latências. Eles deveriam ser equivalentes — e se não forem, a diferença está no ambiente, não no código. É o tipo de medição que normalmente ninguém consegue fazer.

**A latência real fica visível.** Compare a duração dos traces locais com os de produção. A diferença é a soma de: rede pública, a máquina modesta do tier gratuito e, na primeira chamada após hibernação, o tempo de subir a aplicação. É a primeira vez no curso que você mede o custo do ambiente, e não do código.

**A sessão vira uma linha do tempo.** Filtrando por `metadata.session_id`, você reconstrói tudo o que um usuário fez, em ordem. Quando alguém disser "o dashboard travou", isso deixa de ser um relato e vira um trace.

**A versão distingue um deploy do outro.** Mude `APP_VERSION`, publique e compare latência e taxa de erro entre as duas versões. É o começo de uma prática que times usam a sério: nenhum deploy é considerado bom porque "subiu" — ele é avaliado pelos números depois de subir.

> **A ideia para levar:** deploy sem observabilidade é deploy às cegas. O header `X-App-Version`, que na aula de instrumentação parecia um detalhe, agora é o que separa "a versão nova está no ar" de "a versão nova está melhor".

---

# 12. Apêndice — FastAPI num Space Gradio, sem Docker

Para quem quiser manter tudo no Hugging Face mesmo, existe um caminho.

Um Space com `sdk: gradio` simplesmente executa `python app.py` e espera que **alguma coisa** escute na porta 7860. Ele não verifica se o que está rodando é Gradio de fato. Então dá para colocar ali um FastAPI puro:

```python
# app.py na raiz do Space
import os
import uvicorn

from main import app  # o mesmo app FastAPI do Forzy

if __name__ == "__main__":
    # Dentro de um Space a variável SPACE_ID existe e a porta obrigatória é 7860.
    porta = 7860 if os.getenv("SPACE_ID") else 8000
    uvicorn.run(app, host="0.0.0.0", port=porta)
```

Funciona, e há projetos reais usando isso. Mas leia a advertência com atenção:

**Isto depende de um comportamento não documentado.** O Hugging Face não promete que um Space Gradio aceite qualquer processo — ele apenas não impede hoje. É exatamente o tipo de brecha que uma plataforma fecha quando quer, do mesmo jeito que fechou o SDK Docker, sem aviso.

Use como curiosidade e como exercício de entender o que uma plataforma realmente executa por baixo. **Não use como caminho principal de um trabalho avaliado**, e muito menos de um sistema que outra pessoa dependa.

---

# 13. Roteiro de Verificação

1. `https://forzy-api.onrender.com/` responde `{"status": "ok", ...}`.
2. `/docs` abre e, com a chave de produção, `GET /v1/equipamentos` devolve os motores.
3. Sem a chave, o mesmo endpoint recusa a requisição.
4. `https://forzy-api-docker.onrender.com/` responde exatamente o mesmo.
5. O front publicado abre e a lista de equipamentos carrega.
6. Com a API hibernada, o front mostra "Acordando a API…" e carrega em seguida, em vez de dar erro.
7. Selecionar uma linha e clicar em "Ver Dados de Sensores" leva à tela de sensores com a TAG já escolhida.
8. O Dashboard navega Planta → Área → Equipamento e desenha o gráfico.
9. O cadastro de um motor novo retorna sucesso e aparece na lista.
10. Após um novo deploy, o motor cadastrado sumiu — comportamento esperado, e você sabe explicá-lo.
11. No LangSmith, `forzy-producao` recebe traces com `client_platform`, `feature`, `session_id` e `app_version` preenchidos.
12. Nenhum `.env`, `secrets.toml` ou chave aparece no repositório do GitHub.
13. Abra os links no celular. Tudo funciona, porque é HTTPS e é web.

---

# 14. Problemas Comuns

| Sintoma | Causa provável | Como resolver |
|---|---|---|
| Serviço sobe no Render mas nunca responde | Porta fixa no código em vez de `$PORT` | Start Command com `--port $PORT`; no Docker, forma shell com `${PORT}` |
| Container Docker no Render passa a porta literal `${PORT}` para o uvicorn | `CMD` em forma exec não expande variáveis | Usar `CMD ["sh", "-c", "exec uvicorn ... --port ${PORT}"]` |
| Build falha com `ModuleNotFoundError` | Biblioteca ausente do `requirements.txt` | Adicionar e fazer push |
| Build falha por sintaxe de tipos (`dict \| None`) | Versão do Python escolhida pela plataforma é antiga | Criar `backend/.python-version` com a versão testada |
| Render não encontra o `requirements.txt` | `Root Directory` vazio | Preencher com `backend` |
| Todas as chamadas voltam `401` | `API_KEY` diferente entre a API e o front | Conferir os dois valores; atenção a espaços invisíveis no fim |
| Primeira visita do dia sempre falha | Timeout menor que o tempo de acordar | Implementar `acordar_api()` com timeout de 75 s |
| App fica lento a cada clique | Sem cache, refazendo todas as chamadas a cada rerun | Conferir os decoradores `@st.cache_data` |
| Salvou um motor mas a lista não mudou | Cache servindo a resposta antiga | Chamar `api_provider.limpar_cache()` depois de toda escrita |
| Streamlit Cloud não encontra o app | `Main file path` incorreto | Caminho a partir da raiz: `frontend-streamlit/app.py` |
| `st.secrets` não encontra a chave | Segredos não salvos, ou TOML mal formatado | Conferir no painel: valores entre aspas, um por linha |
| Motor cadastrado sumiu | Disco efêmero do plano gratuito | Comportamento esperado; ver a seção 7.1 |
| Traces não chegam ao LangSmith | `LANGSMITH_*` não configuradas no painel | Conferir e reiniciar o serviço |
| Não consegue criar Space com SDK Docker | Mudança de julho de 2026 | Usar o Render; ver a seção 1 |

---

# Referências

- [Render — Free instance types](https://render.com/docs/free)
- [Render — Deploy a FastAPI app](https://render.com/docs/deploy-fastapi)
- [Render — Docker on Render](https://render.com/docs/docker)
- [Render — Environment variables](https://render.com/docs/configure-environment-variables)
- [Streamlit Community Cloud — Documentação](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Streamlit Community Cloud — Status e limitações](https://docs.streamlit.io/deploy/streamlit-community-cloud/status)
- [Streamlit — Segredos (`st.secrets`)](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [Streamlit — Cache de dados (`st.cache_data`)](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [Streamlit — Modelo de execução (rerun)](https://docs.streamlit.io/develop/concepts/architecture/run-your-app)
- [Hugging Face Spaces — Gradio](https://huggingface.co/docs/hub/spaces-sdks-gradio)
- [Hugging Face Spaces — Configuração pelo README](https://huggingface.co/docs/hub/spaces-config-reference)
- [Hugging Face Forums — Docker SDK now marked as "Paid"](https://discuss.huggingface.co/t/docker-sdk-now-marked-as-paid-when-creating-a-new-space/177580)
- [Docker — Dockerfile: diferença entre forma exec e forma shell](https://docs.docker.com/reference/dockerfile/#shell-and-exec-form)
- [FastAPI — Deploy com Docker](https://fastapi.tiangolo.com/deployment/docker/)
