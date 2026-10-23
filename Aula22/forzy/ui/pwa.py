# =============================================================================
# ui/pwa.py — Liga o app Streamlit ao PWA (quando ele é o dono da página)
#
# Funciona quando o Streamlit serve a página principal: rodando localmente,
# no Render ou num servidor próprio. No Streamlit Community Cloud, o app roda
# dentro de um iframe da página da plataforma; para esse caso existe a
# "casca" (python -m pwa.gerar casca URL_DO_APP).
#
# Dois recursos PÚBLICOS do Streamlit sustentam esta camada:
#   - server.enableStaticServing   serve a pasta static/ em /app/static/
#                                  (manifesto e ícones, gerados por
#                                  `python -m pwa.gerar streamlit`);
#   - st.html(..., unsafe_allow_javascript=True)   executa o script que
#                                  escreve o link do manifesto no <head>.
#
# O limite: sem service worker. Um service worker só controla páginas DENTRO
# da pasta de onde é servido; servido de /app/static/, ele nunca alcançaria a
# página do app, que fica em /. O app é instalável e abre em janela própria,
# mas não tem página offline.
# =============================================================================

from pathlib import Path

import streamlit as st

from pwa.gerar import cabecalho_html

_PREFIXO = "/app/static/"
_PRONTO = (Path(__file__).parent.parent / "static" / "manifest.webmanifest").exists()


def ativar_pwa() -> None:
    """Injeta o manifesto, os ícones do iOS e a cor da barra. Sem efeito se os arquivos não foram gerados."""
    if not _PRONTO:
        return
    # O script vem de pwa/gerar.py e não contém nenhum dado do usuário: é o
    # único uso de unsafe_allow_javascript do projeto.
    st.html(cabecalho_html(prefixo=_PREFIXO, registrar_sw=False,
                           link_manifesto=f"{_PREFIXO}manifest.webmanifest"),
            unsafe_allow_javascript=True)
