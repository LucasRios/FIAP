#exemplo de um script estático para simular a avaliação de um modelo de IA, onde temos uma função que retorna métricas de avaliação como precisão e perda. O script inclui um atraso para simular o tempo de inferência e imprime os resultados no console.
import random
import time

def avaliar():
    time.sleep(1)  # simula inferência
    return {"accuracy": random.uniform(0.6, 0.98),
            "loss": random.uniform(0.1, 0.6)}

if __name__ == "__main__":
    print("Avaliando modelo...")
    m = avaliar()
    print("accuracy:", m["accuracy"])
    print("loss:", m["loss"])

 
#importa o streamLit para podermos seguir com a programação normal  
import streamlit as st

# Configuração da página (Isso define o comportamento no browser)
st.set_page_config(page_title="Minha IA", layout="wide",initial_sidebar_state="expanded", page_icon="🤖",menu_items={
          'Get Help': 'https://www.extremelycoolapp.com/help',
          'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "# This is a header. This is an *extremely* cool app!"
     })

st.title("Construindo Interfaces com IA")

#1 - Comece pensando nas abas paa organizar as informações em seus contextos
tab_home, tab_metricas = st.tabs(["Início", "Métricas"])

#com a primeira tab comece a pensar sobre o input e output
with tab_home:
    #2 - Dentro da primeira tab, pense em colunas. É interessante separar em colunas o que preciso pedir? ou melhor manter em uma lista inteira?
    col_input, col_preview = st.columns([1, 1]) # Proporção das colunas
    
    with col_input:
      #3 - a partir da coluna, pense nas linhas, nas informações que você precisa pedir ou apresentar
        st.subheader("Entrada")
        upload = st.file_uploader("Suba uma imagem para análise", type=["jpg", "png"])
        prompt = st.text_area("O que a IA deve procurar?")
        botao = st.button("Analisar Agora")

    with col_preview:
        st.subheader("Saída da IA")
        if botao:
            st.success("Processamento concluído!")
            # Simulação de saída
            st.image("https://via.placeholder.com/400", caption="Resultado da Detecção")

with tab_metricas:
    #Métricas de Contexto
    st.subheader("Métricas do Modelo")
    m1, m2, m3 = st.columns(3)
    m1.metric("Precisão", "92%", "+1.5%")
    m2.metric("Tempo de Resposta", "0.8s", "-0.2s")
    m3.metric("Uso de Memória", "450MB")