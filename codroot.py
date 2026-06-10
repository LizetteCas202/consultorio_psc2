# =================================================================
#    SISTEMA DE GESTIÓN: Consultorio Psicológico DACYTI
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import sqlite3
import urllib.parse

# URL Oficial del Escudo UJAT
LOGO_UJAT_URL = "https://images.seeklogo.com/logo-png/23/1/ujat-tabasco-logo-png_seeklogo-233582.png"

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
# Corregido: Se usa un emoji estable para evitar fallos de renderizado en pestañas
st.set_page_config(
    page_title="Consultorio Psicológico DACYTI",
    page_icon="🧠",
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
        
        # 1. Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                clave_hash TEXT NOT NULL,
                rol TEXT NOT NULL,
                pregunta_secreta TEXT,
                respuesta_secreta_hash TEXT
            )
        """)
        
        # 2. Crear tabla de expedientes con esquema corregido
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
        
        # 3. Crear tabla de citas base
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expediente_id INTEGER,
                fecha_hora TEXT,
                estado TEXT DEFAULT 'Pendiente',
                motivo TEXT,
                FOREIGN KEY(expediente_id) REFERENCES expedientes(id)
            )
        """)
        
        # --- MIGRACIÓN AUTOMÁTICA EXTRA Y REPARACIÓN ---
        cursor.execute("PRAGMA table_info(citas)")
        columnas_citas = [col[1] for col in cursor.fetchall()]
        if "notas_evolucion" not in columnas_citas:
            try: cursor.execute("ALTER TABLE citas ADD COLUMN notas_evolucion TEXT DEFAULT ''")
            except: pass

        cursor.execute("PRAGMA table_info(expedientes)")
        columnas_exps = [col[1] for col in cursor.fetchall()]
        if "carrera" not in columnas_exps:
            try: cursor.execute("ALTER TABLE expedientes ADD COLUMN carrera TEXT DEFAULT ''")
            except: pass
        if "etiquetas" not in columnas_exps:
            try: cursor.execute("ALTER TABLE expedientes ADD COLUMN etiquetas TEXT DEFAULT ''")
            except: pass
        if "observaciones" not in columnas_exps:
            try: cursor.execute("ALTER TABLE expedientes ADD COLUMN observaciones TEXT DEFAULT ''")
            except: pass

        # Insertar usuario por defecto si no existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = 'psicologa.sara'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave_hash, rol, pregunta_secreta, respuesta_secreta_hash)
                VALUES ('psicologa.sara', 'admin123', 'Director/Psicólogo', '¿Unidad de origen?', 'chontalpa')
            """)
        conn.commit()
        conn.close()

# Inicializar y reparar Base de Datos automáticamente
inicializar_sistema_db()

# --- 3. CONTROL DE ESTADOS DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = ""
if "side_peek_modo" not in st.session_state: st.session_state.side_peek_modo = None
if "cita_seleccionada_id" not in st.session_state: st.session_state.cita_seleccionada_id = None

CARRERAS_POR_DIVISION = {
    "DACYTI": [
        "Licenciatura en Tecnologías de la Información",
        "Licenciatura en Sistemas Computacionales",
        "Licenciatura en Telemática",
        "Ingeniería en Informática Administrativa"
    ],
    "DAIA": [
        "Ingeniería Civil",
        "Ingeniería Mecánica Eléctrica",
        "Ingeniería Química",
        "Licenciatura en Arquitectura",
        "Ingeniería en Agua"
    ],
    "DACB": [
        "Licenciatura en Ciencias Computacionales",
        "Licenciatura en Matemáticas",
        "Licenciatura en Física",
        "Licenciatura en Químico Farmacéutico Biólogo"
    ]
}

# -------------------------------------------------------------------------------------
# INYECCIÓN MAESTRA DE CSS - REMEDIACIÓN DE AUTOCOMPLETADO Y INPUTS OSCUROS
# -------------------------------------------------------------------------------------
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stCanvas"] {
        background-color: #f1f5f9 !important; 
    }

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
        color: #0f172a !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    [data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    .stButton button, div[data-testid="stForm"] button, div.custom-card-form button {
        background-color: #0f172a !important;
        color: #ffffff !important;             
        font-weight: 600 !important;
        border: 1px solid #0f172a !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stButton button *, div[data-testid="stForm"] button *, div.custom-card-form button * {
        color: #ffffff !important;
    }

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

    input:-webkit-autofill,
    input:-webkit-autofill:hover, 
    input:-webkit-autofill:focus,
    textarea:-webkit-autofill,
    textarea:-webkit-autofill:hover,
    textarea:-webkit-autofill:focus {
        -webkit-text-fill-color: #0f172a !important;
        -webkit-box-shadow: 0 0 0px 1000px #ffffff inset !important;
        transition: background-color 5000s ease-in-out 0s !important;
        background-color: #ffffff !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important; 
        color: #0f172a !important;            
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    
    div[data-baseweb="select"] span {
        color: #0f172a !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], [role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }

    div[data-baseweb="menu"] li, [role="listbox"] li, [role="option"], ul[role="listbox"] span {
        color: #0f172a !important;            
        background-color: #ffffff !important;
        font-weight: 500 !important;
    }

    div[data-testid="stForm"], .custom-card-form { 
        background-color: #ffffff !important; 
        border: 1px solid #e2e8f0 !important;
        box-shadow: -4px 4px 20px rgba(15, 23, 42, 0.06) !important;
        padding: 24px !important;
        border-radius: 8px !important;
        margin-bottom: 20px;
    }

    [data-testid="stSidebar"] { 
        background-color: #f8fafc !important; 
        border-right: 1px solid #e2e8f0 !important; 
    }

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
    </style>
""", unsafe_allow_html=True)

# --- 4. PORTAL DE ACCESO (LOGIN) ---
if not st.session_state.autenticado:
    st.markdown('<div style="max-width:400px; margin:auto; padding-top:100px;">', unsafe_allow_html=True)
    try:
        st.image(LOGO_UJAT_URL, width=110)
    except:
        st.write("🔺 **UJAT Portal Clínico**")
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
    # Cabecera Fija Estable
    st.markdown(f"""
        <div class="constante-header-container">
            <h1 style="color:#0f172a !important; margin:0; font-size:24px;">🧠 Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Navegación Lateral Módulos
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["🏠 Inicio y Planner", "📋 Expedientes Electrónicos"])
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Personal Encargado:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.side_peek_modo = None
        st.rerun()

    # =================================================================================
    # MÓDULO MAIN: INICIO Y PLANNER DINÁMICO
    # =================================================================================
    if seccion == "🏠 Inicio y Planner":
        if st.session_state.side_peek_modo:
            col_izquierda, col_derecha = st.columns([55, 45], gap="medium")
        else:
            col_izquierda = st.container()

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

            # EXTRAER CITAS DESDE SQLITE
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
                    c_fila1, c_fila2, c_fila3, c_fila4 = st.columns([2, 1.5, 1, 1])
                    with c_fila1:
                        st.markdown(f"<div class='notion-table-row'>📄 {fila['nombre']}</div>", unsafe_allow_html=True)
                    with c_fila2:
                        st.markdown(f"<div class='notion-table-row'>{fila['fecha_hora']}</div>", unsafe_allow_html=True)
                    with c_fila3:
                        st.markdown(f"<div class='notion-table-row'>{fila['estado']}</div>", unsafe_allow_html=True)
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

        # Side-Peek Columna Derecha
        if st.session_state.side_peek_modo:
            with col_derecha:
                c_tit, c_close = st.columns([3.5, 1.5])
                with c_tit:
                    if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                        st.markdown("<h4 style='color:#0f172a !important; margin:0; font-weight:700;'>📝 Registro de Expediente</h4>", unsafe_allow_html=True)
                    elif st.session_state.side_peek_modo == "VER_CITA":
                        st.markdown("<h4 style='color:#0f172a !important; margin:0; font-weight:700;'>📄 Evaluación Clínica</h4>", unsafe_allow_html=True)
                    elif st.session_state.side_peek_modo == "NUEVA_CITA":
                        st.markdown("<h4 style='color:#0f172a !important; margin:0; font-weight:700;'>📅 Nueva Agenda</h4>", unsafe_allow_html=True)
                with c_close:
                    if st.button("Retraer >>", key="btn_close_panel_global", use_container_width=True):
                        st.session_state.side_peek_modo = None
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()
                
                # Formulario Side-peek: Nuevo Expediente
                if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                    st.markdown('<div class="custom-card-form">', unsafe_allow_html=True)
                    exp_nom = st.text_input("Nombre Completo del Alumno:")
                    exp_mat = st.text_input("Matrícula Institucional:")
                    cf1, cf2 = st.columns(2)
                    with cf1: exp_edad = st.number_input("Edad:", min_value=15, max_value=60, value=20)
                    with cf2: exp_gen = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
                    
                    lista_divisiones = ["DACYTI", "DAIA", "DACB"]
                    exp_div = st.selectbox("División Académica:", options=lista_divisiones)
                    lista_carreras_filtrada = CARRERAS_POR_DIVISION.get(exp_div, [])
                    exp_car = st.selectbox("Carrera Universitaria:", options=lista_carreras_filtrada)
                    exp_sem = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"])
                    
                    exp_tel = st.text_input("Teléfono de Contacto:")
                    exp_cor = st.text_input("Correo Electrónico:")
                    exp_tag = st.text_input("Etiquetas Diagnósticas (separadas por comas):")
                    exp_obs = st.text_area("Motivo de Consulta Inicial:")
                    
                    if st.button("Registrar Expediente Electrónico", use_container_width=True):
                        if exp_mat.strip() and exp_nom.strip():
                            conn = conectar_db_local()
                            if conn:
                                try:
                                    tags_p = ",".join([t.strip().lower() for t in exp_tag.split(",") if t.strip()])
                                    conn.cursor().execute("""
                                        INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (exp_mat.strip(), exp_nom.strip(), exp_gen, int(exp_edad), exp_div, exp_car, exp_sem, exp_tel, exp_cor, exp_obs, tags_p))
                                    conn.commit()
                                    st.success("¡Expediente guardado exitosamente!")
                                    st.session_state.side_peek_modo = None
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("La matrícula ya existe.")
                                finally: conn.close()
                    st.markdown('</div>', unsafe_allow_html=True)

                # Formulario Side-peek: Ver Cita
                elif st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id:
                    conn = conectar_db_local()
                    datos_cita = conn.cursor().execute("""
                        SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, 
                               IFNULL(c.notas_evolucion, '') as notas_ev, 
                               IFNULL(e.etiquetas, '') as tags, 
                               e.id, e.matricula
                        FROM citas c JOIN expedientes e ON c.expediente_id = e.id 
                        WHERE c.id = ?
                    """, (st.session_state.cita_seleccionada_id,)).fetchone()
                    conn.close()

                    if datos_cita:
                        st.markdown(f"**Paciente:** {datos_cita[1]} | {datos_cita[8]}")
                        with st.form("form_edicion_cita_notion"):
                            peek_estado = st.selectbox("Estado:", ["Pendiente", "Realizada", "Cancelada", "No Asistió"], index=["Pendiente", "Realizada", "Cancelada", "No Asistió"].index(datos_cita[3]))
                            peek_notas = st.text_area("Notas de Evolución Clínica:", value=datos_cita[5], height=150)
                            peek_tags = st.text_input("Etiquetas Diagnósticas:", value=datos_cita[6])
                            if st.form_submit_button("Actualizar Historial"):
                                conn = conectar_db_local()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (peek_estado, peek_notas, datos_cita[0]))
                                cursor.execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (peek_tags.strip().lower(), datos_cita[7]))
                                conn.commit()
                                conn.close()
                                st.session_state.side_peek_modo = None
                                st.success("¡Historial actualizado!")
                                st.rerun()

                # Formulario Side-peek: Nueva Cita
                elif st.session_state.side_peek_modo == "NUEVA_CITA":
                    st.markdown('<div class="custom-card-form">', unsafe_allow_html=True)
                    mat_buscar = st.text_input("Matrícula del Alumno:").strip()
                    if mat_buscar:
                        conn = conectar_db_local()
                        alumno_data = conn.cursor().execute("SELECT id, nombre, division, carrera FROM expedientes WHERE matricula = ?", (mat_buscar,)).fetchone()
                        conn.close()
                        if alumno_data:
                            st.success(f"Localizado: {alumno_data[1]}")
                            with st.form("form_confirm_cita"):
                                f_c = st.date_input("Fecha:", value=date.today())
                                h_c = st.time_input("Hora:")
                                m_c = st.text_area("Motivo:")
                                if st.form_submit_button("Agendar Cita"):
                                    conn = conectar_db_local()
                                    fh_str = f"{f_c} {h_c.strftime('%H:%M:%S')}"
                                    conn.cursor().execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)", (alumno_data[0], fh_str, m_c))
                                    conn.commit()
                                    conn.close()
                                    st.session_state.side_peek_modo = None
                                    st.success("¡Cita agendada!")
                                    st.rerun()
                        else:
                            st.error("Matrícula no encontrada.")
                    st.markdown('</div>', unsafe_allow_html=True)

    # =================================================================================
    # MÓDULO: 📋 EXPEDIENTES ELECTRÓNICOS (REDISEÑADO COMPLETO Y OPERATIVO)
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("### 📋 Registro Histórico de Expedientes Clínicos")
        st.markdown("Consulte el histórico completo de alumnos atendidos o registre uno nuevo directamente en esta sección.")

        # Layout dividido: Izquierda (Base de Datos), Derecha (Registro Rápido)
        col_db, col_reg = st.columns([60, 40], gap="large")

        with col_db:
            st.markdown("#### 🔍 Expedientes en la Base de Datos")
            conn = conectar_db_local()
            expedientes_df = pd.read_sql_query("""
                SELECT matricula as 'Matrícula', nombre as 'Nombre Alumno', 
                       genero as 'Género', edad as 'Edad', division as 'División', 
                       carrera as 'Carrera', semestre as 'Semestre', telefono as 'Teléfono', 
                       correo as 'Correo', observaciones as 'Motivo Consulta', etiquetas as 'Etiquetas' 
                FROM expedientes
                ORDER BY id DESC
            """, conn)
            conn.close()

            if not expedientes_df.empty:
                # Buscador dinámico de apoyo incorporado nativamente en el dataframe de Streamlit
                st.dataframe(
                    expedientes_df,
                    use_container_width=True,
                    hide_index=True
                )
                st.caption(f"💡 Total de expedientes electrónicos almacenados: {len(expedientes_df)}")
            else:
                st.info("No hay expedientes clínicos registrados aún en el sistema.")

        with col_reg:
            st.markdown("#### ➕ Registrar Otro Expediente Directo")
            with st.form("form_registro_directo_expedientes"):
                reg_nom = st.text_input("Nombre Completo del Alumno:")
                reg_mat = st.text_input("Matrícula Institucional:")
                
                c_r1, c_r2 = st.columns(2)
                with c_r1: reg_edad = st.number_input("Edad Alumno:", min_value=16, max_value=65, value=20)
                with c_r2: reg_gen = st.selectbox("Género Alumno:", ["Masculino", "Femenino", "Otro"])
                
                reg_div = st.selectbox("División Académica de origen:", options=["DACYTI", "DAIA", "DACB"])
                reg_car = st.selectbox("Carrera Universitaria inscrita:", options=CARRERAS_POR_DIVISION.get(reg_div, []))
                reg_sem = st.selectbox("Semestre cursando:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"])
                
                reg_tel = st.text_input("Teléfono:")
                reg_cor = st.text_input("Correo Institucional o Personal:")
                reg_tag = st.text_input("Etiquetas o Palabras clave (separadas por comas):", placeholder="ej. estres, adaptacion")
                reg_obs = st.text_area("Motivo de la Consulta:")

                if st.form_submit_button("Guardar y dar de Alta Expediente", use_container_width=True):
                    if reg_nom.strip() and reg_mat.strip():
                        conn = conectar_db_local()
                        if conn:
                            try:
                                tags_procesados = ",".join([t.strip().lower() for t in reg_tag.split(",") if t.strip()])
                                conn.cursor().execute("""
                                    INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (reg_mat.strip(), reg_nom.strip(), reg_gen, int(reg_edad), reg_div, reg_car, reg_sem, reg_tel, reg_cor, reg_obs, tags_procesados))
                                conn.commit()
                                st.success(f"¡Expediente de {reg_nom} dado de alta con éxito!")
                                conn.close()
                                # Forzar recarga inmediata de la pantalla para ver el nuevo registro en la tabla
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Error operativo: La matrícula ya se encuentra registrada en el sistema.")
                            finally:
                                if conn: conn.close()
                    else:
                        st.warning("Los campos de Nombre y Matrícula son estrictamente obligatorios.")