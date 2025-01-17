import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from supabase import create_client

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
    
    # Configuração do Supabase
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(supabase_url, supabase_key)
    
    # Obter dados do Supabase
    response = supabase.table("teste").select("*").execute()
    df = pd.DataFrame(response.data)
    
    if not df.empty:
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
        st.warning("Não há dados disponíveis no Supabase para exibir no mapa.")

if __name__ == "__main__":
    main()
