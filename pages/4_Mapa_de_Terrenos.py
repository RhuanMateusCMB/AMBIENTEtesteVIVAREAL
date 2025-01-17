import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

def criar_mapa_terrenos(df):
    # Verificar se existem coordenadas válidas
    df_com_coordenadas = df.dropna(subset=['latitude', 'longitude'])
    
    if df_com_coordenadas.empty:
        st.warning("Não há coordenadas válidas para exibir no mapa.")
        return
    
    # Determinar o centro do mapa (média das coordenadas)
    centro_lat = df_com_coordenadas['latitude'].mean()
    centro_lon = df_com_coordenadas['longitude'].mean()
    
    # Criar mapa
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=12)
    
    # Adicionar marcadores para cada terreno
    for idx, row in df_com_coordenadas.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            popup=f"""
            <b>Detalhes do Terreno</b><br>
            Endereço: {row['endereco']}<br>
            Área: {row['area_m2']:.2f} m²<br>
            Preço: R$ {row['preco_real']:,.2f}<br>
            Preço/m²: R$ {row['preco_m2']:,.2f}
            """,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.7
        ).add_to(m)
    
    return m

def main():
    st.title("🗺️ Mapa de Terrenos em Eusébio")
    
    # Carregar dados
    df = st.session_state.get('df')
    
    if df is not None:
        # Verificar se já processou coordenadas
        if 'latitude' not in df.columns or df['latitude'].isna().all():
            st.warning("É necessário processar as coordenadas primeiro.")
            if st.button("Processar Coordenadas"):
                with st.spinner("Processando coordenadas..."):
                    df = processar_coordenadas_em_lote(df)
                    st.session_state.df = df
                    st.experimental_rerun()
        else:
            # Criar mapa
            mapa = criar_mapa_terrenos(df)
            
            if mapa:
                # Exibir mapa
                st_folium(mapa, width=725, height=500)
                
                # Estatísticas do mapa
                st.subheader("📊 Estatísticas dos Terrenos Mapeados")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Terrenos", len(df[df['latitude'].notna()]))
                
                with col2:
                    preco_medio = df[df['latitude'].notna()]['preco_real'].mean()
                    st.metric("Preço Médio", f"R$ {preco_medio:,.2f}")
                
                with col3:
                    area_media = df[df['latitude'].notna()]['area_m2'].mean()
                    st.metric("Área Média", f"{area_media:,.2f} m²")
    else:
        st.warning("Primeiro, colete os dados no módulo de Coleta de Dados.")

if __name__ == "__main__":
    main()
