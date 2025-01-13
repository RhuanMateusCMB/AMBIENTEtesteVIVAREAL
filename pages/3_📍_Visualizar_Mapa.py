import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from supabase import create_client
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import json
import os
import random

# Configuração da página
st.set_page_config(
    page_title="Mapa de Terrenos - CMB Capital",
    page_icon="📍",
    layout="wide"
)

# Estilo CSS personalizado para o tema escuro
st.markdown("""
    <style>
    .metric-container {
        background-color: #2D2D2D;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #444;
    }
    .metric-label {
        color: #CCCCCC;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #FFFFFF;
        font-size: 1.5rem;
        font-weight: bold;
    }
    #map { 
        border-radius: 8px;
        border: 1px solid #444;
    }
    .leaflet-popup-content-wrapper {
        background-color: #2D2D2D;
        color: #FFFFFF;
    }
    .leaflet-popup-tip {
        background-color: #2D2D2D;
    }
    </style>
""", unsafe_allow_html=True)

def init_connection():
    """Inicializa conexão com o Supabase"""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

def get_cache_file():
    return "geocoding_cache.json"

def load_cache():
    try:
        if os.path.exists(get_cache_file()):
            with open(get_cache_file(), 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_cache(cache):
    try:
        with open(get_cache_file(), 'w') as f:
            json.dump(cache, f)
    except:
        pass

@st.cache_data(ttl=3600)
def geocode_address(address):
    """Converte endereço em coordenadas com retry e cache"""
    try:
        # Verifica cache primeiro
        cache = load_cache()
        if address in cache:
            return cache[address]
            
        # Configura sessão com retry
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # Adiciona Eusébio, CE ao endereço
        search_address = f"{address}, Eusébio, Ceará, Brasil"
            
        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            'User-Agent': 'CMBCapital/1.0',
            'Accept-Language': 'pt-BR,pt'
        }
        params = {
            'q': search_address,
            'format': 'json',
            'limit': 1
        }
        
        response = session.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if data:
            coords = (float(data[0]['lat']), float(data[0]['lon']))
            # Salva no cache
            cache[address] = coords
            save_cache(cache)
            return coords
            
        # Fallback: coordenadas aproximadas de Eusébio
        return (-3.8912, -38.4558)
        
    except Exception as e:
        st.warning(f"Usando coordenadas aproximadas para: {address}")
        return (-3.8912, -38.4558)

@st.cache_data(ttl=3600)
def get_data():
    """Busca e processa os dados do Supabase"""
    try:
        supabase = init_connection()
        response = supabase.table('imoveisatual').select('*').execute()
        df = pd.DataFrame(response.data)
        
        # Adiciona coordenadas para cada endereço
        coordinates = []
        total = len(df)
        
        with st.spinner("Geocodificando endereços..."):
            progress_bar = st.progress(0)
            
            for idx, row in df.iterrows():
                progress = (idx + 1) / total
                progress_bar.progress(progress)
                
                coords = geocode_address(row['endereco'])
                if coords:
                    # Adiciona pequena variação se usar coordenadas padrão
                    if coords == (-3.8912, -38.4558):
                        lat = coords[0] + (random.uniform(-0.01, 0.01))
                        lon = coords[1] + (random.uniform(-0.01, 0.01))
                        coordinates.append((lat, lon))
                    else:
                        coordinates.append(coords)
                else:
                    # Coordenadas padrão com variação
                    lat = -3.8912 + (random.uniform(-0.01, 0.01))
                    lon = -38.4558 + (random.uniform(-0.01, 0.01))
                    coordinates.append((lat, lon))
                
                time.sleep(1)  # Respeita limite de requisições
            
            progress_bar.empty()
            
        df['latitude'] = [c[0] for c in coordinates]
        df['longitude'] = [c[1] for c in coordinates]
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None

def format_currency(value):
    """Formata valores monetários"""
    return f"R$ {value:,.2f}"

def format_area(value):
    """Formata valores de área"""
    return f"{value:,.2f} m²"

def main():
    st.title("📍 Mapa de Terrenos - Eusébio, CE")
    
    with st.spinner("Carregando dados..."):
        df = get_data()
    
    if df is not None and not df.empty:
        # Métricas em cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Total de Terrenos</div>
                    <div class="metric-value">{len(df)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            preco_medio = df['preco_real'].mean()
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Preço Médio</div>
                    <div class="metric-value">{format_currency(preco_medio)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            area_media = df['area_m2'].mean()
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-label">Área Média</div>
                    <div class="metric-value">{format_area(area_media)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Filtros
        st.markdown("### 🔍 Filtros")
        col1, col2 = st.columns(2)
        with col1:
            preco_min, preco_max = st.slider(
                "Faixa de Preço (R$)",
                min_value=float(df['preco_real'].min()),
                max_value=float(df['preco_real'].max()),
                value=(float(df['preco_real'].min()), float(df['preco_real'].max()))
            )
        with col2:
            area_min, area_max = st.slider(
                "Faixa de Área (m²)",
                min_value=float(df['area_m2'].min()),
                max_value=float(df['area_m2'].max()),
                value=(float(df['area_m2'].min()), float(df['area_m2'].max()))
            )

        # Filtra os dados
        df_filtrado = df[
            (df['preco_real'].between(preco_min, preco_max)) &
            (df['area_m2'].between(area_min, area_max))
        ]

        # Componente do mapa
        st.markdown("### 🗺️ Mapa de Terrenos")
        components.html(
            f"""
            <div id="map" style="height: 600px; width: 100%;"></div>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
            <script>
                // Inicializar o mapa
                var map = L.map('map').setView([-3.8912, -38.4558], 13);
                
                // Adicionar camada do OpenStreetMap
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);

                // Adicionar marcadores para cada terreno
                const terrenos = {df_filtrado.to_dict('records')};
                const bounds = [];
                
                terrenos.forEach(terreno => {{
                    const lat = terreno.latitude;
                    const lng = terreno.longitude;
                    bounds.push([lat, lng]);
                    
                    const marker = L.marker([lat, lng])
                        .bindPopup(`
                            <div style="color: #FFF;">
                                <strong>Área:</strong> ${{terreno.area_m2.toLocaleString('pt-BR')}} m²<br>
                                <strong>Preço:</strong> R$ ${{terreno.preco_real.toLocaleString('pt-BR')}}<br>
                                <strong>Preço/m²:</strong> R$ ${{(terreno.preco_real / terreno.area_m2).toLocaleString('pt-BR')}}<br>
                                <strong>Endereço:</strong> ${{terreno.endereco}}<br>
                                <a href="${{terreno.link}}" target="_blank" style="color: #FF4B4B;">Ver anúncio</a>
                            </div>
                        `)
                        .addTo(map);
                }});
                
                // Ajusta o zoom para mostrar todos os marcadores
                if (bounds.length > 0) {{
                    map.fitBounds(bounds);
                }}
            </script>
            """,
            height=600,
        )
        
        # Tabela de dados
        st.markdown("### 📊 Lista de Terrenos")
        st.dataframe(
            df_filtrado[['endereco', 'area_m2', 'preco_real', 'preco_m2', 'link']].style.format({
                'area_m2': '{:,.2f} m²',
                'preco_real': 'R$ {:,.2f}',
                'preco_m2': 'R$ {:,.2f}'
            }),
            use_container_width=True
        )

        # Download dos dados filtrados
        csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar dados filtrados (CSV)",
            data=csv,
            file_name=f"terrenos_eusebio_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
