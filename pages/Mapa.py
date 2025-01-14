import streamlit as st
import streamlit.components.v1 as components
import hashlib
from supabase import create_client

# Configuração da página
st.set_page_config(
    page_title="CMB Capital - Mapa",
    page_icon="🗺️",
    layout="wide"
)

# Estilo CSS personalizado (mesmo do Coleta_de_Dados.py)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 20px;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        background-color: #1E1E1E;
        border: 1px solid #333;
    }
    .login-title {
        text-align: center;
        margin-bottom: 2rem;
        color: #FFFFFF;
    }
    .stTextInput>div>div>input {
        background-color: #2D2D2D !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
    }
    .stTextInput>label {
        color: #CCCCCC !important;
    }
    .stButton>button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 5px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #FF3333 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    }
    .login-container p {
        color: #CCCCCC !important;
    }
    </style>
    """, unsafe_allow_html=True)

class SupabaseManager:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase = create_client(self.url, self.key)

    def verificar_credenciais(self, email: str, senha: str) -> bool:
        try:
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            response = self.supabase.table('usuarios').select('*').eq('email', email).execute()
            
            if response.data and len(response.data) > 0:
                usuario = response.data[0]
                return usuario['senha_hash'] == senha_hash
            return False
        except Exception as e:
            st.error(f"Erro ao verificar credenciais: {str(e)}")
            return False

def check_login():
    """Verifica se o usuário está logado"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def login_page():
    """Renderiza a página de login"""
    st.markdown("""
        <div class="login-container">
            <h1 class="login-title">🗺️ CMB Capital</h1>
            <p style='text-align: center; color: #666;'>Sistema de Visualização de Mapa</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", key="email")
        password = st.text_input("Senha", type="password", key="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            db = SupabaseManager()
            if db.verificar_credenciais(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Email ou senha incorretos!")

def main():
    # Verifica o estado do login
    check_login()

    # Se não estiver logado, mostra a página de login
    if not st.session_state.logged_in:
        login_page()
        return

    # Se estiver logado, mostra o botão de logout e o conteúdo
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
            
    # Título e descrição
    st.title("🗺️ Mapa de Terrenos - Eusébio, CE")
    
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <p style='font-size: 1.2em; color: #666;'>
            Visualização geográfica dos terrenos disponíveis em Eusébio
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Incorporar o iframe do Looker Studio
    components.iframe(
        src="https://lookerstudio.google.com/embed/reporting/3eb69112-e085-487f-a9b0-ed395f9248dc/page/oEPdE",
        width=None,
        height=800,
        scrolling=True
    )

    # Botão para abrir em nova aba
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <p style='font-size: 0.9em; color: #666;'>Preferir ver em tela cheia?</p>
        <a href='https://lookerstudio.google.com/reporting/3eb69112-e085-487f-a9b0-ed395f9248dc' target='_blank'>
            <button style='
                background-color: #FF4B4B;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                margin: 5px 0;
            '>
                🗺️ Abrir Mapa em Nova Aba
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

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
