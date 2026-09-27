# Aula 20 — Deploy Gratuito: a API no Render, o front no Streamlit Cloud

Na aula anterior o Forzy foi empacotado em containers. Hoje ele roda assim na sua máquina:

```
docker compose up
  ├── forzy-backend   → localhost:8000   FastAPI + SQLite + LangSmith
  └── forzy-frontend  → localhost:7860   Gradio
```

Os dois containers se enxergam porque estão na mesma rede do compose, e você os acessa porque as portas foram publicadas na sua máquina. Só que tudo isso morre no instante em que você fecha o terminal — e ninguém além de você jamais viu o projeto funcionando.

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

# 1. Uma Lição que Não Estava no Plano

Este material foi escrito para publicar a API num **Hugging Face Space em modo Docker**, que era gratuito. Em **julho de 2026**, sem nenhum anúncio, o Hugging Face passou a exigir plano pago para criar Spaces com SDK Docker. Quem tenta agora recebe:

> *Add billing to your account (credits or subscribe to PRO) to unlock Docker Spaces*

A página de preços sequer foi atualizada. A mudança só apareceu no fórum, em relatos de usuários.

Guarde isso, porque é uma lição de arquitetura mais valiosa do que qualquer comando desta aula:

> **Um tier gratuito é uma decisão comercial de outra empresa, e ela pode mudar da noite para o dia, sem aviso.**

Se o seu projeto depende de uma plataforma específica para existir, você não controla o próprio projeto. A defesa não é escolher "a plataforma certa" — é manter a aplicação **portável**, de forma que trocar de casa seja um trabalho de uma tarde e não uma reescrita.

E é exatamente aqui que o Docker se paga. Repare no que vai acontecer nesta aula: a mesma API, sem uma linha de código alterada, vai subir num provedor completamente diferente do planejado. O Dockerfile da aula passada continua valendo, porque ele descreve a aplicação, não a plataforma.

A Aula 19, então, não foi sobre o Hugging Face. Foi sobre não depender dele.

---

# 2. Onde Cada Coisa Pode Morar Hoje

Nenhuma plataforma gratuita roda "qualquer coisa". Cada uma sabe executar um formato de aplicação, e é isso que decide onde cada parte do Forzy vai parar.

| Plataforma | Gratuito sem cartão | Aceita Dockerfile | Deploy nativo Python | Hibernação |
|---|---|---|---|---|
| **Render** | sim | **sim** | **sim** | 15 min, acorda em 30–50 s |
| **Streamlit Community Cloud** | sim | não | só Streamlit | sim |
| **Hugging Face Spaces** (sdk gradio/streamlit) | sim | **não mais** | só Gradio/Streamlit | sim |
| Google Cloud Run | exige cartão | sim | via buildpacks | sim, acorda em 5–15 s |
| Koyeb | sim | sim | sim | variável |
| Railway | só US$ 1/mês de crédito | sim | sim | para quando o crédito acaba |

Heroku encerrou o tier gratuito em 2022 e o Fly.io reduziu o dele em 2024. Vercel e Cloudflare Workers não servem para o Forzy: a primeira corta a execução em 10 segundos, a segunda limita a 10 milissegundos de CPU — nenhuma das duas roda um processo Python de longa duração.

A escolha desta aula:

- **API FastAPI → Render.** É a única opção da lista que aceita, de graça e sem cartão, tanto um Dockerfile quanto código Python puro. Essa dupla possibilidade é o que permite a comparação da seção 5.
- **Front Streamlit → Streamlit Community Cloud.** A casa natural dele.
- **Front Gradio → Hugging Face Spaces com SDK `gradio`.** Continua gratuito; só o SDK Docker virou pago.

## 2.1 A separação que já estava pronta

Talvez o ponto mais importante desta aula não seja técnico. Repare no que estamos prestes a fazer: colocar o front num provedor, o back em outro, e fazer os dois conversarem por HTTP, sem que nenhuma linha de regra de negócio precise ser movida ou duplicada.

Isso só é possível porque o Forzy foi separado em dois processos independentes. No Sprint original, com o Gradio acessando o `motor.db` diretamente, essa arquitetura seria impensável: o front teria que carregar o banco junto.

Guarde essa observação, porque ela reaparece na aula de mobile: **o produto é a API. O front é substituível.**

---

# 3. Preparando o Repositório

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

## 3.1 O que vai para o repositório

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

# 4. Parte 1 — A API no Render, sem Docker

Esta parte vem primeiro por um motivo prático: o front só pode ser configurado depois que você souber o endereço da API.

E começamos **sem Docker** de propósito. Assim fica claro, por contraste, o que o Dockerfile acrescenta na Parte 2.

## 4.1 Criando a conta e o serviço

1. Acesse [render.com](https://render.com) e crie a conta entrando com o GitHub. **Não é pedido cartão de crédito** para o plano gratuito.
2. No painel, escolha **New → Web Service**.
3. Conecte o repositório do Forzy e autorize o acesso.
4. Preencha:

```
Name:              forzy-api
Language:          Python 3
Branch:            main
Root Directory:    backend
Build Command:     pip install -r requirements.txt
Start Command:     uvicorn main:app --host 0.0.0.0 --port $PORT
Instance Type:     Free
Health Check Path: /
```

Cinco campos merecem explicação.

**`Root Directory: backend`** — diz ao Render que a aplicação vive numa subpasta. Sem isso, ele procuraria o `requirements.txt` na raiz do repositório e não encontraria nada.

**`Build Command`** — o que roda uma vez, na construção. É o mesmo `pip install` que você digita localmente. O Render cria o ambiente virtual sozinho.

**`Start Command`** — o que roda para servir a aplicação. Repare em duas coisas:

- `--host 0.0.0.0`, pelo mesmo motivo da aula anterior: escutar só em `127.0.0.1` torna o processo inalcançável de fora.
- `--port $PORT`, que é novo. O Render **escolhe** a porta e a entrega numa variável de ambiente chamada `PORT`. Sua aplicação não decide em qual porta vai rodar — ela obedece. Uma porta fixa como `--port 8000` faz o serviço subir e nunca receber tráfego, porque o roteador da plataforma está encaminhando para outro lugar.

**`Health Check Path: /`** — o Render chama essa rota periodicamente para saber se a aplicação está viva. É exatamente o mesmo papel do `HEALTHCHECK` do Dockerfile, agora feito pela plataforma. Usamos `/` porque é a única rota do Forzy que não exige `X-API-Key`.

**`Instance Type: Free`** — 512 MB de memória e 750 horas por mês. Uma instância rodando o mês inteiro usa cerca de 730 horas, então cabe.

## 4.2 A versão do Python

O runtime nativo escolhe uma versão padrão do Python, que muda com o tempo. Como o Forzy usa sintaxe que exige 3.10 ou superior (`list[dict]`, `dict | None`), e como você testou tudo numa versão específica, fixe-a. Crie o arquivo:

```text
# backend/.python-version
3.12.10
```

Este arquivo é o equivalente, no runtime nativo, à linha `FROM python:3.12.10` do Dockerfile. Repare na diferença de alcance: o Dockerfile fixa o sistema operacional inteiro; o `.python-version` fixa só o interpretador. Volte a esse ponto na seção 6.

## 4.3 Configurando as variáveis de ambiente

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

## 4.4 Publicando e testando

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

# 5. Parte 2 — A Mesma API no Render, com Docker

Agora publique a **mesma aplicação, do mesmo repositório**, num segundo serviço — desta vez usando o Dockerfile da Aula 19. Os dois vão conviver, e comparar os dois é o objetivo.

## 5.1 O Dockerfile precisa aprender sobre `$PORT`

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

## 5.2 Criando o segundo serviço

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

# 6. O Que os Dois Modos Ensinam

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

**Sem Docker, a configuração da sua aplicação mora no painel de um fornecedor.** Ela não está no Git, ninguém revisa em pull request, e quem for reproduzir o ambiente precisa de acesso àquela conta. Se a plataforma sumir — ou passar a cobrar, como aconteceu em julho —, a configuração some junto.

**Com Docker, ela mora no repositório.** Versionada, revisável, e igual em qualquer lugar que aceite containers.

Em troca, o Docker cobra: mais um arquivo para manter, builds mais lentos, e um conceito a mais para aprender. Para um projeto pequeno e estável, o runtime nativo é perfeitamente adequado e mais simples. É uma escolha de engenharia, não uma questão de certo e errado.

> **O critério prático:** quanto mais o seu ambiente se afasta de "Python e algumas bibliotecas" — uma versão específica de uma biblioteca de sistema, um binário externo, um processo auxiliar —, mais o Dockerfile deixa de ser luxo e vira necessidade.

---

# 7. O Preço do Gratuito

O serviço está no ar e não custa nada. Em troca, três coisas passam a ser verdade. Entendê-las importa mais do que o deploy em si.

## 7.1 O disco é efêmero

Lembra do experimento da aula anterior, em que o motor cadastrado sumia quando o container era removido e recriado? **No plano gratuito do Render isso acontece sozinho.** O sistema de arquivos é efêmero: a cada novo deploy, a cada reinício e a cada saída da hibernação, a aplicação recomeça do zero, com o `motor.db` que veio do repositório.

Faça o teste e veja com os próprios olhos:

1. Cadastre o `MTR-099` pelo Swagger da API publicada.
2. Confirme com `GET /v1/equipamentos/MTR-099`.
3. No painel do Render, clique em **Manual Deploy → Deploy latest commit**.
4. Consulte de novo. O motor sumiu.

Não é um defeito da plataforma, é o modelo dela. Um container de nuvem é descartável por definição, e nesse modelo o banco tem que morar fora dele.

O que um sistema real faria:

- **Disco persistente**: o Render oferece discos anexáveis, mas só em planos pagos.
- **Banco gerenciado externo**: o SQLite dá lugar a um Postgres hospedado, que roda como serviço separado e sobrevive a qualquer coisa que aconteça com a aplicação. O Render oferece um Postgres gratuito, com validade limitada.
- **Servidor próprio com volume**, que é o caminho da próxima aula, na AWS.

Para o Forzy em sala, aceite o comportamento e saiba explicá-lo. Se alguém perguntar na apresentação "e se eu cadastrar um motor?", a resposta certa não é "não pensei nisso" — é "no plano gratuito o disco é efêmero; a persistência exigiria disco anexado ou banco gerenciado".

## 7.2 A aplicação hiberna — e isso quebra o front

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

> **Na apresentação:** abra o app alguns minutos antes. Front e API hibernam de forma independente, então a primeira visita pode pagar dois tempos de espera somados.

## 7.3 Você não controla a rede

Sem IP fixo, sem regra de firewall, sem escolher região, sem decidir quem acessa o quê. O Render hospeda nos Estados Unidos; o Streamlit Cloud também.

Para uma demonstração isso é irrelevante. Para um sistema que lê dados proprietários de uma planta industrial, é exatamente o tipo de coisa que o cliente exige controlar — e é o motivo da próxima aula ser sobre AWS.

---

# 8. O Front Precisa de Três Mudanças

Independentemente da plataforma escolhida, sair do `localhost` exige três ajustes. Eles são os mesmos nos dois caminhos das seções 9 e 10.

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

**O tempo de espera precisa crescer**, pelo motivo da seção 7.2.

---

# 9. Parte 3A — O Front Streamlit no Streamlit Community Cloud

Este é o caminho para a versão Streamlit do Forzy (pasta `frontend-streamlit/`).

## 9.1 O que mudou do Gradio para o Streamlit

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

A maior adaptação não é de sintaxe, é de modelo de execução. Quase todo bug de quem vem do Gradio nasce daqui.

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

**O cache deixou de ser opcional.** Se o script inteiro roda de novo a cada clique, todas as chamadas HTTP da tela se repetem. Sem cache, escolher uma TAG no dashboard dispararia de novo as consultas de plantas, áreas e equipamentos — quatro requisições desnecessárias por clique, contra um serviço que hiberna. Por isso as leituras são memorizadas:

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

## 9.2 `st.secrets` — o `.env` da nuvem

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

## 9.3 Rodando localmente antes de publicar

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

## 9.4 O `requirements.txt`

```text
streamlit==1.49.0
pandas==2.3.3
plotly==7.1.0
requests==2.34.2
python-dotenv==1.2.3
```

A versão do Streamlit não é arbitrária: o front usa `width="stretch"` em botões, tabelas e gráficos — o parâmetro que substituiu o antigo `use_container_width` —, disponível a partir da 1.49. Com uma versão mais antiga, o app quebra.

O `pandas` entrou porque as pipelines passaram a devolver `DataFrame`. O `gradio` saiu.

> **Onde colocar o arquivo:** o Streamlit Cloud procura o `requirements.txt` na mesma pasta do arquivo principal ou na raiz do repositório. Com o front numa subpasta, mantenha o arquivo **dentro dela**, ao lado do `app.py`.

## 9.5 Publicando

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

## 9.6 Atualizações automáticas

O Streamlit Cloud observa o repositório: **cada push na branch publicada reimplanta o app**. Não existe botão de "publicar de novo" — o `git push` é o deploy. O Render funciona da mesma forma.

Os segredos são a exceção, e é importante entender por quê: eles ficam na plataforma, não no repositório. Mudar um segredo é feito no painel, e o serviço reinicia em seguida.

---

# 10. Parte 3B — O Front Gradio no Hugging Face Spaces

Este é o caminho para quem mantém a versão Gradio do Forzy. O SDK `gradio` **continua gratuito** — só o SDK Docker passou a exigir plano pago.

## 10.1 Criando o Space

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

## 10.2 O `README.md` do Space

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

## 10.3 O que ajustar no código

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

## 10.4 Publicando

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

# 11. E o CORS? E o HTTPS?

Duas perguntas que sempre aparecem no primeiro deploy.

## 11.1 O CORS continua não se aplicando

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

## 11.2 HTTPS sem esforço

As duas plataformas entregam HTTPS pronto, com certificado válido e renovado automaticamente. Você não gerou certificado, não configurou nada, não pagou nada.

Registre isso como um privilégio do "grátis", porque ele acaba na próxima aula: numa máquina EC2, o HTTPS é problema seu, e resolvê-lo dá trabalho. E não é detalhe estético — sem HTTPS, um app mobile moderno se recusa a chamar a API.

---

# 12. Observabilidade Depois do Deploy

Aqui as aulas de observabilidade se pagam. Você não precisa adivinhar como o Forzy se comporta no ar: você consegue ver.

Abra o LangSmith no projeto `forzy-producao`, use o app publicado por alguns minutos e observe o que chega.

**O cliente aparece sozinho.** O header `X-Client-Platform` identifica de onde veio cada chamada. A versão Streamlit envia `streamlit-cloud`; a Gradio, `gradio-desktop`. Filtrando por `metadata.client_platform`, você compara o comportamento dos dois fronts — que consomem a **mesma** API, com os **mesmos** endpoints.

**Os dois deploys da API podem ser comparados.** Você tem dois serviços, um com Docker e outro sem, servindo a mesma aplicação. Aponte o front para um, use, aponte para o outro, use de novo, e compare as latências. Eles deveriam ser equivalentes — e se não forem, a diferença está no ambiente, não no código. É o tipo de medição que normalmente ninguém consegue fazer.

**A latência real fica visível.** Compare a duração dos traces locais com os de produção. A diferença é a soma de: rede pública, a máquina modesta do tier gratuito e, na primeira chamada após hibernação, o tempo de subir a aplicação. É a primeira vez no curso que você mede o custo do ambiente, e não do código.

**A sessão vira uma linha do tempo.** Filtrando por `metadata.session_id`, você reconstrói tudo o que um usuário fez, em ordem. Quando alguém disser "o dashboard travou", isso deixa de ser um relato e vira um trace.

**A versão distingue um deploy do outro.** Mude `APP_VERSION`, publique e compare latência e taxa de erro entre as duas versões. É o começo de uma prática que times usam a sério: nenhum deploy é considerado bom porque "subiu" — ele é avaliado pelos números depois de subir.

> **A ideia para levar:** deploy sem observabilidade é deploy às cegas. O header `X-App-Version`, que na aula de instrumentação parecia um detalhe, agora é o que separa "a versão nova está no ar" de "a versão nova está melhor".

---

# 13. Apêndice — FastAPI num Space Gradio, sem Docker

Para quem quiser manter tudo no Hugging Face mesmo depois da mudança de julho, existe um caminho.

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

**Isto depende de um comportamento não documentado.** O Hugging Face não promete que um Space Gradio aceite qualquer processo — ele apenas não impede hoje. É exatamente o tipo de brecha que uma plataforma fecha quando quer, do mesmo jeito que fechou o SDK Docker em julho, sem aviso.

Use como curiosidade e como exercício de entender o que uma plataforma realmente executa por baixo. **Não use como caminho principal de um trabalho avaliado**, e muito menos de um sistema que outra pessoa dependa.

---

# 14. Roteiro de Verificação

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

# 15. Problemas Comuns

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

# 16. Exercícios

**1. Sem Docker contra com Docker.** Você tem os dois serviços no ar. Faça dez chamadas a cada um com `curl -w "%{time_total}\n" -o /dev/null -s` e compare os tempos. Depois compare os tempos de **build** nos logs. Qual dos dois é mais rápido para construir? E para responder? Explique a diferença.

**2. Quebrando de propósito.** No serviço Docker, volte o `CMD` para a forma exec com `${PORT}` dentro. Publique e leia os logs. Qual mensagem exata aparece? Por que o erro acontece no uvicorn e não no Docker?

**3. O erro mais comum.** Altere a `API_KEY` do serviço para um valor diferente do que está no front. Abra o app publicado e descreva: qual mensagem o usuário vê? Ela é suficiente para alguém de fora entender o que houve? Se não for, melhore o tratamento do caso `401` no `api_provider` e publique de novo.

**4. Medindo a hibernação.** Deixe o serviço sem acesso por 20 minutos. Cronometre a primeira requisição (`curl -w "%{time_total}\n" -o /dev/null -s <url>`) e uma segunda logo em seguida. Anote os dois tempos. O `_TIMEOUT_ACORDAR` de 75 s é suficiente, exagerado ou insuficiente?

**5. Persistência.** O `motor.db` é efêmero no plano gratuito. Descreva — sem implementar — como resolver isso de três formas: disco anexado pago, banco gerenciado externo e servidor próprio. Para cada uma, aponte um custo e uma desvantagem.

**6. Dois fronts, uma API.** Publique as duas versões do front apontando para a mesma API. No LangSmith, filtre por `metadata.client_platform` e compare: número de requisições por feature e latência média. As duas fazem o mesmo número de chamadas para a mesma tarefa? Se não, por quê?

**7. O custo de não ter cache.** Comente o decorador `@st.cache_data` da função `listar_todos`, publique e navegue pelo app. Conte os traces de `endpoint_listar_equipamentos` antes e depois. Quantas requisições o cache poupou? Em que situação o cache seria um problema, e não uma vantagem?

**8. Portabilidade.** Sem publicar nada, escreva o que seria necessário para mover a API do Render para o Koyeb, em cada um dos dois modos. Qual dos dois dá menos trabalho? Relacione a resposta com a seção 1.

---

# 17. O que Você Tem ao Final desta Aula

- Um endereço HTTPS público para a API do Forzy, com Swagger acessível e endpoints protegidos por chave.
- A **mesma API publicada de duas formas** — runtime nativo e Docker — e clareza sobre o que cada modo entrega e cobra.
- Um endereço HTTPS público para a interface, apontando para essa API.
- Segredos configurados nos painéis das plataformas, fora do repositório.
- Deploy automático: `git push` publica a versão nova nas duas plataformas.
- Tratamento explícito da hibernação, comunicado ao usuário em vez de escondido atrás de um erro.
- Traces de produção separados dos de desenvolvimento, identificados por cliente, feature, sessão e versão.
- Duas interfaces diferentes consumindo a mesma API — a demonstração prática de que o front é substituível e a API é o produto.
- Clareza sobre as três limitações que você aceitou: disco efêmero, hibernação e ausência de controle de rede. São elas que motivam a próxima aula, sobre AWS.
- E uma lição que não estava no plano: a plataforma gratuita de hoje pode ser a plataforma paga de amanhã, e a defesa contra isso é manter a aplicação portável.

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
