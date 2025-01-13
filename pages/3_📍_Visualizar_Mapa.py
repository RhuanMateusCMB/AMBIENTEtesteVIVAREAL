import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from supabase import create_client
import folium
from streamlit_folium import st_folium
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Mapa de Terrenos - CMB Capital",
    page_icon="📍",
    layout="wide"
)

# Função para conectar ao Supabase
def conectar_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return None

# Função para obter as coordenadas de um endereço
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="cmb_capital_app")
        # Adiciona ", Eusébio, CE, Brasil" ao endereço para melhorar a precisão
        full_address = f"{address}, Eusébio, CE, Brasil"
        location = geolocator.geocode(full_address)
        
        if location:
            return location.latitude, location.longitude
        return None
    except (GeocoderTimedOut, GeocoderServiceError):
        time.sleep(1)  # Espera 1 segundo antes de tentar novamente
        return None

def main():
    st.title("📍 Mapa de Terrenos - Eusébio/CE")
    
    # Conecta ao Supabase
    supabase = conectar_supabase()
    if not supabase:
        return
    
    try:
        # Obtém os dados mais recentes do Supabase
        response = supabase.table('teste').select('*').execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            st.warning("Não há dados disponíveis para exibir no mapa.")
            return
        
        # Obtém a data mais recente
        data_mais_recente = df['data_coleta'].max()
        df_recente = df[df['data_coleta'] == data_mais_recente]
        
        # Informações sobre os dados
        st.info(f"""
        ℹ️ Exibindo dados da coleta mais recente: {data_mais_recente}
        Total de terrenos: {len(df_recente)}
        """)
        
        # Cria um DataFrame para armazenar as coordenadas
        df_mapa = pd.DataFrame()
        
        with st.spinner("Obtendo coordenadas dos endereços..."):
            coordenadas = []
            for endereco in df_recente['endereco']:
                coords = get_coordinates(endereco)
                if coords:
                    coordenadas.append(coords)
                else:
                    coordenadas.append((None, None))
            
            df_mapa['LAT'] = [coord[0] if coord else None for coord in coordenadas]
            df_mapa['LON'] = [coord[1] if coord else None for coord in coordenadas]
        
        # Remove linhas com coordenadas nulas
        df_mapa = df_mapa.dropna()
        
        if df_mapa.empty:
            st.error("Não foi possível obter coordenadas válidas para os endereços.")
            return
        
        # Cria o mapa usando Folium
        m = folium.Map(
            location=[df_mapa['LAT'].mean(), df_mapa['LON'].mean()],
            zoom_start=13
        )
        
        # Adiciona os marcadores
        for idx, row in df_mapa.iterrows():
            preco = df_recente.iloc[idx]['preco_real']
            area = df_recente.iloc[idx]['area_m2']
            endereco = df_recente.iloc[idx]['endereco']
            link = df_recente.iloc[idx]['link']
            
            popup_html = f"""
            <div style='width: 200px'>
                <b>Endereço:</b> {endereco}<br>
                <b>Área:</b> {area:.2f}m²<br>
                <b>Preço:</b> R$ {preco:,.2f}<br>
                <a href='{link}' target='_blank'>Ver no site</a>
            </div>
            """
            
            folium.Marker(
                [row['LAT'], row['LON']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Exibe o mapa
        st_folium(m, width=None, height=600)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Terrenos Mapeados", len(df_mapa))
        with col2:
            preco_medio = df_recente['preco_real'].mean()
            st.metric("Preço Médio", f"R$ {preco_medio:,.2f}")
        with col3:
            area_media = df_recente['area_m2'].mean()
            st.metric("Área Média", f"{area_media:,.2f} m²")
        
    except Exception as e:
        st.error(f"Erro ao processar os dados: {str(e)}")
        
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
