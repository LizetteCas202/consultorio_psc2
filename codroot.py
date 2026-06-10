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
        
        # 2. Crear tabla de expedientes con esquema corregido (Motivo de consulta)
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
        
        # 3. Crear tabla de citas
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
        
        # Insertar usuario por defecto si no existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = 'psicologa.sara'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave_hash, rol, pregunta_secreta, respuesta_secreta_hash)
                VALUES ('psicologa.sara', 'admin123', 'Director/Psicólogo', '¿Unidad de origen?', 'chontalpa')
            """)
        conn.commit()
        conn.close()

# Inicializar Base de Datos automáticamente
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
        "Licenciatura en Arquitectura"
    ],
    "DACB": [
        "Licenciatura en Ciencias Computacionales",
        "Licenciatura en Matemáticas",
        "Licenciatura en Física",
        "Licenciatura en Químico Farmacéutico Biólogo"
    ]
}

# --- 4. INYECCIÓN MAESTRA DE CSS (AESTHETIC & NOTION STYLE) ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stCanvas"] {
        background-color: #f1f5f9 !important; 
    }
    h1, h2, h3, h4, h5, h6, p, span, label, strong, li, [data-testid="stMarkdownContainer"] p {
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
    }
    .stButton button *, div[data-testid="stForm"] button * {
        color: #ffffff !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important; 
        color: #0f172a !important;            
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        -webkit-text-fill-color: #0f172a !important; 
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important; 
        color: #0f172a !important;            
        border: 1px solid #cbd5e1 !important;
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
        color: #475569 !important;
    }
    .notion-table-row {
        display: flex;
        align-items: center;
        padding: 8px 14px;
        color: #0f172a !important;
    }
    .metric-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. PORTAL DE ACCESO (LOGIN) ---
if not st.session_state.autenticado:
    st.markdown('<div style="max-width:400px; margin:auto; padding-top:100px;">', unsafe_allow_html=True)
    try: st.image(LOGO_UJAT_URL, width=110)
    except: st.write("🔺 **UJAT Portal Clínico**")
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
    # Cabecera Institucional Fija
    st.markdown(f"""
        <div class="constante-header-container">
            <h1 style="color:#0f172a !important; margin:0; font-size:24px;">🧠 Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # --- NAVEGACIÓN COMPLETA RECONSTRUIDA ---
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", [
        "🏠 Inicio y Planner", 
        "📋 Expedientes Electrónicos", 
        "📅 Agenda de Citas", 
        "📊 Estadísticas Dashboard"
    ])
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Usuario:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.side_peek_modo = None
        st.rerun()

    # =================================================================================
    # MÓDULO 1: INICIO Y PLANNER DINÁMICO
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

            st.markdown("#### 📄 Próximas Citas Programadas")
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
                st.info("No se encuentran registros de citas programadas en la base de datos.")

            st.markdown("---")

            # CALENDARIO MENSUAL/SEMANAL
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
                    cols_cabecera[idx].markdown(f"<center><strong>{d_nom}</strong></center>", unsafe_allow_html=True)

                for sem_idx, semana in enumerate(semanas_mes):
                    cols_dias = st.columns(7)
                    for dia_idx, f_dia in enumerate(semana):
                        with cols_dias[dia_idx]:
                            if f_dia.month == mes_sel:
                                st.markdown(f"**{f_dia.day}**")
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
                        st.markdown(f"<center><div style='background-color:#ffffff; padding:6px; border:1px solid #e2e8f0; border-radius:4px;'><strong>{nom_dia}</strong><br><small>{fecha_dia_actual.day} de {calendar.month_name[fecha_dia_actual.month][:3]}</small></div></center>", unsafe_allow_html=True)
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

        # Panel desplegable lateral (Side-Peek)
        if st.session_state.side_peek_modo:
            with col_derecha:
                c_tit, c_close = st.columns([3.5, 1.5])
                with c_tit:
                    st.markdown(f"#### 📝 Acción: {st.session_state.side_peek_modo}")
                with c_close:
                    if st.button("Retraer >>", use_container_width=True):
                        st.session_state.side_peek_modo = None
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()
                
                if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                    st.markdown('<div class="custom-card-form">', unsafe_allow_html=True)
                    exp_nom = st.text_input("Nombre Completo:")
                    exp_mat = st.text_input("Matrícula:")
                    exp_edad = st.number_input("Edad:", min_value=15, max_value=60, value=20)
                    exp_gen = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
                    exp_div = st.selectbox("División:", options=["DACYTI", "DAIA", "DACB"])
                    exp_car = st.selectbox("Carrera:", options=CARRERAS_POR_DIVISION.get(exp_div, []))
                    exp_sem = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"])
                    exp_tel = st.text_input("Teléfono:")
                    exp_cor = st.text_input("Correo:")
                    exp_tag = st.text_input("Etiquetas Diagnósticas (comas):")
                    exp_obs = st.text_area("Motivo de Consulta:")
                    
                    if st.button("Guardar Alumno", use_container_width=True):
                        if exp_mat.strip() and exp_nom.strip():
                            conn = conectar_db_local()
                            try:
                                conn.cursor().execute("""
                                    INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (exp_mat.strip(), exp_nom.strip(), exp_gen, int(exp_edad), exp_div, exp_car, exp_sem, exp_tel, exp_cor, exp_obs, exp_tag.strip().lower()))
                                conn.commit()
                                st.success("¡Expediente Creado!")
                                st.session_state.side_peek_modo = None
                                st.rerun()
                            except: st.error("Matrícula ya existente.")
                            finally: conn.close()
                    st.markdown('</div>', unsafe_allow_html=True)

                elif st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id:
                    conn = conectar_db_local()
                    datos_cita = conn.cursor().execute("""
                        SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id
                        FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                    """, (st.session_state.cita_seleccionada_id,)).fetchone()
                    conn.close()

                    if datos_cita:
                        st.markdown(f"**Paciente:** {datos_cita[1]}")
                        with st.form("form_edicion_rapida"):
                            peek_est = st.selectbox("Estado Cita:", ["Pendiente", "Realizada", "Cancelada"], index=["Pendiente", "Realizada", "Cancelada"].index(datos_cita[3]))
                            peek_not = st.text_area("Notas Clínicas / Evolución:", value=datos_cita[5])
                            peek_tag = st.text_input("Etiquetas Clínicas / Diagnósticos:", value=datos_cita[6])
                            if st.form_submit_button("Actualizar Historial"):
                                conn = conectar_db_local()
                                conn.cursor().execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (peek_est, peek_not, datos_cita[0]))
                                conn.cursor().execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (peek_tag.strip().lower(), datos_cita[7]))
                                conn.commit()
                                conn.close()
                                st.session_state.side_peek_modo = None
                                st.success("¡Datos actualizados!")
                                st.rerun()

                elif st.session_state.side_peek_modo == "NUEVA_CITA":
                    st.markdown('<div class="custom-card-form">', unsafe_allow_html=True)
                    mat_b = st.text_input("Ingresa Matrícula del Alumno:").strip()
                    if mat_b:
                        conn = conectar_db_local()
                        al = conn.cursor().execute("SELECT id, nombre FROM expedientes WHERE matricula = ?", (mat_b,)).fetchone()
                        conn.close()
                        if al:
                            st.success(f"Paciente: {al[1]}")
                            with st.form("form_alta_c"):
                                f_c = st.date_input("Fecha:")
                                h_c = st.time_input("Hora:")
                                m_c = st.text_area("Motivo o Síntomas:")
                                if st.form_submit_button("Agendar Cita"):
                                    conn = conectar_db_local()
                                    fh = f"{f_c} {h_c.strftime('%H:%M:%S')}"
                                    conn.cursor().execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)", (al[0], fh, m_c))
                                    conn.commit()
                                    conn.close()
                                    st.session_state.side_peek_modo = None
                                    st.rerun()
                        else: st.error("No existe esa matrícula.")
                    st.markdown('</div>', unsafe_allow_html=True)

    # =================================================================================
    # MÓDULO 2: 📋 EXPEDIENTES ELECTRÓNICOS
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("### 📋 Registro Histórico de Expedientes Clínicos")
        col_db, col_reg = st.columns([60, 40], gap="large")

        with col_db:
            st.markdown("#### 🔍 Expedientes en la Base de Datos")
            conn = conectar_db_local()
            expedientes_df = pd.read_sql_query("""
                SELECT matricula as 'Matrícula', nombre as 'Nombre Alumno', 
                       genero as 'Género', edad as 'Edad', division as 'División', 
                       carrera as 'Carrera', semestre as 'Semestre', observaciones as 'Motivo Consulta', 
                       etiquetas as 'Etiquetas' FROM expedientes ORDER BY id DESC
            """, conn)
            conn.close()

            if not expedientes_df.empty:
                st.dataframe(expedientes_df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay expedientes clínicos registrados aún.")

        with col_reg:
            st.markdown("#### ➕ Alta de Expediente")
            with st.form("form_reg_directo"):
                reg_nom = st.text_input("Nombre Completo:")
                reg_mat = st.text_input("Matrícula:")
                reg_edad = st.number_input("Edad:", min_value=16, max_value=65, value=20)
                reg_gen = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
                reg_div = st.selectbox("División Académica:", options=["DACYTI", "DAIA", "DACB"])
                reg_car = st.selectbox("Carrera Universitaria:", options=CARRERAS_POR_DIVISION.get(reg_div, []))
                reg_sem = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"])
                reg_tel = st.text_input("Teléfono:")
                reg_cor = st.text_input("Correo:")
                reg_tag = st.text_input("Etiquetas Diagnósticas (comas):")
                reg_obs = st.text_area("Motivo de Consulta Inicial:")

                if st.form_submit_button("Guardar e Insertar"):
                    if reg_nom.strip() and reg_mat.strip():
                        conn = conectar_db_local()
                        try:
                            conn.cursor().execute("""
                                INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (reg_mat.strip(), reg_nom.strip(), reg_gen, int(reg_edad), reg_div, reg_car, reg_sem, reg_tel, reg_cor, reg_obs, reg_tag.strip().lower()))
                            conn.commit()
                            st.success("¡Registrado!")
                            st.rerun()
                        except: st.error("Matrícula duplicada.")
                        finally: conn.close()

    # =================================================================================
    # MÓDULO 3: 📅 AGENDA DE CITAS (COMPLETO Y RESTAURADO)
    # =================================================================================
    elif seccion == "📅 Agenda de Citas":
        st.markdown("### 📅 Programación y Control de Citas Clínicas")
        
        c_crear, c_lista = st.columns([40, 60], gap="large")
        
        with c_crear:
            st.markdown("#### 📋 Agendar Nueva Sesión")
            with st.form("form_modulo_citas_directo"):
                c_mat = st.text_input("Matrícula del Alumno Pasante/Estudiante:").strip()
                c_fecha = st.date_input("Fecha Programada:", value=date.today())
                c_hora = st.time_input("Hora Programada:")
                c_motivo = st.text_area("Motivo de la sesión o Sintomatología reportada:")
                
                if st.form_submit_button("Confirmar y Guardar Cita", use_container_width=True):
                    if c_mat:
                        conn = conectar_db_local()
                        al_datos = conn.cursor().execute("SELECT id FROM expedientes WHERE matricula = ?", (c_mat,)).fetchone()
                        if al_datos:
                            fh_completa = f"{c_fecha} {c_hora.strftime('%H:%M:%S')}"
                            conn.cursor().execute("""
                                INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) 
                                VALUES (?, ?, 'Pendiente', ?)
                            """, (al_datos[0], fh_completa, c_motivo))
                            conn.commit()
                            st.success("¡Cita programada con éxito en la base de datos!")
                        else:
                            st.error("Error: La matrícula ingresada no cuenta con un expediente base. Regístralo primero.")
                        conn.close()
                    else:
                        st.warning("Por favor, digite una matrícula institucional válida.")

        with c_lista:
            st.markdown("#### 📜 Historial Clínico de Sesiones")
            conn = conectar_db_local()
            todas_citas_df = pd.read_sql_query("""
                SELECT c.id as 'ID Cita', e.matricula as 'Matrícula', e.nombre as 'Alumno', 
                       c.fecha_hora as 'Fecha/Hora', c.estado as 'Estado', c.motivo as 'Motivo Sesión',
                       c.notas_evolucion as 'Notas Clínicas'
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora DESC
            """, conn)
            conn.close()

            if not todas_citas_df.empty:
                st.dataframe(todas_citas_df, use_container_width=True, hide_index=True)
                
                st.markdown("#### 📑 Modificar Estado de una Citas Rápidamente")
                c_id_sel = st.number_input("Digitar ID de Cita a modificar:", min_value=1, step=1)
                c_est_sel = st.selectbox("Nuevo Estado Clínico:", ["Pendiente", "Realizada", "Cancelada", "No Asistió"])
                if st.button("Actualizar Estado"):
                    conn = conectar_db_local()
                    conn.cursor().execute("UPDATE citas SET estado = ? WHERE id = ?", (c_est_sel, int(c_id_sel)))
                    conn.commit()
                    conn.close()
                    st.success(f"Cita {c_id_sel} cambiada a {c_est_sel}")
                    st.rerun()
            else:
                st.info("No se registran citas programadas en la bitácora.")

    # =================================================================================
    # MÓDULO 4: 📊 ESTADÍSTICAS DASHBOARD (RECONSTRUIDO CON GÉNERO, EDAD, CARRERA, DIVISIÓN Y DIAGNÓSTICO)
    # =================================================================================
    elif seccion == "📊 Estadísticas Dashboard":
        st.markdown("### 📊 Indicadores Clínicos y Demográficos de Estudiantes (UJAT)")
        st.markdown("Análisis en tiempo real de la población estudiantil atendida en el consultorio.")
        
        conn = conectar_db_local()
        df_exp = pd.read_sql_query("SELECT * FROM expedientes", conn)
        df_cit = pd.read_sql_query("SELECT * FROM citas", conn)
        conn.close()
        
        if df_exp.empty:
            st.warning("Se requieren datos guardados en los expedientes para poder estructurar y graficar las métricas institucionales.")
        else:
            # Tarjetas de Kpis Generales
            st.markdown("---")
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.markdown(f'<div class="metric-box"><h3>{len(df_exp)}</h3><p>Total de Alumnos Registrados</p></div>', unsafe_allow_html=True)
            with kpi2:
                st.markdown(f'<div class="metric-box"><h3>{len(df_cit)}</h3><p>Total de Sesiones Agendadas</p></div>', unsafe_allow_html=True)
            with kpi3:
                atendidas = len(df_cit[df_cit['estado'] == 'Realizada']) if not df_cit.empty else 0
                st.markdown(f'<div class="metric-box"><h3>{atendidas}</h3><p>Sesiones Clínicas Completadas</p></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # FILAS DE GRÁFICOS INTERACTIVOS
            col_g1, col_g2 = st.columns(2, gap="large")
            
            with col_g1:
                st.markdown("#### ⚧️ Distribución por Género")
                gen_counts = df_exp['genero'].value_counts()
                st.bar_chart(gen_counts, color="#0f172a")
                
                st.markdown("#### 🎂 Prevalencia de Atenciones por Edad")
                edad_counts = df_exp['edad'].value_counts().sort_index()
                st.line_chart(edad_counts, color="#1e293b")

            with col_g2:
                st.markdown("#### 🏫 Impacto por División Académica")
                div_counts = df_exp['division'].value_counts()
                st.bar_chart(div_counts, color="#334155")
                
                st.markdown("#### 🎓 Alumnos Atendidos por Carrera Universitaria")
                car_counts = df_exp['carrera'].value_counts()
                st.bar_chart(car_counts, color="#475569")
            
            st.markdown("---")
            
            # ANÁLISIS DINÁMICO DE DIAGNÓSTICOS (ETIQUETAS RECOLECTADAS)
            st.markdown("#### 🔍 Mapeo General de Diagnósticos y Sintomatologías (Etiquetas)")
            
            lista_diagnosticos = []
            for tags_row in df_exp['etiquetas'].dropna():
                if tags_row.strip():
                    # Separar por comas y limpiar espacios vacíos
                    lista_diagnosticos.extend([t.strip().capitalize() for t in tags_row.split(",") if t.strip()])
            
            if lista_diagnosticos:
                df_diag = pd.DataFrame(lista_diagnosticos, columns=["Diagnóstico / Síntoma"])
                diag_counts = df_diag["Diagnóstico / Síntoma"].value_counts()
                
                col_t1, col_t2 = st.columns([4, 6])
                with col_t1:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.dataframe(diag_counts, use_container_width=True)
                with col_t2:
                    st.bar_chart(diag_counts, color="#0f172a")
            else:
                st.info("No hay suficientes etiquetas o palabras clave guardadas en los expedientes para trazar la estadística de diagnósticos actuales.")