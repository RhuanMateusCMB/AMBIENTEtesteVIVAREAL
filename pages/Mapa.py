import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

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

    # Componente de Busca
    st.markdown("### 🔍 Busca")
    components.declare_component("search_component", path="components/search")
    
    # Componente de Estatísticas
    st.markdown("### 📊 Resumo")
    components.declare_component("stats_summary", path="components/stats")

    # Abas principais
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa", "📋 Lista", "📈 Análise"])

    with tab1:
        # Filtros laterais
        with st.sidebar:
            st.header("Filtros")
            
            preco_range = st.slider(
                "Faixa de Preço (R$)",
                min_value=0,
                max_value=1000000,
                value=(200000, 800000),
                step=50000,
                format="%d"
            )
            
            area_range = st.slider(
                "Área (m²)",
                min_value=0,
                max_value=2000,
                value=(200, 1000),
                step=50
            )
            
            bairros = st.multiselect(
                "Bairros",
                ["Centro", "Precabura", "Jabuti", "Urucunema"],
                default=["Centro"]
            )

        # Mapa
        components.iframe(
            src="https://lookerstudio.google.com/embed/reporting/3eb69112-e085-487f-a9b0-ed395f9248dc/page/oEPdE",
            width=None,
            height=800,
            scrolling=True
        )

    with tab2:
        # Aqui você pode adicionar uma tabela com os dados
        st.dataframe(
            pd.DataFrame({
                'Endereço': ['Rua A', 'Rua B'],
                'Área (m²)': [500, 750],
                'Preço': ['R$ 250.000', 'R$ 375.000']
            }),
            use_container_width=True
        )

    with tab3:
        # Gráficos de análise
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribuição de Preços")
            st.bar_chart({"Preços": [100, 200, 300, 400, 500]})
        
        with col2:
            st.subheader("Concentração por Bairro")
            st.bar_chart({"Bairros": [30, 20, 15, 35]})

    # Rodapé com data de atualização
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0; color: #666;'>
            <p>Desenvolvido com ❤️ por Rhuan Mateus - CMB Capital</p>
            <p style='font-size: 0.8em;'>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
