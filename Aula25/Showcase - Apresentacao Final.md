# Aula 14 — Showcase: Apresentação Final

## Objetivo

Demonstrar os projetos finais do semestre. Cada grupo apresenta o app completo — front-end, back-end, deploy em produção e documentação — dentro de um formato estruturado que simula uma apresentação técnica real para um time de produto.

---

# 1. O que Este Semestre Construiu

Ao longo das 14 aulas, o projeto evoluiu em camadas:

```
Semestre 1 (base)
  └─ Interface Streamlit/Gradio
  └─ Arquitetura modular (Feature-First)
  └─ Autenticação e estado de sessão

Semestre 2 (evolução)
  └─ Aulas 1-4:  FastAPI separando front do back
  └─ Aulas 5-6:  Observabilidade com LangSmith
  └─ Aula 7:     LangChain orquestrando o pipeline
  └─ Aulas 8-9:  Containerização e deploy gratuito
  └─ Aulas 10-11: Deploy AWS com HTTPS e escalabilidade
  └─ Aulas 12-13: Mobile — PWA e além
```

O projeto final deve evidenciar pelo menos **quatro** dessas camadas funcionando juntas.

---

# 2. Estrutura da Apresentação (20 minutos por grupo)

Cada grupo tem 20 minutos no formato de uma demo técnica real:

**Minuto 0-3 — Problema e solução (sem slides, falando)**
- Qual problema o projeto resolve?
- Para quem?
- Por que IA é parte da solução?

**Minuto 3-10 — Demo ao vivo**
- Abrir o app em produção (URL real, não localhost)
- Mostrar o fluxo principal: o usuário entra, interage, recebe resultado
- Mostrar uma situação de erro e como o front trata elegantemente
- Se tiver mobile: mostrar instalado no celular

**Minuto 10-15 — Arquitetura técnica**
- Mostrar o diagrama de componentes (front, back, modelo, banco, deploy)
- Explicar uma decisão técnica não óbvia que o grupo tomou
- Mostrar um trace no LangSmith de uma chamada real

**Minuto 15-18 — Código que orgulha**
- Um trecho de código que o grupo considera bem resolvido
- Pode ser o tratamento de erro, a chain do LangChain, o Dockerfile, o api_provider

**Minuto 18-20 — Retrospectiva**
- O que funcionou bem?
- O que faria diferente?
- Qual a próxima evolução do projeto?

---

# 3. Critérios de Avaliação

| Critério | Peso | O que é avaliado |
|---|---|---|
| **Front-end funcional** | 20% | App sobe, fluxo principal funciona, erros são tratados com UX adequada |
| **Back-end separado (FastAPI)** | 20% | Provider não está acoplado ao front; API versionada com documentação |
| **Deploy em produção** | 20% | URL pública acessível, HTTPS, variáveis de ambiente sem segredos no código |
| **Observabilidade** | 15% | LangSmith instrumentado; consegue mostrar um trace real no dashboard |
| **Qualidade do código** | 15% | Arquitetura modular, sem código morto, `requirements.txt` limpo |
| **Apresentação** | 10% | Clareza, fluidez da demo, capacidade de responder perguntas técnicas |

---

# 4. Checklist Pré-apresentação

Faça essa verificação no dia anterior:

```
Deploy
  □ URL de produção funcionando (não localhost)
  □ HTTPS ativo (cadeado verde no browser)
  □ App inicia em menos de 10 segundos após a primeira requisição
  □ Secrets configurados na plataforma (não no código)

Código
  □ .gitignore correto (sem .env, sem secrets.toml no repositório)
  □ README no GitHub descreve como rodar o projeto
  □ requirements.txt ou pyproject.toml atualizado
  □ Nenhum print() de debug ou TODO no código principal

Demo
  □ Testou o fluxo completo ao vivo (não só localmente)
  □ Tem um texto/input de exemplo preparado para a demo
  □ Sabe o que mostrar se a API demorar (st.spinner está lá?)
  □ Celular com o PWA instalado (se for mostrar mobile)

Observabilidade
  □ LangSmith aberto em outra aba
  □ Tem um trace recente para mostrar no dashboard
  □ Sabe navegar para o trace de uma chamada específica
```

---

# 5. O que Torna uma Demo Técnica Memorável

Algumas diferenças entre uma apresentação boa e uma excelente:

**Mostre um erro acontecendo — e sendo tratado.**
A maioria das demos só mostra o caminho feliz. Mostrar que você pensou em "o que acontece quando a API está lenta" ou "o que o usuário vê se digitar um texto inválido" demonstra maturidade.

**Fale sobre o que não fez e por quê.**
"Consideramos usar FlutterFlow para mobile mas optamos por PWA porque..." mostra que você avaliou alternativas. Decisões têm contexto — mostrar o contexto é mostrar engenharia, não só código.

**Abra o LangSmith durante a demo.**
Fazer uma requisição ao vivo, abrir o LangSmith na mesma hora e mostrar o trace gerado é o tipo de detalhe que as pessoas se lembram. É concreto, é em tempo real, e demonstra que você monitora o sistema em produção.

**Mostre o Swagger da sua API.**
`/docs` aberto com os endpoints, exemplos e schema Pydantic é a prova de que você separou responsabilidades de verdade. Qualquer cliente conseguiria consumir sua API.

---

# 6. Perguntas Frequentes na Apresentação

Algumas perguntas que avaliadore costumam fazer:

**"Se a API do modelo (Anthropic/OpenAI) ficar fora do ar, o que acontece?"**
Resposta esperada: o fallback tratado no `api_provider.py`, a mensagem de erro que o usuário vê, e (idealmente) um modelo alternativo ou resposta cacheada.

**"Como você saberia se o modelo começou a retornar respostas piores sem você perceber?"**
Resposta esperada: o feedback de like/dislike integrado ao LangSmith, monitoramento de distribuição de sentimentos no dashboard.

**"Qual o custo mensal da sua infraestrutura?"**
Resposta esperada: saiba responder, mesmo que seja "gratuito no HF Spaces com as limitações X". Mostrar que você pensa em custo é maturidade de produto.

**"Se você tivesse mais um sprint, o que faria primeiro?"**
Não existe resposta errada — existe resposta que mostra que você refletiu sobre o produto.

---

# 7. Após o Showcase — O Projeto no Portfólio

Com o projeto em produção e apresentado, você tem o material para um portfólio técnico forte:

**No GitHub:**
- README com badges, overview, arquitetura, getting started, configuração de ambiente
- Link para o app em produção no topo do README
- Print do dashboard LangSmith no README (prova de observabilidade)

**No LinkedIn:**
- Post de lançamento com o link do app, a stack usada e o que o projeto faz
- Adicionar o projeto em "Projetos" no perfil com URL e descrição técnica

**No currículo:**
- "Desenvolveu aplicação de análise de IA com FastAPI + Streamlit, deploy na AWS com Fargate + HTTPS, observabilidade com LangSmith"
- A descrição usa as mesmas palavras que aparecem em vagas de Engenheiro de Machine Learning, ML Engineer e AI Product Developer

---

# Referências

- [Semantic Versioning](https://semver.org)
- [The Twelve-Factor App](https://12factor.net)
- [Google Engineering Practices](https://google.github.io/eng-practices/)
- [Chip Huyen — Machine Learning Interviews Book](https://huyenchip.com/ml-interviews-book/)
