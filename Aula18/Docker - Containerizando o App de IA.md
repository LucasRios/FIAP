# Aula 19 — Docker: Containerizando a API

Neste ponto o Forzy já está dividido em dois processos independentes:

```
frontend/ (Gradio, porta 7860)
   └─ providers/api_provider.py ──[HTTP + X-API-Key]──▶ backend/ (FastAPI, porta 8000)
                                                           ├─ routers/ (equipamentos, plantas, sensores)
                                                           ├─ providers/ (SQLite e hierarquia da planta)
                                                           ├─ motor.db  (tabelas motores e leituras)
                                                           └─ LangSmith (traces de cada request)
```

Para rodar isso hoje, você precisa de: Python instalado na versão certa, dois ambientes virtuais (ou um só, com tudo misturado), dois `pip install`, dois arquivos `.env` preenchidos, dois terminais abertos e a ordem correta de inicialização (primeiro o back, depois o front). Qualquer diferença em qualquer um desses itens quebra o projeto.

É exatamente esse conjunto de passos frágeis que o Docker transforma em um único comando.

---

# 1. O Problema que o Docker Resolve

Imagine a seguinte situação, bem realista: seu grupo termina o Forzy e manda o repositório para o avaliador. Na máquina dele acontece uma destas coisas:

- O Python instalado é o 3.9. O código usa `list[dict]` e `dict | None` em anotações de tipo — sintaxe que exige Python 3.10 ou superior. O back-end nem importa.
- O `requirements.txt` do front diz `gradio>=4.44.0`. O `pip` instala a versão mais recente disponível naquele dia, que mudou o nome de um parâmetro de componente. Uma página do Forzy quebra.
- Ele esquece de criar o `backend/.env`. O `API_KEY` cai no valor padrão `chave-local-dev`, o front manda outra chave, e todas as chamadas voltam `401 Unauthorized`. A tela de equipamentos aparece vazia e ninguém entende por quê.
- Ele sobe o front antes do back. O Gradio abre, tenta listar motores, não encontra a API e mostra a mensagem de erro de conexão.

Nenhum desses problemas é um bug do código do Forzy. São todos problemas de **ambiente**: a diferença entre a máquina onde o código foi escrito e a máquina onde ele está rodando. É o famoso "na minha máquina funciona".

O Docker resolve isso de um jeito direto: em vez de entregar só o código e torcer para o ambiente do outro lado estar certo, você entrega **o código junto com o ambiente**. A versão do Python, as bibliotecas com as versões exatas, os arquivos, a porta, o comando de inicialização — tudo vai empacotado numa unidade chamada **container**, que roda da mesma forma no seu notebook, no computador do avaliador, no Hugging Face ou num servidor da AWS.

### Por que isso é assunto de quem faz front-end de IA

A pergunta aparece sempre: "Docker não é coisa de DevOps?". Três motivos para ser assunto seu também:

**Deploy.** Praticamente toda plataforma de nuvem moderna aceita containers como formato de entrega: Hugging Face Spaces (modo Docker), AWS EC2, AWS ECS/Fargate, Google Cloud Run, Render, Railway. Quando você aprende a escrever um Dockerfile, aprende o "formato de arquivo" que todas elas entendem. É exatamente o que vamos usar para colocar a API do Forzy no ar.

**Portfólio.** Um avaliador ou recrutador que clona seu repositório e sobe o projeto com `docker compose up`, sem instalar nada além do Docker, tem uma impressão muito diferente de quem precisa seguir um README de vinte passos.

**Trabalho em time.** Em empresas, o time de back-end quase sempre entrega serviços em containers. Saber ler um Dockerfile e subir um `docker compose` local elimina muita dependência de outras pessoas no dia a dia.

---

# 2. Docker Explicado a Partir do que Você Já Conhece

Você já resolve uma versão menor desse problema toda vez que cria um ambiente virtual:

```bash
python -m venv .venv
pip install -r requirements.txt
```

O `venv` isola as **bibliotecas Python** do projeto. O `requirements.txt` descreve quais bibliotecas instalar. Isso já evita muita dor de cabeça — mas para por aí. O `venv` não controla:

- qual versão do Python está instalada na máquina;
- qual sistema operacional está rodando (Windows, macOS, Linux);
- bibliotecas de sistema que alguns pacotes Python usam por baixo;
- em qual porta o app sobe e com qual comando;
- quais variáveis de ambiente precisam existir.

O Docker leva a mesma ideia um nível acima. A analogia que vamos usar a aula inteira:

> **O `requirements.txt` descreve as bibliotecas do projeto. O `Dockerfile` descreve a máquina inteira onde o projeto roda.**

| | Ambiente virtual (`venv`) | Container Docker |
|---|---|---|
| O que isola | Bibliotecas Python | Python + bibliotecas + sistema de arquivos + processo + rede |
| Arquivo que descreve | `requirements.txt` | `Dockerfile` |
| Versão do Python | A que estiver instalada na máquina | A que você escolher no Dockerfile |
| Sistema operacional | O da máquina | Um Linux mínimo, igual em qualquer lugar |
| Comando de inicialização | Você lembra e digita | Fica gravado na imagem |
| Portabilidade | Só funciona se a máquina tiver o Python certo | Funciona em qualquer máquina com Docker |

### Container não é máquina virtual

Uma confusão comum: achar que o container é uma máquina virtual, como as do VirtualBox. Não é. Uma máquina virtual simula um computador inteiro, com sistema operacional completo, e costuma pesar gigabytes e levar minutos para ligar. Um container é só um **processo isolado** rodando sobre o sistema operacional da máquina hospedeira: ele tem a própria "visão" de arquivos, rede e processos, mas compartilha o núcleo do sistema. Por isso sobe em segundos e ocupa bem menos espaço.

Para o nosso uso, pense assim: o container do back-end do Forzy é o `uvicorn main:app` rodando dentro de uma caixa fechada, que tem dentro dela exatamente o Python e as bibliotecas de que ele precisa — e nada mais.

---

# 3. Os Quatro Conceitos que Você Precisa

## 3.1 Imagem

A **imagem** é um pacote pronto e somente leitura com tudo que o app precisa: um Linux mínimo, o Python, as bibliotecas instaladas e o código do projeto. É um molde: você constrói uma vez e usa quantas vezes quiser.

No Forzy teremos duas imagens: `forzy-backend` e `forzy-frontend`.

## 3.2 Container

O **container** é uma imagem em execução. Se a imagem é o molde, o container é a peça produzida por ele. Da mesma imagem `forzy-backend` você pode criar vários containers, e cada um roda de forma independente.

Um detalhe que vai ser muito importante na seção sobre o banco de dados: a imagem é somente leitura, mas o container ganha uma **camada gravável** por cima dela. Tudo que o app escreve em disco enquanto roda — por exemplo, um motor novo cadastrado no `motor.db` — vai para essa camada. Quando o container é apagado, essa camada vai junto.

## 3.3 Dockerfile

O **Dockerfile** é a receita, em texto, que diz como construir a imagem: "comece com Python 3.11, copie o `requirements.txt`, instale as dependências, copie o código, e quando alguém iniciar um container, rode `uvicorn`". É o arquivo que você escreve e versiona no Git.

## 3.4 docker compose

O **docker compose** é uma ferramenta que sobe **vários containers juntos**, descritos em um único arquivo (`docker-compose.yml`). O Forzy tem dois serviços que precisam conversar entre si — o front precisa encontrar o back — e o compose cuida disso: cria uma rede entre eles, define a ordem de inicialização e aplica as variáveis de ambiente de cada um.

## 3.5 Resumo visual

```
Dockerfile ──(docker build)──▶ Imagem ──(docker run)──▶ Container
  receita                      molde                     processo rodando
  (texto, no Git)              (pacote pronto)           (com camada gravável)

docker-compose.yml ──(docker compose up)──▶ vários containers + rede entre eles
```

---

# 4. Instalando o Docker

## Windows

1. Acesse [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) e baixe o **Docker Desktop para Windows**.
2. Durante a instalação, mantenha marcada a opção de usar o **WSL 2** (o subsistema Linux do Windows). Se o instalador pedir para instalar ou atualizar o WSL, aceite e reinicie o computador.
3. Abra o Docker Desktop e espere o indicador no canto inferior esquerdo ficar verde ("Engine running").


## Verificando a instalação

Abra o terminal do VS Code e rode:

```bash
docker --version
docker compose version
docker run hello-world
```

O último comando baixa uma imagem minúscula de teste e cria um container a partir dela. Se aparecer a mensagem "Hello from Docker!", está tudo funcionando.

---

# 5. Preparando o Forzy para o Container

Antes de escrever qualquer Dockerfile, vamos organizar o projeto. A estrutura final fica assim:

```
forzy/
├── docker-compose.yml            ← NOVO — sobe back e front juntos
├── .gitignore
├── backend/
│   ├── Dockerfile                ← NOVO
│   ├── .dockerignore             ← NOVO
│   ├── .env                      ← nunca commitar
│   ├── .env.example              ← NOVO — modelo das variáveis, este sim vai para o Git
│   ├── requirements.txt
│   ├── main.py
│   ├── motor.db
│   ├── auth/
│   ├── models/
│   ├── providers/
│   └── routers/
└── frontend/
    ├── Dockerfile                ← NOVO
    ├── .dockerignore             ← NOVO
    ├── .env                      ← nunca commitar
    ├── .env.example              ← NOVO
    ├── requirements.txt
    ├── app.py
    ├── ui/
    ├── state/
    ├── features/
    ├── pipelines/
    └── providers/
```

Repare que **nenhum arquivo de código do Forzy muda nesta aula**. Os routers, os providers, as pipelines e as páginas continuam exatamente como estão. O Docker é uma camada de empacotamento: ele se encaixa em volta do projeto, não dentro dele.

## 5.1 `requirements.txt` — por que fixar versões agora faz diferença

Até aqui usamos versões mínimas (`fastapi>=0.110.0`). Isso significa "qualquer versão a partir desta". Na prática, cada `pip install` pode trazer uma versão diferente, dependendo do dia. Como o objetivo do Docker é justamente ter um ambiente reproduzível, o ideal é **fixar as versões exatas** que você testou.

O jeito mais simples: com o seu `venv` ativado e o projeto funcionando, rode dentro de cada pasta:

```bash
pip freeze > requirements.lock.txt
```

Abra o arquivo gerado, copie para o `requirements.txt` apenas as bibliotecas que o projeto usa diretamente, trocando `>=` por `==` com a versão que apareceu. Para esta aula, as dependências são:

```text
# backend/requirements.txt
fastapi==0.141.1
uvicorn[standard]==0.53.0
pydantic==2.13.5
python-dotenv==1.2.3
langsmith==0.14.0
```

```text
# frontend/requirements.txt
gradio==6.28.0
plotly==7.1.0
requests==2.34.2
python-dotenv==1.2.3
```

> Se você preferir manter `>=` durante a aula, tudo funciona. Mas antes de entregar o projeto ou fazer deploy, fixe as versões — é isso que garante que a imagem construída daqui a três meses seja igual à de hoje.

## 5.2 `.env.example` — o modelo das variáveis

O `.env` nunca vai para o Git, porque contém segredos. Mas quem clona o repositório precisa saber **quais** variáveis criar. Para isso existe o `.env.example`: o mesmo arquivo, com os nomes das variáveis e valores fictícios. Ele vai para o Git.

```text
# backend/.env.example
API_KEY=troque-por-uma-chave-forte
LANGSMITH_API_KEY=sua-chave-do-langsmith
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=forzy-digital-twin
```

```text
# frontend/.env.example
API_URL=http://localhost:8000
API_KEY=troque-por-uma-chave-forte
APP_VERSION=1.3.0
```

Quem clona o projeto só precisa copiar e preencher:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

O `API_KEY` precisa ser **o mesmo valor** nos dois arquivos: o back-end usa para validar, o front-end usa para enviar no header `X-API-Key`.

## 5.3 `.dockerignore` — o que não entra na imagem

Quando você manda o Docker construir uma imagem, ele envia a pasta inteira para o processo de build. O `.dockerignore` funciona como um `.gitignore` para esse envio: lista o que deve ficar de fora.

Isso importa por dois motivos. O primeiro é **segurança**: o `.env`, com as chaves reais, jamais pode ir para dentro da imagem — quem tiver acesso à imagem conseguiria ler o arquivo. O segundo é **tamanho e velocidade**: não faz sentido copiar a pasta `.venv` (que pode ter centenas de megabytes) nem os arquivos `__pycache__`.

```text
# backend/.dockerignore
.env
*.env
.venv/
venv/
__pycache__/
*.pyc
*.log
.git
motor.db-journal
```

```text
# frontend/.dockerignore
.env
*.env
.venv/
venv/
__pycache__/
*.pyc
*.log
.git
```

Repare que o `motor.db` **não** está no `.dockerignore` do back-end. Queremos que ele entre na imagem como banco inicial, com os motores e as leituras já cadastrados. 

## 5.4 O detalhe que mais derruba gente: `localhost` dentro do container

Quando você roda `uvicorn main:app` na sua máquina, o servidor escuta em `127.0.0.1` (o famoso `localhost`) por padrão. Isso quer dizer: "aceito conexões vindas **desta mesma máquina**".

Dentro de um container, "esta mesma máquina" é o próprio container. Se o `uvicorn` escutar em `127.0.0.1` lá dentro, ele só aceita conexões que venham de dentro do container — e o seu navegador, que está fora, nunca consegue acessar. O sintoma é frustrante: o container está rodando, os logs não mostram erro, mas o navegador diz que não conseguiu conectar.

A solução é mandar o servidor escutar em `0.0.0.0`, que significa "aceito conexões vindas de qualquer interface de rede". Por isso você vai ver `--host 0.0.0.0` no comando do back-end e a variável `GRADIO_SERVER_NAME=0.0.0.0` no front-end.

> **Regra prática:** todo servidor que roda dentro de um container precisa escutar em `0.0.0.0`.

---

# 6. Dockerfile do Back-end

Crie o arquivo `backend/Dockerfile` (sem extensão) com o conteúdo abaixo. Em seguida, vamos entender cada bloco.

```dockerfile
# backend/Dockerfile — imagem da API FastAPI do Forzy

# 1. Imagem base: Linux mínimo com Python 3.12 já instalado
FROM python:3.12.10

# 2. Ajustes de comportamento do Python dentro do container
#    - PYTHONDONTWRITEBYTECODE: não gera arquivos .pyc (inúteis num container)
#    - PYTHONUNBUFFERED: envia os print() direto para os logs, sem atraso
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Usuário sem privilégios de administrador para rodar a aplicação
RUN useradd --create-home --uid 1000 forzy

# 4. Pasta de trabalho dentro do container
WORKDIR /app

# 5. Dependências primeiro — aproveita o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Código da aplicação (inclui o motor.db como banco inicial)
COPY --chown=forzy:forzy . .

# 7. O usuário forzy precisa poder escrever na pasta /app:
#    o SQLite cria arquivos temporários ao lado do motor.db durante as escritas
RUN chown forzy:forzy /app

# 8. A partir daqui, tudo roda como o usuário forzy
USER forzy

# 9. Documenta a porta em que a API escuta
EXPOSE 8000

# 10. Verificação de saúde: o Docker chama a rota "/" periodicamente
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# 11. Comando executado quando o container inicia
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 6.1 Entendendo cada instrução

**`FROM python:3.11-slim`** — Todo Dockerfile começa de uma imagem base. Aqui usamos a imagem oficial do Python 3.11 na variante `slim`, que é um Linux enxuto com Python pré-instalado. A variante completa (`python:3.11`) traz compiladores e ferramentas que o Forzy não usa e deixa a imagem bem maior. Este é o ponto em que resolvemos o problema do "Python 3.9 na máquina do avaliador": não importa o que ele tenha instalado, o container sempre roda Python 3.11.

**`ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`** — `ENV` define variáveis de ambiente que ficam gravadas na imagem. A primeira evita que o Python gere arquivos `.pyc`. A segunda é mais importante do que parece: por padrão, o Python guarda o que você imprime num buffer e só envia em blocos. Dentro de um container isso faz os `print()` do `api_provider` ou do `uvicorn` demorarem para aparecer nos logs — ou só aparecerem quando o container é parado. Com `PYTHONUNBUFFERED=1`, cada linha aparece na hora.

**`RUN useradd --create-home --uid 1000 forzy`** — `RUN` executa um comando durante a construção da imagem. Aqui criamos um usuário comum chamado `forzy`. Por padrão, tudo dentro de um container roda como `root`, o administrador do sistema. Se alguém encontrar uma falha na API e conseguir executar comandos, vai ter poderes de administrador dentro do container. Rodar como usuário comum limita esse estrago. Além disso, algumas plataformas de deploy (o Hugging Face Spaces, por exemplo) exigem exatamente um usuário com UID 1000 — então já deixamos pronto.

**`WORKDIR /app`** — Define a pasta onde os próximos comandos vão rodar e onde os arquivos serão copiados. Se a pasta não existir, é criada. É o equivalente a fazer `cd /app` dentro do container.

**`COPY requirements.txt .` + `RUN pip install ...`** — Copiamos **só** o `requirements.txt` e instalamos as dependências. O código vem depois. Parece um detalhe, mas faz uma diferença enorme no tempo de build — a seção 12 explica o motivo. A opção `--no-cache-dir` evita que o `pip` guarde os arquivos baixados, o que deixaria a imagem maior sem nenhum benefício.

**`COPY --chown=forzy:forzy . .`** — Copia todo o conteúdo da pasta `backend/` (exceto o que está no `.dockerignore`) para `/app` dentro da imagem. O primeiro `.` é a origem (a pasta onde está o Dockerfile), o segundo é o destino (a pasta de trabalho, `/app`). O `--chown` faz os arquivos pertencerem ao usuário `forzy`, e não ao `root` — senão o `forzy` não conseguiria gravar no `motor.db`.

**`RUN chown forzy:forzy /app`** — O SQLite, ao gravar, cria um arquivo temporário (`motor.db-journal`) na **mesma pasta** do banco. Então não basta o `forzy` ser dono do `motor.db`: ele precisa poder criar arquivos em `/app`. Sem essa linha, o cadastro de motores falha com o erro `attempt to write a readonly database`.

**`USER forzy`** — A partir desta linha, todos os comandos (inclusive o `CMD` que inicia a API) rodam como o usuário `forzy`.

**`EXPOSE 8000`** — Serve como documentação: informa que a aplicação escuta na porta 8000. Ela **não abre** a porta para fora do container sozinha. Quem faz isso é a opção `-p` do `docker run` (ou `ports` no compose), que veremos a seguir.

**`HEALTHCHECK`** — Diz ao Docker como verificar se a aplicação está realmente funcionando, e não apenas se o processo existe. A cada 15 segundos, o Docker executa um pequeno comando Python que acessa a rota `/` do Forzy (aquela que responde `{"status": "ok", ...}` e não exige API Key). Se a rota responder, o container é marcado como `healthy`. Se falhar cinco vezes seguidas, vira `unhealthy`. O `--start-period=10s` dá um tempo inicial para a API subir antes de começar a contar falhas. Usamos Python para essa verificação, e não o `curl`, porque a imagem `slim` não vem com `curl` instalado — um erro comum em Dockerfiles copiados da internet.

**`CMD [...]`** — O comando que roda quando um container é iniciado a partir desta imagem. Repare em duas diferenças em relação ao que você digita no terminal durante o desenvolvimento:

- `--host 0.0.0.0` — pelo motivo explicado na seção 5.4;
- **sem `--reload`** — o `--reload` fica vigiando os arquivos e reinicia o servidor a cada alteração. É ótimo para desenvolver, mas num container o código não muda depois de construído, e o monitoramento só consome recursos.

## 6.2 Construindo a imagem

No terminal do VS Code, entre na pasta do back-end e rode:

```bash
cd backend
docker build -t forzy-backend .
```

- `docker build` constrói uma imagem a partir de um Dockerfile;
- `-t forzy-backend` dá um nome (tag) à imagem, para você não precisar lidar com o identificador gerado automaticamente;
- o `.` no final indica que o Dockerfile e os arquivos estão na pasta atual.

A primeira execução demora um pouco: o Docker baixa a imagem base do Python e instala as dependências. Você vai ver cada instrução do Dockerfile sendo executada em ordem. Ao final, confira que a imagem existe:

```bash
docker images
```

Deve aparecer uma linha com `forzy-backend` e o tamanho da imagem.

## 6.3 Rodando o container

```bash
docker run --name forzy-backend -p 8000:8000 --env-file .env forzy-backend
```

- `--name forzy-backend` dá um nome ao container (senão o Docker inventa um aleatório);
- `-p 8000:8000` liga a porta 8000 da sua máquina à porta 8000 do container. O formato é sempre `porta_da_sua_máquina:porta_do_container`. Sem isso, a API roda isolada lá dentro e ninguém consegue acessá-la;
- `--env-file .env` lê o arquivo `.env` da sua máquina e injeta cada variável no container no momento em que ele inicia.

Com o container rodando, abra o navegador:

1. Acesse `http://localhost:8000/` — deve aparecer `{"status": "ok", "servico": "Forzy Digital Twin API"}`.
2. Acesse `http://localhost:8000/docs` — o Swagger com os grupos Equipamentos, Plantas e Sensores.
3. Clique em **Authorize**, cole o valor de `API_KEY` do seu `backend/.env` e teste `GET /v1/equipamentos`. Os motores do `motor.db` devem aparecer.
4. Teste `GET /v1/sensores/MTR-001/leitura-atual` e confira que `severidade_temp` e `severidade_vibracao` vêm calculados.

Pelo terminal, o mesmo teste:

```bash
curl -H "X-API-Key: SUA_CHAVE_AQUI" http://localhost:8000/v1/equipamentos/tags
```

Para parar o container, pressione `Ctrl+C` no terminal. Para removê-lo (e poder criar outro com o mesmo nome):

```bash
docker rm forzy-backend
```

## 6.4 E o `load_dotenv()` do `main.py`?

O `main.py` do Forzy chama `load_dotenv()` logo no início. Fora do Docker, essa função lê o arquivo `.env` e carrega as variáveis. Dentro do container, **não existe arquivo `.env`** — ele foi barrado pelo `.dockerignore`. Então o `load_dotenv()` simplesmente não encontra nada e segue em frente, sem erro.

As variáveis chegam por outro caminho: o `--env-file .env` do `docker run` as injeta diretamente no ambiente do processo. Quando o código chama `os.getenv("API_KEY")`, a variável já está lá. Resultado: o mesmo código funciona fora do Docker (lendo o arquivo) e dentro dele (lendo o ambiente), sem nenhuma alteração.

## 6.5 E o LangSmith?

A instrumentação com `@traceable` e `trace()` continua funcionando dentro do container sem nenhuma mudança de código. O SDK do LangSmith lê `LANGSMITH_API_KEY`, `LANGSMITH_TRACING` e `LANGSMITH_PROJECT` do ambiente — e essas variáveis estão no `backend/.env`, injetado pelo `--env-file`.

Para confirmar: faça algumas chamadas pelo Swagger e abra o projeto `forzy-digital-twin` no LangSmith. Os traces `endpoint_leitura_atual`, `db_leitura_atual` e `classificar_severidade` devem aparecer normalmente. O container precisa de acesso à internet para enviar os traces, e por padrão o Docker libera a saída.

---

# 7. Dockerfile do Front-end (Gradio)

Crie o arquivo `frontend/Dockerfile`:

```dockerfile
# frontend/Dockerfile — imagem da interface Gradio do Forzy

FROM python:3.12.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # O Gradio lê estas variáveis automaticamente ao chamar launch():
    # escutar em todas as interfaces (obrigatório dentro de container) e na porta 7860
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

RUN useradd --create-home --uid 1000 forzy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=forzy:forzy . .

USER forzy

EXPOSE 7860

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/')" || exit 1

CMD ["python", "app.py"]
```

A estrutura é praticamente igual à do back-end. As diferenças estão em três pontos.

**`GRADIO_SERVER_NAME=0.0.0.0` e `GRADIO_SERVER_PORT=7860`** — O Gradio, quando executa `launch()`, procura essas duas variáveis de ambiente. Se encontrar, usa os valores delas. Assim resolvemos o problema do `localhost` dentro do container sem alterar uma linha do `app.py`. **Importante:** isso só funciona se o `app.py` não passar `server_name` explicitamente no `launch()`. Se o seu `app.py` tiver algo como `launch(server_name="127.0.0.1")`, remova esse parâmetro — valores passados no código têm prioridade sobre as variáveis de ambiente.

**Não há `chown /app`** — O front-end do Forzy não grava nada em disco: ele só chama a API. Então basta os arquivos pertencerem ao usuário `forzy`.

**`--start-period=20s`** — O Gradio costuma demorar um pouco mais que o FastAPI para ficar pronto, então damos mais tempo antes de começar a contar falhas na verificação de saúde.

## 7.1 Construindo e testando o front sozinho

```bash
cd frontend
docker build -t forzy-frontend .
docker run --name forzy-frontend -p 7860:7860 --env-file .env forzy-frontend
```

Abra `http://localhost:7860`. A interface do Forzy carrega... mas a lista de equipamentos aparece vazia e o terminal mostra:

```
[api_provider] Não foi possível conectar ao back-end em http://localhost:8000.
```

Isso acontece mesmo com o container do back-end rodando em outro terminal. Entender o porquê é fundamental.

O `frontend/.env` diz `API_URL=http://localhost:8000`. Mas quem faz essa chamada HTTP é o `api_provider.py`, que roda **dentro do container do front**. Para ele, `localhost` é o próprio container do front — onde não existe nenhuma API na porta 8000. Cada container tem o seu próprio `localhost`.

```
Sua máquina
├── container forzy-frontend  → "localhost" = ele mesmo (não tem API aqui)
└── container forzy-backend   → "localhost" = ele mesmo (a API está aqui)
```

Existem duas formas de resolver:

1. **Paliativa:** apontar para a sua máquina, usando o endereço especial `host.docker.internal`, que o Docker Desktop traduz como "a máquina hospedeira". Como o back-end publicou a porta 8000 na sua máquina, a chamada chega nele:

   ```bash
   docker run --name forzy-frontend -p 7860:7860 --env-file .env \
   -e API_URL=http://host.docker.internal:8000 forzy-frontend
   ```

   No Linux, esse endereço não existe por padrão. É preciso acrescentar `--add-host=host.docker.internal:host-gateway` ao comando.

2. **Definitiva:** colocar os dois containers na mesma rede, para que um encontre o outro pelo nome. É exatamente o que o docker compose faz, e é o que vamos usar (seção 9).

Pare e remova os dois containers antes de continuar:

```bash
docker rm -f forzy-frontend forzy-backend
```

(`-f` força a remoção mesmo que o container ainda esteja rodando.)

---

# 8. O Banco de Dados Dentro do Container

Esta é a seção mais importante da aula para o Forzy, porque o projeto tem algo que muitos exemplos de Docker não têm: um banco de dados em arquivo que **recebe escritas**. O formulário de cadastro faz `POST /v1/equipamentos`, que executa `INSERT OR REPLACE` no `motor.db`.

## 8.1 Onde o `motor.db` está

Quando o Docker executa `COPY . .` durante o build, o `motor.db` da sua pasta é copiado para dentro da imagem, em `/app/motor.db`. Lembre que a imagem é **somente leitura**. Então o que acontece quando a API grava um motor novo?

O container tem uma camada gravável por cima da imagem. Na primeira vez que o SQLite escreve no `motor.db`, o Docker faz uma cópia do arquivo para essa camada, e a escrita vai para a cópia. A imagem original continua intacta.

```
┌──────────────────────────────────┐
│ Camada gravável do container     │  ← motor.db com o motor novo (MTR-021)
├──────────────────────────────────┤
│ Imagem forzy-backend (só leitura)│  ← motor.db original, com MTR-001 a MTR-020
└──────────────────────────────────┘
```

## 8.2 Experimento: o motor que desaparece

Faça este experimento. Ele vale mais do que qualquer explicação.

**Passo 1 — Suba o back-end em segundo plano.** A opção `-d` (*detached*) roda o container sem prender o terminal:

```bash
cd backend
docker run -d --name forzy-backend -p 8000:8000 --env-file .env forzy-backend
```

**Passo 2 — Cadastre um motor novo.** Pelo Swagger (`http://localhost:8000/docs`), autorize com a sua chave e execute `POST /v1/equipamentos` com este corpo:

```json
{
  "tag": "MTR-099",
  "modelo": "W22 Teste Docker",
  "fabricante": "WEG",
  "potencia_cv": 10
}
```

A resposta deve ser `Equipamento MTR-099 cadastrado com sucesso.` Confira com `GET /v1/equipamentos/MTR-099`.

**Passo 3 — Pare e inicie o mesmo container.**

```bash
docker stop forzy-backend
docker start forzy-backend
```

Consulte `GET /v1/equipamentos/MTR-099` de novo. **O motor continua lá.** Parar e iniciar mantém a camada gravável.

**Passo 4 — Remova o container e crie outro a partir da mesma imagem.**

```bash
docker rm -f forzy-backend
docker run -d --name forzy-backend -p 8000:8000 --env-file .env forzy-backend
```

Consulte `GET /v1/equipamentos/MTR-099`. **O motor sumiu** (`404`). O novo container nasceu da imagem, que tem o `motor.db` original. A camada gravável do container anterior foi apagada junto com ele.

## 8.3 Por que isso importa tanto

Remover e recriar containers é rotina, não exceção. Acontece quando você:

- muda o código e reconstrói a imagem (`docker build`) para rodar a versão nova;
- atualiza uma dependência;
- faz um novo deploy numa plataforma de nuvem — que quase sempre destrói o container antigo e cria um novo.

Ou seja: com o banco dentro do container, **todo cadastro feito pelos usuários se perde no próximo deploy**. Para um sistema de gestão de motores industriais, isso é inaceitável.

> **Princípio:** containers são descartáveis. Tudo que precisa sobreviver a eles — bancos, uploads, arquivos gerados — tem que morar **fora** do container.

## 8.4 A solução: volumes

Um **volume** é uma forma de ligar uma pasta ou arquivo de fora do container a um caminho dentro dele. O container lê e grava normalmente, mas os dados ficam fora da camada gravável e sobrevivem à remoção.

Existem dois tipos principais:

| Tipo | Como funciona | Quando usar |
|---|---|---|
| **Bind mount** | Liga um arquivo ou pasta **da sua máquina** a um caminho do container | Desenvolvimento: você enxerga e edita o arquivo diretamente |
| **Volume nomeado** | O Docker cria e gerencia uma área de armazenamento própria | Produção: você não precisa saber onde o arquivo está fisicamente |

Para o Forzy em desenvolvimento, o bind mount é o mais didático: o `motor.db` da sua pasta `backend/` passa a ser **o mesmo arquivo** usado pelo container.

```bash
docker rm -f forzy-backend

docker run -d --name forzy-backend -p 8000:8000 --env-file .env \
  -v "$(pwd)/motor.db:/app/motor.db" \
  forzy-backend
```

O formato de `-v` é `caminho_na_sua_máquina:caminho_no_container`. O `$(pwd)` é substituído pelo caminho da pasta atual. No PowerShell do Windows, use `${PWD}` no lugar de `$(pwd)`.

Repita o experimento: cadastre o `MTR-099`, remova o container, crie outro com o mesmo `-v` e consulte. **O motor continua lá**, porque agora ele foi gravado no `motor.db` da sua máquina, e não na camada do container.

> **Efeito colateral:** com o bind mount, os cadastros feitos pela API alteram o `motor.db` do seu repositório. Se você não quiser commitar essas alterações, rode `git checkout backend/motor.db` para voltar ao banco original.

## 8.5 E em produção?

Ao colocar a API no ar, a pergunta "onde o banco mora?" volta com força, e cada plataforma responde de um jeito:

- em plataformas gratuitas, o disco do container costuma ser **efêmero** — o mesmo comportamento do passo 4 do experimento acontece a cada reinício;
- em servidores próprios, como uma máquina na AWS, é possível usar volumes como fizemos aqui;
- em sistemas maiores, o SQLite costuma dar lugar a um banco gerenciado, que roda como um serviço separado.

Guarde o experimento da seção 8.2 na cabeça: ele explica boa parte das decisões que vamos tomar no deploy.

---

# 9. docker compose — Subindo o Forzy Inteiro

Até aqui usamos comandos `docker run` longos, com várias opções, em dois terminais, e ainda esbarramos no problema de um container não enxergar o outro. O docker compose resolve tudo isso descrevendo os dois serviços num único arquivo.

Crie o arquivo `docker-compose.yml` **na raiz do projeto** (fora das pastas `backend/` e `frontend/`):

```yaml
# docker-compose.yml — sobe a API e a interface do Forzy juntas

services:

  backend:
    build: ./backend                 # usa o backend/Dockerfile
    container_name: forzy-backend
    ports:
      - "8000:8000"                  # sua_máquina:container — Swagger acessível em localhost:8000
    env_file:
      - ./backend/.env               # API_KEY e variáveis do LangSmith
    volumes:
      - ./backend/motor.db:/app/motor.db   # banco fora do container: cadastros sobrevivem
    restart: unless-stopped          # reinicia se cair, a menos que você pare manualmente

  frontend:
    build: ./frontend                # usa o frontend/Dockerfile
    container_name: forzy-frontend
    ports:
      - "7860:7860"                  # interface acessível em localhost:7860
    env_file:
      - ./frontend/.env              # API_KEY e APP_VERSION
    environment:
      # Dentro da rede do compose, o back-end é encontrado pelo NOME DO SERVIÇO.
      # Este valor substitui o API_URL=http://localhost:8000 do frontend/.env.
      API_URL: http://backend:8000
    depends_on:
      backend:
        condition: service_healthy   # só sobe o front depois que o HEALTHCHECK do back passar
    restart: unless-stopped
```

## 9.1 Entendendo o arquivo

**`services`** — Cada entrada é um container. O nome do serviço (`backend`, `frontend`) é importante: ele vira o **nome de rede** do container.

**`build: ./backend`** — Em vez de você rodar `docker build` manualmente, o compose constrói a imagem a partir do Dockerfile daquela pasta.

**`ports`** — O mesmo papel do `-p` no `docker run`.

**`env_file`** — O mesmo papel do `--env-file`.

**`volumes`** — O mesmo bind mount da seção 8.4, agora com caminho relativo ao `docker-compose.yml`. Não precisa de `$(pwd)`.

**`environment`** — Define variáveis diretamente no arquivo. Quando a mesma variável aparece no `env_file` e no `environment`, **o `environment` vence**. É assim que o `API_URL` do front passa a apontar para `http://backend:8000` dentro do compose, enquanto o `frontend/.env` continua com `http://localhost:8000` para quando você roda o front fora do Docker.

**`depends_on` com `condition: service_healthy`** — Resolve o problema de ordem de inicialização. O compose sobe o back-end, espera o `HEALTHCHECK` definido no `backend/Dockerfile` marcar o container como `healthy`, e só então sobe o front. Sem a condição, o compose apenas iniciaria o back primeiro, sem esperar ele estar pronto para responder.

**`restart: unless-stopped`** — Se o processo cair por algum erro, o Docker reinicia o container automaticamente. Se você parar manualmente, ele respeita.

## 9.2 A rede entre os containers

Você não precisou declarar nenhuma rede no arquivo. O compose cria automaticamente uma rede privada para o projeto e coloca os dois serviços nela. Dentro dessa rede, existe um DNS interno: o nome `backend` é traduzido para o endereço do container do back-end.

É por isso que o `api_provider.py` do front, lendo `API_URL=http://backend:8000`, consegue chegar na API. Repare que é a porta **8000 do container**, e não a da sua máquina: dentro da rede, os containers se falam diretamente, sem passar pelo mapeamento de `ports`.

```
Rede do compose (criada automaticamente)
├── frontend ──http://backend:8000──▶ backend
│   (porta 7860 publicada)             (porta 8000 publicada)
│
Sua máquina
├── navegador → localhost:7860 → frontend
└── navegador → localhost:8000 → backend (Swagger)
```

## 9.3 Subindo tudo

Na raiz do projeto:

```bash
docker compose up --build
```

- `up` cria e inicia todos os serviços;
- `--build` reconstrói as imagens antes de subir. Use sempre que tiver mudado código ou dependências.

Os logs dos dois containers aparecem intercalados no terminal, cada linha com o nome do serviço à esquerda. Você vai ver o back-end subir primeiro, a verificação de saúde passar e só então o front iniciar.

Abra `http://localhost:7860` e use o Forzy normalmente: lista de equipamentos, ficha técnica, cadastro, sensores e dashboard. No terminal, as requisições do front aparecem nos logs do back.

Para rodar em segundo plano, liberando o terminal:

```bash
docker compose up --build -d
```

Para acompanhar os logs depois:

```bash
docker compose logs -f              # todos os serviços
docker compose logs -f backend      # só o back-end
```

Para parar e remover os containers (o `motor.db` fica intacto, porque está no bind mount):

```bash
docker compose down
```

---

# 10. Variáveis de Ambiente e Segredos

Com Docker, existem dois momentos em que uma variável pode entrar: durante a **construção** da imagem ou durante a **execução** do container. Para segredos, a regra é simples:

> **Segredos entram só na execução. Nunca na construção.**

## 10.1 O erro que parece inofensivo

Seria tentador escrever no Dockerfile:

```dockerfile
# ERRADO — nunca faça isso
ENV API_KEY=chave-super-secreta-dev
ENV LANGSMITH_API_KEY=lsv2_pt_abc123...
```

Funciona. Mas agora as chaves estão **gravadas dentro da imagem**. Qualquer pessoa com acesso a ela consegue lê-las, por exemplo com:

```bash
docker history forzy-backend
docker inspect forzy-backend
```

E se a imagem for publicada num registro público, ou enviada para uma plataforma de deploy, as chaves vão junto. O mesmo vale para copiar o `.env` para dentro da imagem — por isso ele está no `.dockerignore`.

## 10.2 O jeito certo

A imagem é construída **sem nenhum segredo**. As chaves são entregues só quando o container inicia:

- localmente, por `--env-file` ou `env_file` no compose, lendo o `.env` da sua máquina;
- em plataformas de nuvem, pelo painel de "Secrets" ou "Environment variables" de cada serviço.

A consequência é poderosa: **a mesma imagem** pode rodar em desenvolvimento, com uma chave de teste, e em produção, com a chave real, sem ser reconstruída. Só o ambiente muda.

## 10.3 Checklist de segurança antes de construir uma imagem

- O `.env` está no `.dockerignore` de cada pasta.
- O `.env` está no `.gitignore` da raiz.
- Nenhum `ENV` do Dockerfile contém chave, senha ou token.
- Nenhum arquivo de código tem chave escrita diretamente (`API_KEY = "..."`).
- O `.env.example` tem apenas valores fictícios.

Um jeito rápido de conferir o último item antes de commitar:

```bash
grep -rn "lsv2_" --include="*.py" .    # chaves do LangSmith no código
grep -rn "API_KEY\s*=\s*\"" --include="*.py" .    # API_KEY com valor fixo
```

---

# 11. E o CORS, Como Fica?

O `main.py` do Forzy configura CORS permitindo a origem `http://localhost:7860`. Com o compose, o front passa a chamar `http://backend:8000`. Será que o CORS vai bloquear?

Não vai, e vale entender por quê. O CORS é uma regra aplicada **pelo navegador**, e só quando um código JavaScript rodando numa página tenta chamar uma API em outra origem. No Forzy, quem chama a API é o `api_provider.py`, usando a biblioteca `requests`, dentro do processo Python do Gradio — no servidor, e não no navegador. Uma chamada feita por `requests` ignora o CORS completamente, dentro ou fora do Docker.

```
Navegador ──▶ Gradio (servidor Python) ──requests──▶ FastAPI
               └─ esta chamada é servidor → servidor: CORS não se aplica
```

Então por que manter a configuração de CORS? Porque a API do Forzy foi pensada para ter outros clientes além do Gradio. No dia em que um cliente rodar **no navegador ou num app** e chamar a API diretamente, o CORS passa a valer, e a lista `allow_origins` vai precisar incluir o endereço desse cliente. Guarde essa ideia para quando o Forzy ganhar novos clientes.

---

# 12. Por que a Ordem das Instruções Importa: Cache de Camadas

Cada instrução do Dockerfile gera uma **camada** da imagem. O Docker guarda essas camadas em cache. Na próxima vez que você rodar `docker build`, ele reaproveita todas as camadas cujo conteúdo não mudou — e reconstrói a partir da **primeira instrução que mudou**, junto com todas as que vêm depois dela.

Compare as duas formas de escrever o back-end do Forzy:

```dockerfile
# Ruim — qualquer mudança no código reinstala todas as dependências
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

```dockerfile
# Bom — dependências ficam em cache enquanto o requirements.txt não mudar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=forzy:forzy . .
```

Na primeira forma, o `COPY . .` copia o projeto inteiro. Se você altera uma única linha em `routers/sensores.py` — por exemplo, recalibrando um limite da ISO 10816 —, essa camada muda, e o `pip install` que vem depois precisa rodar de novo. Com o Gradio e o Plotly no front, isso pode levar minutos a cada build.

Na segunda forma, o `requirements.txt` é copiado sozinho. Enquanto ele não mudar, a camada do `pip install` vem do cache, e só a última camada (a cópia do código) é refeita. O build cai para poucos segundos.

Na prática, durante o desenvolvimento você altera o código muitas vezes por dia e o `requirements.txt` raramente. A ordem certa faz essa diferença a cada build.

Você consegue ver o cache funcionando: rode `docker compose build` duas vezes seguidas. Na segunda, as etapas aparecem marcadas como `CACHED`. Depois altere um comentário em qualquer arquivo `.py` do back-end e rode de novo: só a etapa de cópia do código é refeita.

---

# 13. Comandos do Dia a Dia

| O que você quer fazer | Comando |
|---|---|
| Subir o Forzy (reconstruindo as imagens) | `docker compose up --build` |
| Subir em segundo plano | `docker compose up --build -d` |
| Ver o estado dos containers | `docker compose ps` |
| Acompanhar os logs | `docker compose logs -f` |
| Logs só do back-end | `docker compose logs -f backend` |
| Parar e remover os containers | `docker compose down` |
| Reiniciar só o back-end | `docker compose restart backend` |
| Abrir um terminal dentro do container | `docker compose exec backend sh` |
| Listar as imagens | `docker images` |
| Ver uso de CPU e memória | `docker stats` |
| Limpar containers, imagens e cache sem uso | `docker system prune` |

## Inspecionando o banco de dentro do container

O comando `exec` executa algo dentro de um container que já está rodando. Isso é útil para investigar o `motor.db` sem sair do Docker:

```bash
docker compose exec backend python -c "import sqlite3; c = sqlite3.connect('motor.db'); print(c.execute('SELECT COUNT(*) FROM motores').fetchone())"
```

Ou para abrir um terminal lá dentro e explorar os arquivos:

```bash
docker compose exec backend sh
ls -la          # confira que motor.db pertence ao usuário forzy
whoami          # deve responder: forzy
exit
```

---

# 14. Roteiro de Verificação

Com `docker compose up --build` rodando, confira cada item:

1. `docker compose ps` mostra `forzy-backend` com status `healthy` e `forzy-frontend` em execução.
2. `http://localhost:8000/docs` abre o Swagger. `GET /v1/equipamentos` responde `401` sem chave e `200` com a chave do `.env`.
3. `http://localhost:7860` abre o Forzy e a lista de equipamentos carrega.
4. Cadastre um motor novo pela interface. Rode `docker compose down` e depois `docker compose up -d`. O motor continua cadastrado.
5. Navegue pelo Dashboard (Planta → Área → Equipamento) e pela página de Sensores. Nos logs do back-end, as requisições aparecem.
6. No LangSmith, os traces chegam com `metadata.client_platform`, `metadata.feature` e `metadata.app_version` preenchidos.
7. Rode `docker compose stop backend` e use o Forzy. A mensagem de erro de conexão aparece no lugar de uma tela quebrada. Rode `docker compose start backend` e tudo volta a funcionar.

---

# 15. Problemas Comuns

| Sintoma | Causa provável | Como resolver |
|---|---|---|
| Container roda, mas o navegador não conecta | Servidor escutando em `127.0.0.1` dentro do container | Conferir `--host 0.0.0.0` no back e `GRADIO_SERVER_NAME=0.0.0.0` no front; remover `server_name` fixo do `launch()` |
| Front mostra "Não foi possível conectar ao back-end em http://localhost:8000" | `API_URL` aponta para o `localhost` do próprio container do front | No compose, usar `API_URL: http://backend:8000` em `environment` |
| Todas as chamadas voltam `401 Unauthorized` | `API_KEY` diferente nos dois `.env`, ou `.env` ausente | Conferir que os dois arquivos existem e têm o mesmo valor; rodar `docker compose up` de novo |
| `attempt to write a readonly database` ao cadastrar | Usuário `forzy` sem permissão de escrita no `motor.db` ou na pasta | Conferir o `chown` no Dockerfile. No Linux, com bind mount, rodar `chmod 664 backend/motor.db` e garantir que a pasta `backend/` permita escrita |
| Motor cadastrado some depois de um novo `up --build` | Banco dentro do container, sem volume | Conferir a linha `volumes` do serviço `backend` no compose |
| `port is already allocated` | Outro processo (ou um `uvicorn` esquecido fora do Docker) já usa a porta 8000 ou 7860 | Encerrar o processo ou mudar a porta da sua máquina: `"8001:8000"` |
| Front nunca sobe e o back fica `unhealthy` | A API está falhando ao iniciar (erro de import, variável faltando) | `docker compose logs backend` para ver o erro |
| `ModuleNotFoundError` dentro do container | Biblioteca usada no código mas ausente do `requirements.txt` | Adicionar ao `requirements.txt` e rodar `docker compose up --build` |
| Os `print()` do `api_provider` não aparecem nos logs | Saída do Python em buffer | Conferir `PYTHONUNBUFFERED=1` no Dockerfile |
| Traces não chegam no LangSmith | Variáveis `LANGSMITH_*` ausentes do `backend/.env` | Conferir o arquivo e reiniciar com `docker compose up -d` |
| Mudei o código e nada mudou no container | Imagem antiga sendo reutilizada | Rodar `docker compose up --build` (com `--build`) |


---

# Referências

- [Docker — Documentação oficial](https://docs.docker.com)
- [Docker — Instalação do Docker Desktop](https://docs.docker.com/desktop/)
- [Dockerfile — Referência de instruções](https://docs.docker.com/reference/dockerfile/)
- [Dockerfile — Boas práticas](https://docs.docker.com/build/building/best-practices/)
- [Docker Compose — Documentação](https://docs.docker.com/compose/)
- [Docker — Volumes e bind mounts](https://docs.docker.com/engine/storage/)
- [FastAPI — Deploy com Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Gradio — Variáveis de ambiente](https://www.gradio.app/guides/environment-variables)
- [12-Factor App — Configuração](https://12factor.net/config)
