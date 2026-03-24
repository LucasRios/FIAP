# 📰 AI News Analyzer

O **AI News Analyzer** é uma plataforma educativa e funcional para análise de notícias em tempo real. Ele utiliza técnicas de Processamento de Linguagem Natural (NLP) para extrair, resumir e classificar o sentimento de artigos da web.

Este projeto foi estruturado de forma modular para facilitar o aprendizado sobre arquitetura de sistemas Python e pipelines de dados.

---

## 🛠️ Tecnologias e Requisitos

* **Linguagem:** [Python 3.12+](https://www.python.org/)
* **Interface:** [Streamlit](https://streamlit.io/)
* **Dados:** [Pandas](https://pandas.pydata.org/)
* **NLP:** Bibliotecas de processamento local (TensorFlow/Keras/NLTK)

---

## 📂 Estrutura do Projeto

* `app.py`: O ponto de entrada que orquestra a navegação.
* `pipelines/`: Onde ocorre o fluxo de dados (Extração -> Limpeza -> IA).
* `features/`: Interface visual dividida por funcionalidades (Análise, Histórico, Configurações).
* `state/`: Gerenciamento de memória e variáveis de sessão.
* `providers/`: Motores de IA e lógica analítica.

---

## 📥 Instalação (Passo a Passo)

### 1. Clonar o repositório
```bash
git clone
cd gestaomax-news-analyzer
```

### 2. Configurar o Ambiente Virtual

É altamente recomendado o uso de um ambiente virtual para evitar conflitos de versões (especialmente com Python 3.12/3.14):

```bash
# Criar o ambiente
python -m venv venv

# Ativar (Windows)
.\venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

---

## 🖥️ Como Rodar

Para iniciar o servidor local de desenvolvimento, execute:

```bash
streamlit run app.py
```

O sistema estará disponível em http://localhost:8501.

---

## ☁️ Publicação no Streamlit Cloud

Para colocar sua ferramenta online para o mundo:

1. Dê Push do seu código para um repositório no GitHub.
2. Acesse https://share.streamlit.io e conecte sua conta.
3. Clique em "New app" e selecione o repositório do projeto.
4. No campo "Main file path", aponte para app.py.
5. Clique em "Deploy".

---

## 👨‍🏫 Guia de Implementaçãos

- Observar o app.py: Veja como o roteamento é feito de forma limpa sem misturar lógica de UI com lógica de negócio.
- Entender o Pipeline: No arquivo pipelines/news_pipeline.py, observe como os dados são validados com .empty antes de seguir para a próxima etapa.
- Comentários: Todo o código foi extensivamente comentado para que você possa seguir a execução linha por linha.
