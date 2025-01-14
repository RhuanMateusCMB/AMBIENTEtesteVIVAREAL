import streamlit as st
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

    # Barra de busca usando componente nativo do Streamlit
    st.text_input("🔍 Buscar por endereço, bairro ou características...", placeholder="Digite sua busca aqui...")

    # Métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Terrenos", "127", "↑ 12%")
    with col2:
        st.metric("Preço Médio/m²", "R$ 450,00", "↓ 5%")
    with col3:
        st.metric("Área Total Disponível", "25.000 m²", "↑ 8%")

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

            st.button("Aplicar Filtros", type="primary")

        # Mapa
        st.components.v1.iframe(
            src="https://lookerstudio.google.com/embed/reporting/3eb69112-e085-487f-a9b0-ed395f9248dc/page/oEPdE",
            width=None,
            height=800,
            scrolling=True
        )

    with tab2:
        # Tabela de dados
        exemplo_dados = pd.DataFrame({
            'Endereço': ['Rua A, Centro', 'Rua B, Precabura', 'Rua C, Jabuti'],
            'Área (m²)': [500, 750, 600],
            'Preço': ['R$ 250.000', 'R$ 375.000', 'R$ 300.000'],
            'Preço/m²': ['R$ 500', 'R$ 500', 'R$ 500'],
            'Bairro': ['Centro', 'Precabura', 'Jabuti']
        })
        
        st.dataframe(
            exemplo_dados,
            use_container_width=True,
            hide_index=True
        )

    with tab3:
        # Gráficos de análise
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribuição de Preços")
            chart_data = pd.DataFrame({
                'Faixa de Preço': ['200-300k', '300-400k', '400-500k', '500k+'],
                'Quantidade': [10, 15, 8, 5]
            })
            st.bar_chart(chart_data, x='Faixa de Preço', y='Quantidade')
        
        with col2:
            st.subheader("Concentração por Bairro")
            bairro_data = pd.DataFrame({
                'Bairro': ['Centro', 'Precabura', 'Jabuti', 'Urucunema'],
                'Quantidade': [30, 20, 15, 35]
            })
            st.bar_chart(bairro_data, x='Bairro', y='Quantidade')

    # Download dos dados
    st.download_button(
        label="📥 Baixar dados em CSV",
        data=exemplo_dados.to_csv(index=False).encode('utf-8-sig'),
        file_name=f'terrenos_eusebio_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )

    # Rodapé
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0; color: #666;'>
            <p>Desenvolvido com ❤️ por Rhuan Mateus - CMB Capital</p>
            <p style='font-size: 0.8em;'>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
