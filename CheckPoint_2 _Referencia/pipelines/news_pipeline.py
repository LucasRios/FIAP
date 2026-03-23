# =============================================================================
# ARQUIVO: pipelines/news_pipeline.py
# =============================================================================
# Responsabilidade: Orquestrar o fluxo de processamento de dados (ETL).
# ETL significa: Extract (Extrair), Transform (Transformar) e Load (Carregar).
# Este arquivo conecta as funções de baixo nível do provedor de NLP com 
# a interface visual do Streamlit.
# =============================================================================

# Importamos as funções especializadas do nosso "Provedor" de inteligência artificial.
# etapa_1: Busca a notícia na web.
# etapa_2: Limpa o texto (remove HTML, anúncios, etc).
# etapa_analise_local: Aplica os modelos de IA para resumo e sentimento.
from providers.NLP_Sentimentos_Resumo_Analitico import (
    etapa_1_coleta, 
    etapa_2_preparacao, 
    etapa_analise_local
)

def analyze_news(url: str):
    """
    Função principal que orquestra o fluxo de dados. 
    Recebe uma URL (string) e retorna um dicionário estruturado ou None.
    """
    
    # -------------------------------------------------------------------------
    # 1. COLETA (EXTRAÇÃO)
    # -------------------------------------------------------------------------
    # Enviamos a URL dentro de uma lista [url] para a função de coleta.
    # df_bruto é um DataFrame do Pandas contendo o que foi baixado do site.
    df_bruto = etapa_1_coleta([url])
    
    # Validação de segurança: Se a coleta falhou (URL inválida ou site bloqueado),
    # interrompemos o processo aqui para evitar erros no código seguinte.
    if df_bruto.empty:
        return None

    # -------------------------------------------------------------------------
    # 2. LIMPEZA E PREPARAÇÃO (TRANSFORMAÇÃO)
    # -------------------------------------------------------------------------
    # O texto bruto de um site vem com "sujeira". Esta etapa isola apenas 
    # o corpo do texto da notícia, tratando pontuação e caracteres especiais.
    df_final = etapa_2_preparacao(df_bruto)

    # -------------------------------------------------------------------------
    # 3. ANÁLISE (IA E PROCESSAMENTO)
    # -------------------------------------------------------------------------
    if not df_final.empty:
        # Aqui a mágica acontece: o modelo de NLP lê o texto limpo e gera:
        # - Um resumo automático.
        # - A polaridade (positivo/negativo).
        # - A distribuição de confiança dos sentimentos.
        resultado_analise = etapa_analise_local(df_final)
        
        # ---------------------------------------------------------------------
        # 4. FORMATAÇÃO DO CONTRATO (RETORNO)
        # ---------------------------------------------------------------------
        # Não retornamos o DataFrame bruto para a UI.
        # Criamos um "Dicionário de Resposta" limpo. Isso separa a lógica de dados
        # da lógica de visualização. Se mudarmos a IA no futuro, a UI nem percebe.
        return {
            "article": df_final.iloc[0]['texto_bruto'],  # Texto original completo
            "summary": resultado_analise['summary'],      # Resumo gerado pela IA
            "sentiment": {
                "label": resultado_analise['overall_sentiment'], # Ex: "Positivo"
                "score": resultado_analise['polarity_val'],      # Valor numérico da análise
                "distribution": resultado_analise['distribution'], # Dados para gerar gráficos
                # Lógica visual simples: escolhe o emoji baseado no texto do sentimento
                "emoji": "😊" if resultado_analise['overall_sentiment'] == "Positivo" else "😐"
            }
        }
    
    # Se algo falhou no meio do caminho, retornamos Nada (None)
    return None