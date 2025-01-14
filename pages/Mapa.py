import streamlit as st
import streamlit.components.v1 as components

def main():
    # Configuração da página
    st.set_page_config(
        page_title="CMB Capital - Mapa",
        page_icon="🗺️",
        layout="wide"
    )

    # Título e descrição
    st.title("🗺️ Mapa de Terrenos - Eusébio, CE")
    
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <p style='font-size: 1.2em; color: #666;'>
            Visualização geográfica dos terrenos disponíveis em Eusébio
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Incorporar o iframe do Looker Studio
    components.iframe(
        src="https://lookerstudio.google.com/embed/reporting/3eb69112-e085-487f-a9b0-ed395f9248dc/page/oEPdE",
        width=None,  # None fará com que ocupe toda a largura disponível
        height=800,
        scrolling=True
    )

    # Botão para abrir em nova aba
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <p style='font-size: 0.9em; color: #666;'>Preferir ver em tela cheia?</p>
        <a href='https://lookerstudio.google.com/reporting/3eb69112-e085-487f-a9b0-ed395f9248dc' target='_blank'>
            <button style='
                background-color: #FF4B4B;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                margin: 5px 0;
            '>
                🗺️ Abrir Mapa em Nova Aba
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # Rodapé
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: #666;'>
            <p>Desenvolvido com ❤️ por Rhuan Mateus - CMB Capital</p>
            <p style='font-size: 0.8em;'>Última atualização: Janeiro 2025</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
