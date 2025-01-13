import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client

# Configuração da página
st.set_page_config(
    page_title="Mapa de Terrenos - CMB Capital",
    page_icon="🗺️",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

class SupabaseManager:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase = create_client(self.url, self.key)

    def obter_dados(self):
        try:
            response = self.supabase.table('teste').select('*').execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao obter dados: {str(e)}")
            return pd.DataFrame()

def criar_mapa(df):
    # Centralizar o mapa em Eusébio
    mapa = folium.Map(
        location=[-3.8928, -38.4559],
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    # Adicionar marcadores para cada terreno
    for idx, row in df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            # Criar popup com informações do terreno
            popup_html = f"""
                <div style='width: 200px'>
                    <h4>{row['titulo']}</h4>
                    <p><b>Área:</b> {row['area_m2']:,.2f} m²</p>
                    <p><b>Preço:</b> R$ {row['preco_real']:,.2f}</p>
                    <p><b>Preço/m²:</b> R$ {row['preco_m2']:,.2f}</p>
                    <p><b>Endereço:</b> {row['endereco']}</p>
                    <a href='{row['link']}' target='_blank'>Ver no site</a>
                </div>
            """
            
            # Adicionar marcador
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"R$ {row['preco_real']:,.2f}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(mapa)

    return mapa

def main():
    # Título
    st.title("🗺️ Mapa de Terrenos - Eusébio, CE")
    
    # Descrição
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <p style='font-size: 1.2em; color: #666;'>
                Visualização geográfica dos terrenos disponíveis em Eusébio
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Carregar dados do Supabase
    db = SupabaseManager()
    df = db.obter_dados()

    if not df.empty:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            preco_min, preco_max = st.slider(
                "Faixa de Preço (R$)",
                float(df['preco_real'].min()),
                float(df['preco_real'].max()),
                (float(df['preco_real'].min()), float(df['preco_real'].max())),
                format="R$ %.2f"
            )
        
        with col2:
            area_min, area_max = st.slider(
                "Faixa de Área (m²)",
                float(df['area_m2'].min()),
                float(df['area_m2'].max()),
                (float(df['area_m2'].min()), float(df['area_m2'].max())),
                format="%.2f m²"
            )
        
        with col3:
            if 'bairro' in df.columns:
                bairros = ['Todos'] + list(df['bairro'].unique())
                bairro_selecionado = st.selectbox("Bairro", bairros)

        # Aplicar filtros
        df_filtrado = df[
            (df['preco_real'] >= preco_min) &
            (df['preco_real'] <= preco_max) &
            (df['area_m2'] >= area_min) &
            (df['area_m2'] <= area_max)
        ]

        if 'bairro' in df.columns and bairro_selecionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['bairro'] == bairro_selecionado]

        # Criar e exibir o mapa
        mapa = criar_mapa(df_filtrado)
        st_folium(mapa, width="100%", height=600)

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Terrenos", len(df_filtrado))
        with col2:
            preco_medio = df_filtrado['preco_real'].mean()
            st.metric("Preço Médio", f"R$ {preco_medio:,.2f}")
        with col3:
            area_media = df_filtrado['area_m2'].mean()
            st.metric("Área Média", f"{area_media:,.2f} m²")
        with col4:
            preco_m2_medio = df_filtrado['preco_m2'].mean()
            st.metric("Preço/m² Médio", f"R$ {preco_m2_medio:,.2f}")

        # Tabela de dados
        st.markdown("### 📋 Dados Detalhados")
        st.dataframe(
            df_filtrado.style.format({
                'preco_real': 'R$ {:,.2f}',
                'preco_m2': 'R$ {:,.2f}',
                'area_m2': '{:,.2f} m²',
                'latitude': '{:.6f}',
                'longitude': '{:.6f}'
            }),
            use_container_width=True
        )
    else:
        st.warning("Não há dados disponíveis para exibição.")

    # Rodapé
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: #666;'>
            <p>Desenvolvido por Rhuan Mateus - CMB Capital</p>
            <p style='font-size: 0.8em;'>Última atualização: Janeiro 2025</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
