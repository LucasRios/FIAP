# Autenticação, Estado e Navegação por Perfil no Streamlit

Até aqui, a aplicação construída funciona bem como protótipo. No entanto, ainda não resolve um problema essencial de qualquer sistema real: controle de acesso. Nesta aula, a proposta é evoluir a aplicação para um cenário mais próximo de produto, introduzindo autenticação, persistência de sessão e navegação baseada no perfil do usuário.

A ideia central é simples: diferentes usuários devem enxergar diferentes partes do sistema. Para isso, vamos implementar um fluxo completo de login e, a partir dele, controlar o que é exibido na interface.

---

## Arquitetura do Projeto

A estrutura do projeto permanece a mesma, reforçando um ponto importante: não é necessário mudar a arquitetura para adicionar autenticação, apenas evoluí-la.

```
📂 projeto_streamlit/
├── 📂 provider/        # Lógica de autenticação e dados
├── 📂 ui/              # Componentes de interface (Login, Dashboards)
├── 📂 feature/         # Lógicas específicas de cada tela
├── 📂 pipeline/        # Processamento de dados (opcional)
└── 📄 app.py           # Orquestrador principal e roteamento
```

Essa separação continua sendo essencial. A autenticação fica no `provider`, a interface no `ui`, e o `app.py` continua sendo responsável apenas por decidir o fluxo da aplicação. Esse padrão evita acoplamento e facilita evolução futura, como trocar o login mockado por uma API real.

---

## Como o Streamlit se comporta (e por que isso importa)

Um ponto crítico para entender essa aula é o funcionamento interno do Streamlit. Diferente de frameworks tradicionais, ele não mantém estado automaticamente entre interações. A cada clique, input ou ação do usuário, o script inteiro é executado novamente do zero.

Isso significa que, sem algum mecanismo de persistência, qualquer informação — inclusive o login — seria perdida imediatamente.

É aqui que entra o `st.session_state`. Ele funciona como uma memória isolada por usuário (na prática, por aba do navegador). Tudo o que for salvo ali permanece disponível entre execuções do script.

Ao fazer login, salvamos três informações principais:

- se o usuário está autenticado  
- qual é o perfil dele  
- qual é o nome do usuário  

Esses dados passam a guiar toda a renderização da aplicação.

Outro ponto importante é o uso do `st.rerun()`. Quando o login acontece, o estado muda, mas a interface ainda está “presa” à execução anterior. O `rerun` força uma nova execução imediata, garantindo que a aplicação leia o novo estado e renderize a interface correta.

Sem isso, o usuário faria login, mas continuaria vendo a tela antiga até interagir novamente.

---

## Controle de acesso (RBAC na prática)

O conceito aplicado aqui é o de RBAC (Role-Based Access Control). Em vez de controlar permissões diretamente por usuário, associamos cada usuário a um papel (role), e esse papel define o que ele pode acessar.

No exemplo da aula, temos dois perfis:

- `user` → acesso básico  
- `admin` → acesso completo  

Esse modelo é amplamente utilizado em sistemas reais porque simplifica a gestão de permissões. Em vez de configurar acesso individual, basta definir regras por perfil.

No código, isso aparece de forma simples, mas poderosa: o menu lateral é construído dinamicamente com base no perfil do usuário. Se o usuário for admin, novas opções são adicionadas. Caso contrário, elas simplesmente não existem para ele.

---

## Implementação

### Provider de autenticação

O `provider` centraliza a lógica de validação. Isso é importante porque evita espalhar regras de negócio pela interface.

```python
import streamlit as st

def login(username, password):
    # Simulação de base de dados (Em produção, aqui seria uma consulta ao banco ou API)
    users = {
        "admin": {"password": "123", "role": "admin"},
        "aluno": {"password": "456", "role": "user"}
    }

    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def logout():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()
```

Aqui estamos simulando um banco de dados com um dicionário. O ponto relevante não é a implementação em si, mas a separação de responsabilidade. Em um cenário real, essa função poderia facilmente ser substituída por uma chamada a API ou banco sem impactar o restante da aplicação.

---

### Interface de login

A interface é responsável apenas por capturar os dados do usuário e reagir ao resultado da autenticação.

```python
import streamlit as st
from provider.auth_provider import login

def show_login():
    st.subheader("Acesso ao Sistema de IA")

    with st.form("login_form"):
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            role = login(user, pw)
            if role:
                st.session_state.logged_in = True
                st.session_state.user_role = role
                st.session_state.username = user
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
```

O uso de `st.form` evita reexecuções desnecessárias enquanto o usuário digita. A validação só acontece no momento do submit, o que deixa o fluxo mais previsível.

Quando o login é bem-sucedido, os dados são armazenados no `session_state`, e o `rerun` garante a transição imediata para a área logada.

---

### Orquestração e roteamento

O `app.py` continua sendo o ponto central da aplicação. Ele não implementa regras de negócio nem UI detalhada — apenas decide o fluxo.

```python
import streamlit as st
from ui.login_ui import show_login
from provider.auth_provider import logout

# 1. Configuração da Página
st.set_page_config(page_title="FIAP - IA Platform", layout="wide")

# 2. Inicialização do Estado de Sessão
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def main():
    # Roteamento Principal
    if not st.session_state.logged_in:
        show_login()
    else:
        render_app()

def render_app():
    # Sidebar Customizada por Perfil
    st.sidebar.title(f"Olá, {st.session_state.username}")
    role = st.session_state.user_role

    # Menu Comum
    menu = ["Home", "Análise de Dados"]

    # Menu Restrito (RBAC)
    if role == "admin":
        menu.append("Gestão de Modelos")
        menu.append("Logs do Sistema")

    choice = st.sidebar.selectbox("Navegação", menu)

    if st.sidebar.button("Sair"):
        logout()

    # Renderização das Telas
    st.title(f"Área: {choice}")

    if choice == "Home":
        st.write("Bem-vindo ao portal de inteligência artificial.")

    elif choice == "Análise de Dados":
        st.info("Tela visível para todos os usuários logados.")

    elif choice == "Gestão de Modelos":
        st.warning("Atenção: Esta tela é exclusiva para ADMINISTRADORES.")
        st.write("Configurações de Hiperparâmetros e Retreinamento.")

if __name__ == "__main__":
    main()
```

O fluxo aqui é direto: se não está logado, mostra login. Se está, renderiza a aplicação. A função `render_app` constrói a interface com base no perfil, garantindo que o usuário veja apenas o que pode acessar.

---

## O que realmente está acontecendo

Mesmo parecendo simples, o fluxo envolve uma sequência importante:

1. O usuário acessa a aplicação  
2. O estado indica que ele não está logado  
3. A tela de login é exibida  
4. Ele envia as credenciais  
5. O provider valida  
6. O estado é atualizado  
7. O `rerun` dispara uma nova execução  
8. A aplicação agora entende que ele está autenticado  
9. A interface muda completamente  

Esse comportamento é a base para qualquer aplicação interativa no Streamlit.

---

## Limitações importantes

Esse modelo funciona muito bem para aprendizado, mas não é adequado para produção. As senhas estão em texto puro, não há criptografia, não existe controle de sessão real, nem integração com backend.

O objetivo aqui é ensinar o fluxo e a arquitetura, não segurança.

---

## Evolução natural

A partir desse ponto, a aplicação já pode evoluir para algo mais próximo de mercado:

- substituir o dicionário por banco de dados  
- usar hash de senha  
- integrar com APIs de autenticação  
- implementar tokens (JWT)  
- controlar expiração de sessão  

---

## Insight final

O principal aprendizado não é o login em si, mas entender como o Streamlit pode ser usado para controlar fluxo de aplicação. Quando se domina `session_state` e `rerun`, deixa de ser apenas um script interativo e passa a ser possível construir aplicações completas, com comportamento semelhante a sistemas web tradicionais.

Essa é a mudança de nível: de interface simples para aplicação com regras, estado e controle de acesso.
