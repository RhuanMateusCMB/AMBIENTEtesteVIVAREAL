import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from supabase import create_client
import requests
import time
import json

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

@st.cache_data(ttl=3600)  # Cache por 1 hora
def geocode_address(address):
    """Converte endereço em coordenadas usando Nominatim (OpenStreetMap)"""
    try:
        # Adiciona 'Eusébio, CE, Brasil' ao endereço se não estiver presente
        if 'eusebio' not in address.lower():
            address = f"{address}, Eusébio, CE, Brasil"
            
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        headers = {'User-Agent': 'CMBCapital/1.0'}
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        return None
    except Exception as e:
        st.error(f"Erro no geocoding: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_data():
    """Busca e processa os dados do Supabase"""
    try:
        supabase = init_connection()
        response = supabase.table('imoveisatual').select('*').execute()
        df = pd.DataFrame(response.data)
        
        # Adiciona coordenadas para cada endereço
        coordinates = []
        total = len(df)
        progress_text = "Processando endereços..."
        progress_bar = st.progress(0, text=progress_text)
        
        for idx, row in df.iterrows():
            progress = (idx + 1) / total
            progress_bar.progress(progress, text=f"{progress_text} ({idx+1}/{total})")
            
            coords = geocode_address(row['endereco'])
            if coords:
                coordinates.append(coords)
            else:
                # Coordenadas aproximadas com variação
                lat = -3.8912 + (0.02 * ((idx % 10) - 5))
                lon = -38.4558 + (0.02 * ((idx % 10) - 5))
                coordinates.append((lat, lon))
            
            time.sleep(1)  # Respeita limite de requisições
        
        df['latitude'] = [c[0] for c in coordinates]
        df['longitude'] = [c[1] for c in coordinates]
        
        progress_bar.empty()
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
