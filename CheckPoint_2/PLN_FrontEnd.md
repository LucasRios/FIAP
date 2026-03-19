# Checkpoint 2 --- Projeto Integrado de Front-end e PLN

**Curso:** Tecnólogo em Inteligência Artificial --- FIAP

**Disciplinas envolvidas:** - Front-end\
- Processamento de Linguagem Natural (PLN)

------------------------------------------------------------------------

## 1. Contexto do desafio

Neste checkpoint, os grupos deverão desenvolver uma aplicação com
interface web capaz de apoiar a análise de conteúdo jornalístico a
partir de técnicas de Processamento de Linguagem Natural.

A proposta integra conhecimentos das duas disciplinas envolvidas no
semestre. A aplicação deverá permitir que o usuário obtenha ou informe
uma notícia, processe esse conteúdo com apoio de modelos de linguagem e
apresente os resultados em uma interface organizada, funcional e
modular.

O projeto deverá contemplar, no mínimo, três capacidades principais:

1.  Buscar ou receber uma notícia\
2.  Realizar análise de sentimento sobre a notícia\
3.  Gerar um resumo do conteúdo

Além disso, a aplicação deverá ser construída seguindo princípios de
arquitetura e separação de responsabilidades, com organização adequada
dos arquivos, módulos e componentes, conforme trabalhado na disciplina
de Front-end.

------------------------------------------------------------------------

## 2. Objetivo

Desenvolver uma aplicação interativa que demonstre a integração entre
interface web e processamento de linguagem natural, permitindo ao
usuário analisar notícias de forma automatizada e visualmente clara.

O projeto deve evidenciar que o grupo é capaz de:

-   construir uma interface utilizável;\
-   estruturar a aplicação em módulos;\
-   integrar a interface com funções de PLN;\
-   processar texto de notícia;\
-   exibir resultados de forma clara e organizada.

------------------------------------------------------------------------

## 3. Desafio proposto

Cada grupo deverá desenvolver uma aplicação em Python com interface web
que permita ao usuário:

### Etapa 1 --- Entrada da notícia

A aplicação deve permitir ao usuário escolher uma das abordagens abaixo:

-   informar a URL de uma notícia, ou\
-   colar diretamente o texto da notícia, ou\
-   implementar uma opção de busca de notícia a partir de tema, termo ou
    palavra-chave.

**Observação:** a forma de entrada pode variar conforme a estratégia
adotada pelo grupo, mas a aplicação precisa trabalhar com conteúdo
jornalístico textual.

### Etapa 2 --- Processamento em PLN

Após obter o conteúdo da notícia, a aplicação deverá:

-   realizar análise de sentimento do texto;\
-   gerar um resumo automático da notícia.

### Etapa 3 --- Exibição dos resultados

A interface deverá apresentar, de forma clara:

-   título ou identificação da notícia;\
-   texto original ou trecho processado;\
-   resultado da análise de sentimento;\
-   resumo gerado;\
-   elementos de organização visual que facilitem a leitura dos
    resultados.

------------------------------------------------------------------------

## 4. Requisitos técnicos

### 4.1. Requisitos de Front-end

A aplicação deverá demonstrar os conceitos trabalhados na disciplina de
Front-end, especialmente:

-   organização do projeto em arquitetura modular;\
-   separação de responsabilidades entre interface, lógica e
    processamento;\
-   separação adequada de pastas e arquivos;\
-   uso dos componentes já trabalhados em aula até o CP1;\
-   construção de uma interface coerente, funcional e compreensível.

**Estrutura mínima esperada:**

-   arquivo principal da interface;\
-   módulo(s) de lógica de negócio;\
-   módulo(s) de integração com o processamento de PLN;\
-   pasta(s) auxiliares para utilidades, dados ou serviços.

### 4.2. Requisitos de PLN

A aplicação deverá demonstrar integração com técnicas e recursos de PLN
para:

-   tratar ou receber o texto da notícia;\
-   executar análise de sentimento;\
-   gerar resumo do conteúdo;\
-   retornar os resultados à interface.

O grupo poderá escolher a abordagem técnica mais adequada, desde que
consiga demonstrar o funcionamento da solução.

**Exemplos de possibilidades:**

-   uso de bibliotecas de PLN;\
-   uso de modelos prontos;\
-   uso de APIs;\
-   uso de pipelines simplificados para classificação e sumarização.

O importante é que o grupo consiga mostrar claramente:

-   o que entra;\
-   como o texto é processado;\
-   o que sai como resultado.

------------------------------------------------------------------------

## 5. Entregáveis

### 5.1. Código-fonte

Repositório ou pacote do projeto contendo todos os arquivos necessários
para execução.

### 5.2. Aplicação funcional

A aplicação deve estar executável localmente ou em ambiente acessível ao
professor.

### 5.3. Documento breve de apoio

Um arquivo simples em PDF ou Markdown contendo:

-   nome dos integrantes;\
-   descrição da proposta;\
-   arquitetura adotada;\
-   tecnologias utilizadas;\
-   instruções de execução;\
-   limitações conhecidas;\
-   divisão resumida de responsabilidades do grupo.

### 5.4. Evidências de funcionamento

Inserir prints de tela ou pequeno vídeo demonstrando:

-   entrada da notícia;\
-   processamento;\
-   resultado da análise de sentimento;\
-   resumo gerado.

------------------------------------------------------------------------

## 6. Critérios de avaliação

### 6.1. Critérios de Front-end

**a) Organização arquitetural**\
Avalia a separação de responsabilidades, modularização e clareza
estrutural do projeto.

**b) Qualidade da interface**\
Avalia usabilidade, clareza visual, organização dos elementos e
coerência da navegação.

**c) Uso adequado dos componentes**\
Avalia se o grupo aplicou corretamente os recursos e componentes
trabalhados em aula.

### 6.2. Critérios de PLN

**d) Obtenção e tratamento da notícia**\
Avalia se a aplicação consegue receber ou buscar o conteúdo de forma
consistente.

**e) Análise de sentimento**\
Avalia se a funcionalidade foi implementada corretamente e se o
resultado é apresentado de forma compreensível.

**f) Resumo da notícia**\
Avalia a capacidade da solução de sintetizar o conteúdo de forma útil e
inteligível.

### 6.3. Critérios integradores

**g) Integração entre interface e processamento**\
Avalia se Front e PLN funcionam de forma conectada e coerente.

**h) Funcionamento geral da solução**\
Avalia estabilidade, execução e qualidade final do projeto.

------------------------------------------------------------------------

## 7. Regras e orientações

-   O trabalho poderá ser realizado em grupo, conforme orientação da
    turma.\
-   A aplicação deve estar funcional no momento da correção.\
-   O grupo deve deixar claro o que foi desenvolvido por ele e o que foi
    adaptado de bibliotecas, exemplos ou modelos prontos.\
-   O uso de ferramentas de IA para apoio ao desenvolvimento é
    permitido, desde que o grupo compreenda e consiga explicar o que foi
    implementado.\
-   Projetos sem organização arquitetural mínima poderão ter desconto
    relevante na parte de Front-end.\
-   Projetos sem integração real entre interface e PLN não atenderão ao
    objetivo do checkpoint.

------------------------------------------------------------------------

## 8. Diferenciais que podem melhorar a avaliação

Itens não obrigatórios, mas que podem enriquecer a entrega:

-   histórico das notícias analisadas;\
-   comparação entre mais de uma notícia;\
-   exibição de score de sentimento;\
-   filtros por tema;\
-   tratamento de erros;\
-   layout mais refinado;\
-   opção de exportar resultados;\
-   comparação entre abordagens de resumo ou sentimento.

------------------------------------------------------------------------

## 9. Prazo de entrega

**☞ 05/04/2026 às 23h59 ☜**

------------------------------------------------------------------------

## 10. Síntese do que será esperado do aluno

Ao final, o grupo deverá entregar uma aplicação que:

-   trabalhe com notícias;\
-   faça análise de sentimento;\
-   gere resumo;\
-   tenha uma interface web funcional;\
-   esteja organizada em arquitetura modular;\
-   demonstre claramente a integração entre Front-end e PLN.
