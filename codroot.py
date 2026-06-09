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
# INYECCIÓN MAESTRA DE CSS - ENFOQUE NOTION SIDE-PEEK Y BLINDAJE DE COLORES
# -------------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* 1. BLINDAJE DEL FONDO GENERAL DE LA APLICACIÓN */
    .stApp, [data-testid="stAppViewContainer"] { 
        background-color: #ffffff !important; 
    }
    
    /* 2. CONTRASTE ABSOLUTO DE TEXTOS ESTILO NOTION */
    h1, h2, h3, h4, h5, h6, p, span, label, li, small {
        color: #191919 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3, 
    [data-testid="stMarkdownContainer"] h4 {
        color: #191919 !important;
        font-weight: 600 !important;
    }
    
    .stWidgetFormLabel, [data-testid="stWidgetLabel"] p {
        color: #2f2f2f !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }

    /* 3. SIMULACIÓN DEL SIDE-PEEK DESLIZABLE (NOTION SIDE PANEL) */
    div[data-testid="stForm"] { 
        background-color: #fbfbfa !important; 
        border-left: 1px solid #e3e2e0 !important; 
        border-top: none !important;
        border-bottom: none !important;
        border-right: none !important;
        box-shadow: -4px 0px 16px rgba(0, 0, 0, 0.04) !important;
        padding: 26px !important;
        border-radius: 0px !important; /* Panel lateral recto */
        height: 100% !important;
        margin-top: 0px !important;
    }
    
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #ffffff !important;
        border: 1px solid #dcdbdb !important;
        border-radius: 6px !important;
    }
    
    div[data-baseweb="input"] input, div[data-baseweb="select"] span, div[data-baseweb="textarea"] textarea {
        color: #191919 !important;
    }
    
    div[data-testid="stColumn"] {
        padding: 0px !important;
        margin: 0px !important;
    }
    
    /* 4. MENÚ LATERAL IZQUIERDO (SIDEBAR) */
    [data-testid="stSidebar"] { 
        background-color: #f4f5f6 !important; 
        border-right: 1px solid #e9e9e8 !important; 
    }
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p {
        color: #2f2f2f !important; 
        font-weight: 500 !important;
    }
    
    /* 5. DISEÑO DE LA TABLA COMPACTA DE NOTION (BASADO EN IMAGE_526D7A) */
    .constante-header-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 25px;
        border-bottom: 1px solid #e9e9e8;
        padding-bottom: 12px;
    }
    .constante-header-container h1 { margin: 0 !important; font-size: 22px; color: #191919 !important; }
    
    .notion-table-container {
        border: 1px solid #e9e9e8;
        border-radius: 6px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    
    .notion-table-header {
        display: flex; 
        background-color: #f7f7f5; 
        font-weight: 600; 
        padding: 10px 14px; 
        border-bottom: 1px solid #e9e9e8; 
        font-size: 13px; 
        color: #6a6a65 !important;
    }
    .notion-table-header div { color: #6a6a65 !important; }
    
    .notion-table-row {
        display: flex;
        align-items: center;
        padding: 8px 14px;
        border-bottom: 1px solid #f1f0ef;
        background-color: #ffffff;
    }
    .notion-table-row:last-child { border-bottom: none; }
    
    /* Indicador visual de estado Notion */
    .status-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    .status-pendiente { background-color: #fdecc8; color: #b35900 !important; }
    .status-realizada { background-color: #e2f2e4; color: #2e6930 !important; }
    .status-cancelada { background-color: #ffe2dd; color: #cc3333 !important; }
    
    /* Textos y botones del planificador */
    center small strong, .stMarkdown center, .stMarkdown center small {
        color: #37352f !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    
    div.stButton > button, .stButton button {
        background-color: #ffffff !important;
        color: #191919 !important;
        border: 1px solid #dcdbdb !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    div.stButton > button:hover, .stButton button:hover {
        background-color: #f4f5f6 !important;
        border-color: #c0bfbf !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. SISTEMA DE AUTENTICACIÓN ---
if not st.session_state.autenticado:
    st.markdown('<div style="max-width:400px; margin:auto; padding-top:100px;">', unsafe_allow_html=True)
    st.image(LOGO_UJAT_URL, width=90)
    st.markdown("### Acceso al Portal Clínico DACYTI")
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
    # Cabecera Institucional Fija
    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="35">
            <h1>Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Navegación Lateral Izquierda
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["🏠 Inicio y Planner", "📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Personal Encargado:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.side_peek_modo = None
        st.rerun()

    # =================================================================================
    # MÓDULO: INICIO Y PLANNER DINÁMICO
    # =================================================================================
    if seccion == "🏠 Inicio y Planner":
        
        # Grid fluido que maneja la apertura del Side-Peek deslizable a la derecha
        if st.session_state.side_peek_modo:
            col_izquierda, col_derecha = st.columns([62, 38], gap="medium")
        else:
            col_izquierda = st.container()

        # -----------------------------------------------------------------------------
        # COLUMNA IZQUIERDA: PLANNER PRINCIPAL
        # -----------------------------------------------------------------------------
        with col_izquierda:
            st.markdown("### Panel de la Agenda e Historial Clínico")
            
            c_btn1, c_btn2, _ = st.columns([2, 2, 4])
            with c_btn1:
                if st.button("➕ Nuevo Expediente", use_container_width=True):
                    st.session_state.side_peek_modo = "NUEVO_EXPEDIENTE"
                    st.rerun()
            with c_btn2:
                if st.button("📅 Agendar Nueva Cita", use_container_width=True):
                    st.session_state.side_peek_modo = "NUEVA_CITA"
                    st.rerun()

            st.markdown("---")

            # EXTRACCIÓN DE CITAS GLOBALES DE LA BASE DE DATOS
            conn = conectar_db_local()
            citas_tabla = pd.read_sql_query("""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora ASC
            """, conn)
            conn.close()

            # TABLILLA ESTILO NOTION ASOCIADA A LAS IMÁGENES COMPARTIDAS
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
                    # Filtrar badge según el estado clínico
                    clase_badge = "status-pendiente"
                    if fila['estado'] == "Realizada": clase_badge = "status-realizada"
                    elif fila['estado'] == "Cancelada": clase_badge = "status-cancelada"

                    c_fila1, c_fila2, c_fila3, c_fila4 = st.columns([2, 1.5, 1, 1])
                    with c_fila1:
                        st.markdown(f"<div class='notion-table-row' style='border:none;'>📄 {fila['nombre']}</div>", unsafe_allow_html=True)
                    with c_fila2:
                        st.markdown(f"<div class='notion-table-row' style='border:none; color:#5a5d56;'>{fila['fecha_hora']}</div>", unsafe_allow_html=True)
                    with c_fila3:
                        st.markdown(f"<div class='notion-table-row' style='border:none;'><span class='status-badge {clase_badge}'>{fila['estado']}</span></div>", unsafe_allow_html=True)
                    with c_fila4:
                        if st.button("Ver Detalle", key=f"open_t_{fila['id']}", use_container_width=True):
                            st.session_state.side_peek_modo = "VER_CITA"
                            st.session_state.cita_seleccionada_id = fila['id']
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="background-color: #f7f7f5; padding: 12px; border-left: 4px solid #7c7b77; color: #191919; border-radius: 4px; font-size: 14px;">
                        No se encuentran registros de citas programadas para el día de hoy.
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # PLANNER E INTERFAZ DE CALENDARIOS INTERACTIVOS
            st.markdown("#### 📅 Visualizador de Calendario Clínico")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                tipo_formato = st.selectbox("Formato Ajustado:", ["Mensual (Carga General)", "Semanal (Horario Laboral L-V)"])
            with c_p2:
                fecha_pivote = st.date_input("Fecha Base Enfoque:", value=date.today(), key="pivote_date")

            # Mapear citas indexadas por string de fecha para acceso directo desde cualquier vista
            diccionario_citas_global = {}
            for _, c_act in citas_tabla.iterrows():
                try:
                    dt_c = datetime.strptime(c_act['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                    f_str = dt_c.strftime("%Y-%m-%d")
                    if f_str not in diccionario_citas_global: diccionario_citas_global[f_str] = []
                    diccionario_citas_global[f_str].append(c_act)
                except: pass

            # --- VISTA 1: CALENDARIO MENSUAL ---
            if tipo_formato == "Mensual (Carga General)":
                año_sel, mes_sel = fecha_pivote.year, fecha_pivote.month
                cal_objeto = calendar.Calendar(firstweekday=0)
                semanas_mes = cal_objeto.monthdatescalendar(año_sel, mes_sel)

                dias_semana_nombres = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
                cols_cabecera = st.columns(7)
                for idx, d_nom in enumerate(dias_semana_nombres):
                    cols_cabecera[idx].markdown(f"<center><small><strong>{d_nom}</strong></small></center>", unsafe_allow_html=True)

                for sem_idx, semana in enumerate(semanas_mes):
                    cols_dias = st.columns(7)
                    for dia_idx, f_dia in enumerate(semana):
                        with cols_dias[dia_idx]:
                            if f_dia.month == mes_sel:
                                st.markdown(f"<span style='color:#191919; font-weight:500; font-size:12px;'>{f_dia.day}</span>", unsafe_allow_html=True)
                                f_buscar = f_dia.strftime("%Y-%m-%d")
                                if f_buscar in diccionario_citas_global:
                                    for cita_dia in diccionario_citas_global[f_buscar]:
                                        hora_c = cita_dia['fecha_hora'][11:16]
                                        # Acceso y edición directa desde la cuadrícula mensual
                                        if st.button(f"⏱️ {hora_c}", key=f"cal_m_btn_{cita_dia['id']}", use_container_width=True):
                                            st.session_state.side_peek_modo = "VER_CITA"
                                            st.session_state.cita_seleccionada_id = cita_dia['id']
                                            st.rerun()
                    st.markdown("<hr style='margin:4px 0; border-top:1px dashed #e3e2e0;'>", unsafe_allow_html=True)

            # --- VISTA 2: CALENDARIO SEMANAL LABORAL (LUNES A VIERNES) ---
            elif tipo_formato == "Semanal (Horario Laboral L-V)":
                # Calcular el lunes de la semana actual basado en la fecha seleccionada
                inicio_semana = fecha_pivote - timedelta(days=fecha_pivote.weekday())
                
                # Desplegar únicamente de Lunes (0) a Viernes (4)
                dias_laborales = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
                cols_semana = st.columns(5)
                
                for idx, nom_dia in enumerate(dias_laborales):
                    fecha_dia_actual = inicio_semana + timedelta(days=idx)
                    f_buscar_semana = fecha_dia_actual.strftime("%Y-%m-%d")
                    
                    with cols_semana[idx]:
                        st.markdown(f"<center><div style='background-color:#f7f7f5; padding:6px; border-radius:4px;'><strong>{nom_dia}</strong><br><small>{fecha_dia_actual.day} de {calendar.month_name[fecha_dia_actual.month][:3]}</small></div></center>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        if f_buscar_semana in diccionario_citas_global:
                            for cita_sem in diccionario_citas_global[f_buscar_semana]:
                                hora_s = cita_sem['fecha_hora'][11:16]
                                # Acceso y edición directa desde la cuadrícula semanal
                                if st.button(f"{hora_s} - {cita_sem['nombre'][:12]}...", key=f"cal_s_btn_{cita_sem['id']}", use_container_width=True):
                                    st.session_state.side_peek_modo = "VER_CITA"
                                    st.session_state.cita_seleccionada_id = cita_sem['id']
                                    st.rerun()
                        else:
                            st.markdown("<center><span style='color:#a0a0a0; font-size:12px;'>Sin citas</span></center>", unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # COLUMNA DERECHA: APARTADO COMPLETO DEL SIDE-PEEK ESTILO NOTION PANEL
        # -----------------------------------------------------------------------------
        if st.session_state.side_peek_modo:
            with col_derecha:
                # Fila de comandos superior para control del panel deslizable
                c_tit, c_close = st.columns([3.8, 1.6])
                with c_tit:
                    if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                        st.markdown("<h4 style='margin:0;'>📝 Registro de Expediente</h4>", unsafe_allow_html=True)
                    elif st.session_state.side_peek_modo == "VER_CITA":
                        st.markdown("<h4 style='margin:0;'>📄 Evaluación Clínica</h4>", unsafe_allow_html=True)
                    elif st.session_state.side_peek_modo == "NUEVA_CITA":
                        st.markdown("<h4 style='margin:0;'>📅 Nueva Consulta</h4>", unsafe_allow_html=True)
                with c_close:
                    if st.button("Retraer >>", key="btn_close_panel_global", use_container_width=True):
                        st.session_state.side_peek_modo = None
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()
                
                # --- FORMULARIO SIDE-PEEK: NUEVO EXPEDIENTE ---
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

                # --- FORMULARIO SIDE-PEEK: VER / EDITAR CITA SELECCIONADA ---
                elif st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id:
                    conn = conectar_db_local()
                    datos_cita = conn.cursor().execute("""
                        SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id, e.matricula
                        FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                    """, (st.session_state.cita_seleccionada_id,)).fetchone()
                    conn.close()

                    if datos_cita:
                        st.caption(f"✨ Paciente: {datos_cita[1]} | Matrícula: {datos_cita[8]}")
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

                # --- FORMULARIO SIDE-PEEK: AGENDAR NUEVA CITA ---
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
    # OTROS MÓDULOS DE GESTIÓN (DATAFRAMES CON CONTROLES DE DESCARGA LIBERADOS)
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h3>Repositorio General de Expedientes Clínicos</h3>", unsafe_allow_html=True)
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
        st.markdown("<h3>Control de Citas Clínicas e Historial de Sesiones</h3>", unsafe_allow_html=True)
        st.info("Utilice el panel principal '🏠 Inicio y Planner' para desplegar la ventana lateral interactiva de forma óptima.")

    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("<h3>Panel de Métricas y Estadísticas</h3>", unsafe_allow_html=True)
        st.write("Módulo en desarrollo para la generación de analíticas semestrales institucionales.")