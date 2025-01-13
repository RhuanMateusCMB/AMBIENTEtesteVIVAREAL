# pages/3_📍_Visualizar_Mapa.py

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

# Configuração do Supabase (se necessário)
def init_connection():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

def get_data():
    """Função para buscar dados do Supabase"""
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
        # Componente do mapa
        components.html(
            """
            <div id="mapa" style="height: 600px; width: 100%;"></div>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
            """,
            height=600,
        )
        
        # Converter DataFrame para JSON para usar no mapa
        st.session_state.map_data = df.to_dict('records')
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Terrenos", len(df))
        with col2:
            preco_medio = df['preco_real'].mean()
            st.metric("Preço Médio", f"R$ {preco_medio:,.2f}")
        with col3:
            area_media = df['area_m2'].mean()
            st.metric("Área Média", f"{area_media:,.2f} m²")
        
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
