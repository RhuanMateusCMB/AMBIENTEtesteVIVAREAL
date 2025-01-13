# pages/📍_Visualizar_Mapa.py

import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from supabase import create_client

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
    }
    .metric-label {
        color: #CCCCCC;
        font-size: 0.9rem;
    }
    .metric-value {
        color: #FFFFFF;
        font-size: 1.5rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def init_connection():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

def get_data():
    try:
        supabase = init_connection()
        response = supabase.table('imoveisatual').select('*').execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None

def main():
    st.title("📍 Mapa de Terrenos - Eusébio, CE")
    
    # Buscar dados
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
                    <div class="metric-value">R$ {preco_medio:,.2f}</div>
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
                    <div class="metric-value">{area_media:,.2f} m²</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Componente do mapa com inicialização
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
                const terrenos = {df.to_dict('records')};
                terrenos.forEach(terreno => {{
                    // Adiciona uma pequena variação nas coordenadas para evitar sobreposição
                    const lat = -3.8912 + (Math.random() - 0.5) * 0.01;
                    const lng = -38.4558 + (Math.random() - 0.5) * 0.01;
                    
                    const marker = L.marker([lat, lng])
                        .bindPopup(`
                            <strong>Área:</strong> ${{terreno.area_m2.toLocaleString('pt-BR')}} m²<br>
                            <strong>Preço:</strong> R$ ${{terreno.preco_real.toLocaleString('pt-BR')}}<br>
                            <strong>Preço/m²:</strong> R$ ${{(terreno.preco_real / terreno.area_m2).toLocaleString('pt-BR')}}<br>
                            ${{terreno.endereco}}
                        `)
                        .addTo(map);
                }});
            </script>
            """,
            height=600,
        )
        
        # Tabela de dados
        st.markdown("### 📊 Dados dos Terrenos")
        st.dataframe(
            df[['endereco', 'area_m2', 'preco_real', 'preco_m2']].style.format({
                'area_m2': '{:,.2f} m²',
                'preco_real': 'R$ {:,.2f}',
                'preco_m2': 'R$ {:,.2f}'
            })
        )

if __name__ == "__main__":
    main()
