import streamlit as st
import pandas as pd
import numpy as np
import time
import requests

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(
    page_title="Cache & Conectividade",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ==========================================================
# HEADER
# ==========================================================
st.markdown("# Aula — Caching & Conectividade") 
 
# ==========================================================
# TABS
# ==========================================================
tab_cache, tab_api = st.tabs([
    "01 · Cache de Dados",
    "02 · Cache + Conectividade",
])


# ##########################################################
# TAB 1 — CACHE DE DADOS
# ##########################################################
with tab_cache:

    st.markdown("### Carregamento de dataset pesado")
    st.caption(
        "Simula um CSV de 500 000 linhas com 2 s de latência de I/O. " 
    )
    st.markdown("")

    # ----------------------------------------------------------
    # Funções: com e sem cache
    # ----------------------------------------------------------

    # COM cache — resultado armazenado após a primeira execução
    @st.cache_data  
    def carregar_com_cache(numero_linhas) -> pd.DataFrame:  
        time.sleep(2)                          
        rng = np.random.default_rng(42)        # Cria um gerador de números aleatórios com semente (seed) 42 para resultados replicáveis
        n = numero_linhas                      
        return pd.DataFrame({                  # Cria e retorna um objeto DataFrame do Pandas com as colunas abaixo:
            "id":        np.arange(n),         # Cria uma sequência numérica de 0 até n-1
            "valor":     rng.uniform(0, 1_000, n).round(2), # Gera 'n' números reais entre 0 e 1000 com 2 casas decimais
            "categoria": rng.choice(["A", "B", "C", "D"], n), # Escolhe aleatoriamente 'n' categorias da lista fornecida
            "score":     rng.normal(50, 15, n).round(2), # Gera 'n' números seguindo uma distribuição normal (média 50, desvio 15)
        })

    # SEM cache — recalcula sempre
    def carregar_sem_cache(numero_linhas) -> pd.DataFrame:
        time.sleep(2)                          # simula I/O lento
        rng = np.random.default_rng(42)
        n = numero_linhas
        return pd.DataFrame({
            "id":        np.arange(n),
            "valor":     rng.uniform(0, 1_000, n).round(2),
            "categoria": rng.choice(["A", "B", "C", "D"], n),
            "score":     rng.normal(50, 15, n).round(2),
        })

    # ----------------------------------------------------------
    # Controles
    # ----------------------------------------------------------
    numero_linhas = st.number_input(
            "Número de linhas (simulado)",
            value=500_000,
            step=100_000,
            min_value=100_000,
            max_value=1_000_000 
        )
    
    col_a, col_b, col_c, _  = st.columns([1, 1, 1 ,3 ])

    with col_a:
        run_com = st.button("Carregar com cache")
    with col_b:
        run_sem = st.button("Carregar sem cache")
    with col_c:        
        if st.button("Limpar cache"):
            st.cache_data.clear()
            st.toast("Cache limpo", icon="🗑️")        

    st.markdown("")

    # ----------------------------------------------------------
    # Execução COM cache
    # ----------------------------------------------------------
    if run_com:
        t0 = time.perf_counter()
 
        with st.spinner("Carregando dataset..."):
            df = carregar_com_cache(numero_linhas)

        elapsed = time.perf_counter() - t0 
 
        st.markdown(f"Execução com Cache:  `{elapsed:.4f}s`" )
 
        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Linhas", f"{len(df):,}")
        m2.metric("Colunas", len(df.columns))
        m3.metric("Tempo", f"{elapsed:.4f} s")
        m4.metric("Tamanho", f"{df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

        st.markdown("")
        st.caption("head(10) do dataset")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    # ----------------------------------------------------------
    # Execução SEM cache
    # ----------------------------------------------------------
    if run_sem:
        t0 = time.perf_counter()

        with st.spinner("Carregando dataset (sem cache)..."): 
            df = carregar_sem_cache(numero_linhas)

        elapsed = time.perf_counter() - t0

        st.markdown(f"Execução sem Cache:  `{elapsed:.4f}s`" )
        st.caption("Sem cache: 2 s de I/O toda vez, independente de quantas vezes executar.")
        st.markdown("")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Linhas", f"{len(df):,}")
        m2.metric("Colunas", len(df.columns))
        m3.metric("Tempo", f"{elapsed:.4f} s")
        m4.metric("Tamanho", f"{df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

        st.markdown("")
        st.caption("head(10) do dataset")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    if not run_com and not run_sem:
        st.info("Clique em um dos botões acima para iniciar a comparação.")


# ##########################################################
# TAB 2 — CACHE + CONECTIVIDADE (PokéAPI)
# ##########################################################
with tab_api:

    st.markdown("### Cache em chamadas externas — PokéAPI")
    st.caption(
        "Cada chamada à API tem latência de rede real (~200–600 ms). "
        "Com cache, execuções posteriores são instantâneas."
    )

    # ----------------------------------------------------------
    # Secrets — configuração centralizada
    # ----------------------------------------------------------
    #   [pokeapi]
    #   base_url  = "https://pokeapi.co/api/v2"
    #   cache_ttl = 300

    POKE_BASE = st.secrets["pokeapi"]["base_url"]
    CACHE_TTL  = st.secrets["cache_ttl"]

    st.markdown(
        f"`base_url = \"{POKE_BASE}\"` &nbsp;·&nbsp; "
        f"`cache_ttl = {CACHE_TTL}s`",
        unsafe_allow_html=True,
    )
    st.markdown("")

    # ----------------------------------------------------------
    # Função cacheada com TTL vindo dos secrets
    # ----------------------------------------------------------
    @st.cache_data(ttl=CACHE_TTL)
    def buscar_pokemon(nome: str) -> dict:
        """Chama a PokéAPI e retorna dados do Pokémon."""
        url = f"{POKE_BASE}/pokemon/{nome.lower().strip()}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return resp.json()

    # ----------------------------------------------------------
    # Input
    # ----------------------------------------------------------
    col_in, col_btn, col_clr, _ = st.columns([2, 1, 1, 2])

    with col_in:
        nome = st.text_input(
            "Nome Pokémon",
            value="pikachu",
            label_visibility="collapsed",
            placeholder="pikachu, charizard, 25...",
        )
    with col_btn:
        buscar = st.button("Buscar")
    with col_clr:
        if st.button("Limpar"):
            st.cache_data.clear()
            st.toast("Cache de API limpo.", icon="🗑️")

    st.markdown("")

    # ----------------------------------------------------------
    # Busca + exibição
    # ----------------------------------------------------------
    if buscar and nome:
        t0 = time.perf_counter()

        try:
            with st.spinner(f"Consultando PokéAPI → /{nome.lower()}..."):
                data = buscar_pokemon(nome)

            elapsed = time.perf_counter() - t0

            st.markdown(f"Execução com Cache:  `{elapsed:.4f}s`")
            st.markdown("")

            st.json(data, expanded=False)

            # Layout: imagem + dados
            img_col, info_col = st.columns([1, 2])

            with img_col:
                sprite = data["sprites"]["other"]["official-artwork"]["front_default"]
                if sprite:
                    st.image(sprite, width=220)

            with info_col:
                nome_display = data["name"].upper()
                st.markdown(f"### `{nome_display}` · #{data['id']:04d}")

                tipos = " · ".join(
                    f"`{t['type']['name'].upper()}`" for t in data["types"]
                )
                st.markdown(f"**Tipo:** {tipos}")

                # Stats como DataFrame
                stats_df = pd.DataFrame([
                    {"stat": s["stat"]["name"], "base": s["base_stat"]}
                    for s in data["stats"]
                ])

                st.dataframe(
                    stats_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "stat": st.column_config.TextColumn("Atributo"),
                        "base": st.column_config.ProgressColumn(
                            "Base", min_value=0, max_value=255, format="%d"
                        ),
                    },
                )

                # Métricas rápidas
                ma, mb, mc = st.columns(3)
                ma.metric("Altura", f"{data['height'] / 10} m")
                mb.metric("Peso",   f"{data['weight'] / 10} kg")
                mc.metric("Tempo",  f"{elapsed:.4f} s")

        except requests.exceptions.HTTPError as e:
            st.error(f"Pokémon não encontrado: `{nome}` — {e}")
        except Exception as e:
            st.error(f"Erro de conexão: {e}")

    elif not buscar:
        st.info(
            "Digite o nome ou ID de um Pokémon e clique em **Buscar**. "
            "Execute duas vezes para ver o cache em ação."
        )