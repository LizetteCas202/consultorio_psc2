# =================================================================
#    SISTEMA DE GESTIÓN: Consultorio Psicológico DACYTI
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import sqlite3

# URL Oficial del Escudo UJAT
LOGO_UJAT_URL = "https://images.seeklogo.com/logo-png/23/1/ujat-tabasco-logo-png_seeklogo-233582.png"

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Consultorio Psicológico DACYTI",
    page_icon=LOGO_UJAT_URL,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MOTOR DE CONEXIÓN Y BASE DE DATOS LOCAL ---
def conectar_db_local():
    try:
        return sqlite3.connect("centro_psicologico.db")
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None

def inicializar_sistema_db():
    conn = conectar_db_local()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                clave_hash TEXT NOT NULL,
                rol TEXT NOT NULL,
                pregunta_secreta TEXT,
                respuesta_secreta_hash TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expedientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                genero TEXT,
                edad INTEGER DEFAULT 20,
                division TEXT,
                carrera TEXT,
                semestre TEXT,
                telefono TEXT,
                correo TEXT,
                observaciones TEXT,
                etiquetas TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expediente_id INTEGER,
                fecha_hora TEXT,
                estado TEXT DEFAULT 'Pendiente',
                motivo TEXT,
                notas_evolucion TEXT DEFAULT '',
                FOREIGN KEY(expediente_id) REFERENCES expedientes(id)
            )
        """)
        
        cursor.execute("SELECT * FROM usuarios WHERE usuario = 'psicologa.sara'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave_hash, rol, pregunta_secreta, respuesta_secreta_hash)
                VALUES ('psicologa.sara', 'admin123', 'Director/Psicólogo', '¿Unidad de origen?', 'chontalpa')
            """)
        conn.commit()
        conn.close()

inicializar_sistema_db()

# --- 3. CONTROL DE ESTADOS DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = ""
if "side_peek_modo" not in st.session_state: st.session_state.side_peek_modo = None
if "cita_seleccionada_id" not in st.session_state: st.session_state.cita_seleccionada_id = None

ESTRUCTURA_UJAT = {
    "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
    "DAIA": ["Ingeniería Mecánica Eléctrica", "Ingeniería Civil", "Ingeniería Química", "Ingeniería Ambiental"],
    "DACB": ["Licenciatura en Ciencias Computacionales", "Licenciatura en Matemáticas", "Licenciatura en Física"]
}

# -------------------------------------------------------------------------------------
# INYECCIÓN MAESTRA DE CSS - REPARACIÓN DE MENÚS DESPLEGABLES FLOTANTES (DROPDOWNS)
# -------------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* 1. CONTROL DE FONDO GENERAL DE LA APLICACIÓN */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stCanvas"] {
        background-color: #f1f5f9 !important; /* Gris claro suave */
    }

    /* 2. REPARACIÓN RADICAL DE TÍTULOS Y TEXTOS (FORZADO A AZUL MARINO) */
    h1, h2, h3, h4, h5, h6, p, span, label, strong, li, 
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    .stWidgetFormLabel p,
    .stSelectbox label p,
    .stTextInput label p,
    .stTextArea label p,
    .stNumberInput label p {
        color: #0f172a !important; /* Azul marino institucional */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    [data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* 3. SOLUCIÓN COMPLETA PARA BOTONES */
    .stButton button {
        color: #f8fafc !important;             
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stButton button p {
        color: #f8fafc !important;
    }

    .stButton button:hover {
        background-color: #1e293b !important;  
        color: #ffffff !important;
        border-color: #475569 !important;
    }

    /* 4. BLINDAJE DE CAJAS DE TEXTO (INPUTS Y TEXTAREAS) */
    div[data-baseweb="input"] input, 
    div[data-baseweb="textarea"] textarea,
    .stTextInput input, .stPasswordInput input, .stTextArea textarea {
        background-color: #ffffff !important; 
        color: #0f172a !important;            
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        -webkit-text-fill-color: #0f172a !important; 
    }

    /* 5. FIX TOTAL PARA MENÚS DESPLEGABLES (GÉNERO, CARRERA, DIVISIÓN, SEMESTRE) */
    /* Caja contenedora cerrada del selectbox */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important; 
        color: #0f172a !important;            
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }

    /* Forzar el contenedor flotante de la lista desplegable (popover/menu) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], [role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08) !important;
    }

    /* Forzar los elementos individuales de la lista (las opciones a elegir) */
    div[data-baseweb="menu"] li, 
    [role="listbox"] li, 
    [role="option"], 
    div[data-baseweb="popover"] div {
        color: #0f172a !important;            
        background-color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* Efecto al pasar el cursor sobre las opciones del desplegable */
    div[data-baseweb="menu"] li:hover, 
    [role="option"]:hover,
    div[aria-selected="true"] {
        background-color: #f1f5f9 !important; /* Gris claro de selección */
        color: #0284c7 !important;            /* Resaltado en azul clínico */
    }

    /* Botones de incremento del número de edad */
    div[data-testid="stNumberInput"] button {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
    }

    /* 6. DISEÑO DEL CONTENEDOR SIDE-PEEK (TARJETA TIPO NOTION CAJA BLANCA) */
    div[data-testid="stForm"] { 
        background-color: #ffffff !important; 
        border: 1px solid #e2e8f0 !important;
        box-shadow: -4px 4px 20px rgba(15, 23, 42, 0.06) !important;
        padding: 24px !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stForm"] h4, 
    div[data-testid="stForm"] p, 
    div[data-testid="stForm"] label {
        color: #0f172a !important;
    }

    /* 7. BARRA LATERAL IZQUIERDA */
    [data-testid="stSidebar"] { 
        background-color: #f8fafc !important; 
        border-right: 1px solid #e2e8f0 !important; 
    }
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #0f172a !important;
    }

    /* 8. TABLAS, CABECERAS Y CONTENEDORES DE AVISOS */
    .constante-header-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 25px;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 12px;
    }
    
    .notion-table-container {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        overflow: hidden;
        margin-bottom: 20px;
        background-color: #ffffff;
    }
    
    .notion-table-header {
        display: flex; 
        background-color: #f1f5f9; 
        font-weight: 600; 
        padding: 10px 14px; 
        border-bottom: 1px solid #e2e8f0; 
        font-size: 13px; 
        color: #475569 !important;
    }
    
    .notion-table-row {
        display: flex;
        align-items: center;
        padding: 8px 14px;
        color: #0f172a !important;
    }
    
    .status-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .status-pendiente { background-color: #fef3c7; color: #d97706 !important; }
    .status-realizada { background-color: #dcfce7; color: #15803d !important; }
    .status-cancelada { background-color: #fee2e2; color: #b91c1c !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. PORTAL DE ACCESO (LOGIN) ---
if not st.session_state.autenticado:
    st.markdown('<div style="max-width:400px; margin:auto; padding-top:100px;">', unsafe_allow_html=True)
    st.image(LOGO_UJAT_URL, width=90)
    st.markdown("<h2>Acceso al Portal Clínico DACYTI</h2>", unsafe_allow_html=True)
    u_login = st.text_input("Usuario Corporativo:")
    p_login = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar al Sistema", use_container_width=True):
        conn = conectar_db_local()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND clave_hash=?", (u_login, p_login))
        if cursor.fetchone():
            st.session_state.autenticado = True
            st.session_state.usuario_actual = u_login
            st.rerun()
        else:
            st.error("Credenciales institucionales incorrectas.")
        conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Cabecera Fija Institucional
    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="35">
            <h1 style="color:#0f172a !important; margin:0; font-size:24px;">Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Navegación Lateral Izquierda
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["🏠 Inicio ", "📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Personal Encargado:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.side_peek_modo = None
        st.rerun()

    # =================================================================================
    # MÓDULO: INICIO Y PLANNER DINÁMICO
    # =================================================================================
    if seccion == "🏠 Inicio ":
        
        if st.session_state.side_peek_modo:
            col_izquierda, col_derecha = st.columns([60, 40], gap="medium")
        else:
            col_izquierda = st.container()

        # -----------------------------------------------------------------------------
        # COLUMNA IZQUIERDA: PLANNER DE TRABAJO
        # -----------------------------------------------------------------------------
        with col_izquierda:
            st.markdown("### Panel de la Agenda e Historial Clínico")
            
            c_btn1, c_btn2, _ = st.columns([2.5, 2.5, 3])
            with c_btn1:
                if st.button("➕ Nuevo Expediente", use_container_width=True):
                    st.session_state.side_peek_modo = "NUEVO_EXPEDIENTE"
                    st.rerun()
            with c_btn2:
                if st.button("📅 Agendar Nueva Cita", use_container_width=True):
                    st.session_state.side_peek_modo = "NUEVA_CITA"
                    st.rerun()

            st.markdown("---")

            # EXTRACCIÓN DE CITAS
            conn = conectar_db_local()
            citas_tabla = pd.read_sql_query("""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora ASC
            """, conn)
            conn.close()

            st.markdown("#### 📄 Citas Programadas")
            if not citas_tabla.empty:
                st.markdown('<div class="notion-table-container">', unsafe_allow_html=True)
                st.markdown("""
                    <div class="notion-table-header">
                        <div style="flex: 2; padding-left: 5px;">Aa Nombre del Paciente</div>
                        <div style="flex: 1.5;">📅 Fecha y Hora</div>
                        <div style="flex: 1;">✨ Estado</div>
                        <div style="flex: 1; text-align: center;">⚙️ Gestión</div>
                    </div>
                """, unsafe_allow_html=True)

                for _, fila in citas_tabla.iterrows():
                    clase_badge = "status-pendiente"
                    if fila['estado'] == "Realizada": clase_badge = "status-realizada"
                    elif fila['estado'] == "Cancelada": clase_badge = "status-cancelada"

                    c_fila1, c_fila2, c_fila3, c_fila4 = st.columns([2, 1.5, 1, 1])
                    with c_fila1:
                        st.markdown(f"<div class='notion-table-row'>📄 {fila['nombre']}</div>", unsafe_allow_html=True)
                    with c_fila2:
                        st.markdown(f"<div class='notion-table-row'>{fila['fecha_hora']}</div>", unsafe_allow_html=True)
                    with c_fila3:
                        st.markdown(f"<div class='notion-table-row'><span class='status-badge {clase_badge}'>{fila['estado']}</span></div>", unsafe_allow_html=True)
                    with c_fila4:
                        if st.button("Ver Detalle", key=f"open_t_{fila['id']}", use_container_width=True):
                            st.session_state.side_peek_modo = "VER_CITA"
                            st.session_state.cita_seleccionada_id = fila['id']
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background-color: #ffffff; padding: 14px; border-left: 4px solid #0f172a; color: #0f172a; border-radius: 4px; font-size: 14px; border: 1px solid #e2e8f0; font-weight: 500;">No se encuentran registros de citas programadas en la base de datos.</div>', unsafe_allow_html=True)

            st.markdown("---")

            # INTERFAZ DE CALENDARIOS INTERACTIVOS
            st.markdown("#### 📅 Visualizador de Calendario Clínico")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                tipo_formato = st.selectbox("Formato Ajustado:", ["Mensual (Carga General)", "Semanal (Horario Laboral L-V)"])
            with c_p2:
                fecha_pivote = st.date_input("Fecha Base Enfoque:", value=date.today(), key="pivote_date")

            diccionario_citas_global = {}
            for _, c_act in citas_tabla.iterrows():
                try:
                    dt_c = datetime.strptime(c_act['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                    f_str = dt_c.strftime("%Y-%m-%d")
                    if f_str not in diccionario_citas_global: diccionario_citas_global[f_str] = []
                    diccionario_citas_global[f_str].append(c_act)
                except: pass

            if tipo_formato == "Mensual (Carga General)":
                año_sel, mes_sel = fecha_pivote.year, fecha_pivote.month
                cal_objeto = calendar.Calendar(firstweekday=0)
                semanas_mes = cal_objeto.monthdatescalendar(año_sel, mes_sel)

                dias_semana_nombres = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
                cols_cabecera = st.columns(7)
                for idx, d_nom in enumerate(dias_semana_nombres):
                    cols_cabecera[idx].markdown(f"<center><strong style='color:#0f172a !important;'>{d_nom}</strong></center>", unsafe_allow_html=True)

                for sem_idx, semana in enumerate(semanas_mes):
                    cols_dias = st.columns(7)
                    for dia_idx, f_dia in enumerate(semana):
                        with cols_dias[dia_idx]:
                            if f_dia.month == mes_sel:
                                st.markdown(f"<span style='color:#0f172a !important; font-weight:600; font-size:13px;'>{f_dia.day}</span>", unsafe_allow_html=True)
                                f_buscar = f_dia.strftime("%Y-%m-%d")
                                if f_buscar in diccionario_citas_global:
                                    for cita_dia in diccionario_citas_global[f_buscar]:
                                        hora_c = cita_dia['fecha_hora'][11:16]
                                        if st.button(f"⏱️ {hora_c}", key=f"cal_m_btn_{cita_dia['id']}", use_container_width=True):
                                            st.session_state.side_peek_modo = "VER_CITA"
                                            st.session_state.cita_seleccionada_id = cita_dia['id']
                                            st.rerun()
                    st.markdown("<hr style='margin:4px 0; border-top:1px dashed #cbd5e1;'>", unsafe_allow_html=True)

            elif tipo_formato == "Semanal (Horario Laboral L-V)":
                inicio_semana = fecha_pivote - timedelta(days=fecha_pivote.weekday())
                dias_laborales = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
                cols_semana = st.columns(5)
                
                for idx, nom_dia in enumerate(dias_laborales):
                    fecha_dia_actual = inicio_semana + timedelta(days=idx)
                    f_buscar_semana = fecha_dia_actual.strftime("%Y-%m-%d")
                    
                    with cols_semana[idx]:
                        st.markdown(f"<center><div style='background-color:#ffffff; padding:6px; border:1px solid #e2e8f0; border-radius:4px; color:#0f172a !important;'><strong>{nom_dia}</strong><br><small style='color:#475569;'>{fecha_dia_actual.day} de {calendar.month_name[fecha_dia_actual.month][:3]}</small></div></center>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        if f_buscar_semana in diccionario_citas_global:
                            for cita_sem in diccionario_citas_global[f_buscar_semana]:
                                hora_s = cita_sem['fecha_hora'][11:16]
                                if st.button(f"{hora_s} - {cita_sem['nombre'][:12]}...", key=f"cal_s_btn_{cita_sem['id']}", use_container_width=True):
                                    st.session_state.side_peek_modo = "VER_CITA"
                                    st.session_state.cita_seleccionada_id = cita_sem['id']
                                    st.rerun()
                        else:
                            st.markdown("<center><span style='color:#94a3b8; font-size:12px;'>Sin citas</span></center>", unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # COLUMNA DERECHA: SIDE-PEEK RECONFIGURADO
        # -----------------------------------------------------------------------------
        if st.session_state.side_peek_modo:
            with col_derecha:
                c_tit, c_close = st.columns([3.5, 1.5])
                with c_tit:
                    if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                        st.markdown("<h4 style='color:#0f172a !important; margin:0; font-weight:700;'>📝 Abrir Nuevo Expediente Clínico</h4>", unsafe_allow_html=True)
                    elif st.session_state.side_peek_modo == "VER_CITA":
                        st.markdown("<h4 style='color:#0f172a !important; margin:0; font-weight:700;'>📄 Evaluación Clínica Semanal</h4>", unsafe_allow_html=True)
                    elif st.session_state.side_peek_modo == "NUEVA_CITA":
                        st.markdown("<h4 style='color:#0f172a !important; margin:0; font-weight:700;'>📅 Nueva Agenda de Consulta</h4>", unsafe_allow_html=True)
                with c_close:
                    if st.button("Retraer >>", key="btn_close_panel_global", use_container_width=True):
                        st.session_state.side_peek_modo = None
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()
                
                st.markdown("<p style='color:#475569 !important; font-size:13px; margin-top:-5px;'>Complete los datos requeridos del alumno institucional.</p>", unsafe_allow_html=True)

                # --- NUEVO EXPEDIENTE ---
                if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                    with st.form("form_nuevo_expediente_notion"):
                        exp_nom = st.text_input("Nombre Completo del Alumno:")
                        exp_mat = st.text_input("Matrícula Institucional:")
                        
                        cf1, cf2 = st.columns(2)
                        with cf1: exp_edad = st.number_input("Edad:", min_value=15, max_value=60, value=20)
                        with cf2: exp_gen = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
                        
                        exp_div = st.selectbox("División Académica:", list(ESTRUCTURA_UJAT.keys()))
                        exp_car = st.selectbox("Carrera Universitaria:", ESTRUCTURA_UJAT[exp_div])
                        exp_sem = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"])
                        
                        exp_tel = st.text_input("Teléfono de Contacto:")
                        exp_cor = st.text_input("Correo Electrónico:")
                        exp_tag = st.text_input("Etiquetas Diagnósticas (separadas por comas):")
                        exp_obs = st.text_area("Motivo de Consulta Inicial:", height=100)
                        
                        if st.form_submit_button("Registrar Expediente Electrónico", use_container_width=True):
                            if exp_mat.strip() and exp_nom.strip():
                                conn = conectar_db_local()
                                try:
                                    tags_p = ",".join([t.strip().lower() for t in exp_tag.split(",") if t.strip()])
                                    conn.cursor().execute("""
                                        INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (exp_mat.strip(), exp_nom.strip(), exp_gen, int(exp_edad), exp_div, exp_car, exp_sem, exp_tel, exp_cor, exp_obs, tags_p))
                                    conn.commit()
                                    st.session_state.side_peek_modo = None
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("La matrícula ya existe.")
                                finally: conn.close()

                # --- VER / EDITAR CITA SELECCIONADA ---
                elif st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id:
                    conn = conectar_db_local()
                    datos_cita = conn.cursor().execute("""
                        SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id, e.matricula
                        FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                    """, (st.session_state.cita_seleccionada_id,)).fetchone()
                    conn.close()

                    if datos_cita:
                        st.markdown(f"<span style='color:#0284c7 !important; font-size:14px; font-weight: 600;'>✨ Paciente: {datos_cita[1]} | Matrícula: {datos_cita[8]}</span>", unsafe_allow_html=True)
                        with st.form("form_edicion_cita_notion"):
                            peek_estado = st.selectbox("Estado de la Consulta:", ["Pendiente", "Realizada", "Cancelada", "No Asistió"], index=["Pendiente", "Realizada", "Cancelada", "No Asistió"].index(datos_cita[3]))
                            peek_fecha = st.text_input("Horario Programado:", value=datos_cita[2], disabled=True)
                            peek_motivo = st.text_area("Motivo Clínico de Consulta:", value=datos_cita[4], disabled=True)
                            peek_notas = st.text_area("Notas de Evolución Clínica:", value=datos_cita[5], height=180)
                            peek_tags = st.text_input("Etiquetas Diagnósticas:", value=datos_cita[6])

                            if st.form_submit_button("Actualizar Historial Clínico", use_container_width=True):
                                conn = conectar_db_local()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (peek_estado, peek_notas, datos_cita[0]))
                                cursor.execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (peek_tags.strip().lower(), datos_cita[7]))
                                conn.commit()
                                conn.close()
                                st.session_state.side_peek_modo = None
                                st.session_state.cita_seleccionada_id = None
                                st.rerun()

                # --- AGENDAR NUEVA CITA ---
                elif st.session_state.side_peek_modo == "NUEVA_CITA":
                    conn = conectar_db_local()
                    expedientes_df = pd.read_sql_query("SELECT id, nombre, matricula FROM expedientes", conn)
                    conn.close()

                    with st.form("form_nueva_cita_notion"):
                        if not expedientes_df.empty:
                            opciones_pacientes = {f"{r['nombre']} ({r['matricula']})": r['id'] for _, r in expedientes_df.iterrows()}
                            paciente_sel = st.selectbox("Seleccionar Alumno Paciente:", list(opciones_pacientes.keys()))
                            fecha_cita = st.date_input("Fecha de la Consulta:", value=date.today())
                            hora_cita = st.time_input("Hora de la Consulta:")
                            motivo_cita = st.text_area("Motivo o Descripción de Sesión:")
                            
                            if st.form_submit_button("Confirmar Cita Médica", use_container_width=True):
                                conn = conectar_db_local()
                                cursor = conn.cursor()
                                fecha_hora_str = f"{fecha_cita} {hora_cita.strftime('%H:%M:%S')}"
                                cursor.execute("""
                                    INSERT INTO citas (expediente_id, fecha_hora, estado, motivo)
                                    VALUES (?, ?, 'Pendiente', ?)
                                """, (opciones_pacientes[paciente_sel], fecha_hora_str, motivo_cita))
                                conn.commit()
                                conn.close()
                                st.session_state.side_peek_modo = None
                                st.rerun()
                        else:
                            st.warning("No existen expedientes registrados para asignar la cita.")
                            st.form_submit_button("Aceptar", disabled=True)

    # =================================================================================
    # OTROS MÓDULOS DE GESTIÓN
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h3 style='color:#0f172a !important;'>Repositorio General de Expedientes Clínicos</h3>", unsafe_allow_html=True)
        bus_nom = st.text_input("🔍 Buscar Alumno por Nombre o Matrícula:")
        
        conn = conectar_db_local()
        query = "SELECT matricula, nombre, genero, edad, division, carrera, semestre, etiquetas, observaciones FROM expedientes WHERE 1=1"
        args = []
        if bus_nom:
            query += " AND (nombre LIKE ? OR matricula LIKE ?)"
            args.extend([f"%{bus_nom}%", f"%{bus_nom}%"])
        df_exp = pd.read_sql_query(query, conn, params=args)
        conn.close()
        
        st.dataframe(df_exp, use_container_width=True)

    elif seccion == "📅 Agenda de Citas":
        st.markdown("<h3 style='color:#0f172a !important;'>Control de Citas Clínicas e Historial de Sesiones</h3>", unsafe_allow_html=True)
        st.info("Utilice el panel principal '🏠 Inicio y Planner' para desplegar la ventana lateral interactiva de forma óptima.")

    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("<h3 style='color:#0f172a !important;'>Panel de Métricas y Estadísticas</h3>", unsafe_allow_html=True)
        st.write("Módulo en desarrollo para la generación de analíticas semestrales institucionales.")