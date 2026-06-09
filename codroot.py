# =================================================================
#    SISTEMA COMPLETO: Consultorio Psicológico DACYTI (UJAT)
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import sqlite3

# URL Oficial del Escudo UJAT
LOGO_UJAT_URL = "https://images.seeklogo.com/logo-png/23/1/ujat-tabasco-logo-png_seeklogo-233582.png"

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Consultorio Psicológico DACYTI",
    page_icon=LOGO_UJAT_URL,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MOTOR DE CONEXIÓN LOCAL Y MIGRACIÓN DE BD ---
def conectar_db_local():
    try:
        return sqlite3.connect("centro_psicologico.db")
    except Exception as e:
        st.error(f"Error al conectar a la base de datos institucional: {e}")
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

# Estados del Side Peek: None, "VER_CITA", "NUEVO_EXPEDIENTE", "NUEVA_CITA"
if "side_peek_modo" not in st.session_state: st.session_state.side_peek_modo = None
if "cita_seleccionada_id" not in st.session_state: st.session_state.cita_seleccionada_id = None

ESTRUCTURA_UJAT = {
    "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
    "DAIA": ["Ingeniería Mecánica Eléctrica", "Ingeniería Civil", "Ingeniería Química", "Ingeniería Ambiental"],
    "DACB": ["Licenciatura en Ciencias Computacionales", "Licenciatura en Matemáticas", "Licenciatura en Física"]
}

# -------------------------------------------------------------------------------------
# INYECCIÓN MAESTRA DE CSS - AJUSTADA CON EL BOTÓN NOTION DE COLAPSAR
# -------------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Fondo e interfaz clara y limpia */
    .stApp { background-color: #ffffff !important; }
    
    /* Reset de formularios */
    div[data-testid="stForm"] { background-color: #ffffff !important; border: 1px solid #e9e9e8 !important; }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #fafafa !important;
        border: 1px solid #e0e0e0 !important;
        color: #37352f !important;
    }
    
    /* Barra lateral izquierda */
    [data-testid="stSidebar"] { 
        background-color: #f4f5f6 !important; 
        border-right: 1px solid #e9e9e8; 
    }
    
    /* Tipografías Notion */
    div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, h1, h3, h4, h5, span { 
        color: #37352f !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Botones generales minimalistas */
    div.stButton > button, .stButton button {
        background-color: #ffffff !important;
        color: #37352f !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 5px !important;
        font-size: 13px !important;
    }
    
    /* ESTILIZADO DE DOBLE FLECHA NOTION (BOTÓN MINIMIZAR) */
    .notion-close-trigger button {
        border: none !important;
        background: transparent !important;
        font-size: 18px !important;
        color: #7c7b77 !important;
        padding: 4px 8px !important;
        border-radius: 4px !important;
        transition: background 0.2s ease;
    }
    .notion-close-trigger button:hover {
        background-color: #efeee3 !important;
        color: #37352f !important;
    }

    /* CAPA DE DETECCIÓN CLIC AFUERA (FONDO) */
    .side-peek-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0,0,0,0.08);
        z-index: 9999;
    }

    /* VENTANA LATERAL FLOTANTE SUPERPUESTA CON SCROLL INDEPENDIENTE */
    .side-peek-floating {
        position: fixed;
        top: 0;
        right: 0;
        width: 480px;
        height: 100vh;
        background-color: #fbfbfa !important;
        box-shadow: -8px 0px 30px rgba(0,0,0,0.06);
        border-left: 1px solid #e3e2e0;
        z-index: 10000;
        padding: 24px;
        overflow-y: auto; /* Scroll vertical si el formulario se extiende */
        box-sizing: border-box;
    }
    
    /* Estilos de cabeceras y tablas */
    .constante-header-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
        border-bottom: 1px solid #e9e9e8;
        padding-bottom: 10px;
    }
    .constante-header-container h1 { margin: 0 !important; font-size: 22px; font-weight: 600; }
    
    .notion-table-header {
        display: flex; 
        background-color: #f7f7f5; 
        font-weight: 600; 
        padding: 8px 12px; 
        border-bottom: 1px solid #e9e9e8; 
        font-size: 13px; 
        color: #6a6a65;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.autenticado:
    # --- PROCESO DE ACCESO SEGURO ---
    st.markdown('<div style="max-width:400px; margin:auto; padding-top:100px;">', unsafe_allow_html=True)
    st.image(LOGO_UJAT_URL, width=90)
    st.markdown("### Acceso al Portal Clínico DACYTI")
    u_login = st.text_input("Usuario Corporativo:")
    p_login = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar Sistema"):
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
    # Renderizado de Cabecera Fija
    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="35">
            <h1>Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Navegación del Panel Lateral Izquierdo
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["🏠 Inicio y Planner", "📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Profesional:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.side_peek_modo = None
        st.rerun()

    # =================================================================================
    # MÓDULO 0: INICIO Y PLANNER DINÁMICO
    # =================================================================================
    if seccion == "🏠 Inicio y Planner":
        col_principal = st.container()

        with col_principal:
            st.markdown("### Panel de la Agenda e Historial Clínico")
            
            c_btn1, c_btn2, _ = st.columns([1, 1, 2])
            with c_btn1:
                if st.button("➕ Nuevo Expediente", use_container_width=True):
                    st.session_state.side_peek_modo = "NUEVO_EXPEDIENTE" if st.session_state.side_peek_modo != "NUEVO_EXPEDIENTE" else None
                    st.rerun()
            with c_btn2:
                if st.button("📅 Agendar Nueva Cita", use_container_width=True):
                    st.session_state.side_peek_modo = "NUEVA_CITA" if st.session_state.side_peek_modo != "NUEVA_CITA" else None
                    st.rerun()

            st.markdown("---")

            # --- TABLILLA DE CITAS PROGRAMADAS ---
            st.markdown("#### 📄 Citas Programadas")
            conn = conectar_db_local()
            citas_tabla = pd.read_sql_query("""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora ASC
            """, conn)
            conn.close()

            if not citas_tabla.empty:
                st.markdown("""
                    <div class="notion-table-header">
                        <div style="flex: 2;">Aa Nombre de Paciente</div>
                        <div style="flex: 1.5;">📅 Fecha y Hora</div>
                        <div style="flex: 1;">✨ Estado</div>
                        <div style="flex: 1; text-align: center;">⚙️ Gestión</div>
                    </div>
                """, unsafe_allow_html=True)

                for _, fila in citas_tabla.iterrows():
                    c_fila1, c_fila2, c_fila3, c_fila4 = st.columns([2, 1.5, 1, 1])
                    with c_fila1:
                        st.markdown(f"<div style='padding-top:6px; font-size:14px;'>📄 {fila['nombre']}</div>", unsafe_allow_html=True)
                    with c_fila2:
                        st.markdown(f"<div style='padding-top:6px; font-size:14px; color:#5a5d56;'>{fila['fecha_hora']}</div>", unsafe_allow_html=True)
                    with c_fila3:
                        st.markdown(f"<div style='padding-top:6px;'><span class='badge-notion badge-progress'>{fila['estado']}</span></div>", unsafe_allow_html=True)
                    with c_fila4:
                        if st.button("📄 Abrir", key=f"open_t_{fila['id']}", use_container_width=True):
                            st.session_state.side_peek_modo = "VER_CITA"
                            st.session_state.cita_seleccionada_id = fila['id']
                            st.rerun()
            else:
                st.info("No hay registros de consultas en la base de datos.")

            st.markdown("---")

            # --- PLANNER CLÍNICO (CALENDARIO) ---
            st.markdown("#### 📅 Visualizador de Calendario Clínico")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                tipo_formato = st.selectbox("Formato Ajustado:", ["Mensual (Cuadrícula General)", "Semanal (Horario Laboral L-V)"])
            with c_p2:
                fecha_pivote = st.date_input("Fecha Base Enfoque:", value=date.today(), key="pivote_date")

            if tipo_formato == "Mensual (Cuadrícula General)":
                año_sel, mes_sel = fecha_pivote.year, fecha_pivote.month
                cal_objeto = calendar.Calendar(firstweekday=0)
                semanas_mes = cal_objeto.monthdatescalendar(año_sel, mes_sel)

                diccionario_citas_mes = {}
                for _, c_act in citas_tabla.iterrows():
                    try:
                        dt_c = datetime.strptime(c_act['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                        f_str = dt_c.strftime("%Y-%m-%d")
                        if f_str not in diccionario_citas_mes: diccionario_citas_mes[f_str] = []
                        diccionario_citas_mes[f_str].append(c_act)
                    except: pass

                dias_semana_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                cols_cabecera = st.columns(7)
                for idx, d_nom in enumerate(dias_semana_nombres):
                    cols_cabecera[idx].markdown(f"<center><strong>{d_nom}</strong></center>", unsafe_allow_html=True)

                for sem_idx, semana in enumerate(semanas_mes):
                    cols_dias = st.columns(7)
                    for dia_idx, f_dia in enumerate(semana):
                        with cols_dias[dia_idx]:
                            if f_dia.month == mes_sel:
                                st.markdown(f"<span style='color:#6a6a65; font-size:12px;'>{f_dia.day}</span>", unsafe_allow_html=True)
                                f_buscar = f_dia.strftime("%Y-%m-%d")
                                if f_buscar in diccionario_citas_mes:
                                    for cita_dia in diccionario_citas_mes[f_buscar]:
                                        hora_c = cita_dia['fecha_hora'][11:16]
                                        if st.button(f"⏱️ {hora_c}\n{cita_dia['nombre'][:12]}...", key=f"cal_btn_{cita_dia['id']}", use_container_width=True):
                                            st.session_state.side_peek_modo = "VER_CITA"
                                            st.session_state.cita_seleccionada_id = cita_dia['id']
                                            st.rerun()
                    st.markdown("<hr style='margin:4px 0; border-top:1px solid #f1f1ef;'>", unsafe_allow_html=True)

        # =================================================================================
        # RENDERIZADO DE LA VENTANA EMERGENTE (SIDE PEEK) SUPERPUESTA
        # =================================================================================
        if st.session_state.side_peek_modo:
            # 1. Capa invisible trasera para capturar clics afuera
            st.markdown('<div class="side-peek-overlay"></div>', unsafe_allow_html=True)
            
            # 2. Contenedor Flotante Side Peek
            st.markdown('<div class="side-peek-floating">', unsafe_allow_html=True)
            
            # 3. Encabezado del Side Peek con el nuevo botón Notion deslizante de doble flecha
            col_head_btn, col_head_space = st.columns([1, 4])
            with col_head_btn:
                st.markdown('<div class="notion-close-trigger">', unsafe_allow_html=True)
                # Al pulsar las flechas de colapsar, reseteamos el estado para minimizar la ventana
                if st.button("»", key="close_side_peek_notion_style", help="Cerrar vista lateral"):
                    st.session_state.side_peek_modo = None
                    st.session_state.cita_seleccionada_id = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            # --- CASO A: FORMULARIO LARGO PARA NUEVO EXPEDIENTE ---
            if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                st.markdown("### 📄 Abrir Nuevo Expediente Clínico")
                st.caption("Complete todos los campos del alumno universitario.")
                
                exp_nom = st.text_input("Nombre Completo del Alumno:", key="f_exp_nom")
                exp_mat = st.text_input("Matrícula Institucional Única:", key="f_exp_mat")
                
                c_form_1, c_form_2 = st.columns(2)
                with c_form_1:
                    exp_edad = st.number_input("Edad:", min_value=15, max_value=60, value=20, key="f_exp_edad")
                with c_form_2:
                    exp_gen = st.selectbox("Género Biológico:", ["Masculino", "Femenino", "Otro"], key="f_exp_gen")
                
                exp_div = st.selectbox("División Académica:", list(ESTRUCTURA_UJAT.keys()), key="f_exp_div")
                exp_car = st.selectbox("Carrera Universitaria:", ESTRUCTURA_UJAT[exp_div], key="f_exp_car")
                exp_sem = st.selectbox("Semestre Activo:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="f_exp_sem")
                
                exp_tel = st.text_input("Teléfono Móvil:", key="f_exp_tel")
                exp_cor = st.text_input("Correo Institucional:", key="f_exp_cor")
                exp_tag = st.text_input("Diagnóstico (Etiquetas separadas por comas):", key="f_exp_tag")
                
                # Mapeado a la columna motivo_consulta corregida
                exp_obs = st.text_area("Motivo de Consulta:", height=120, key="f_exp_obs")
                
                st.markdown("---")
                if st.button("Guardar Registro de Expediente", use_container_width=True, key="btn_guardar_exp_final"):
                    if exp_mat.strip() and exp_nom.strip():
                        conn = conectar_db_local()
                        try:
                            tags_p = ",".join([t.strip().lower() for t in exp_tag.split(",") if t.strip()])
                            conn.cursor().execute("""
                                INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (exp_mat.strip(), exp_nom.strip(), exp_gen, int(exp_edad), exp_div, exp_car, exp_sem, exp_tel, exp_cor, exp_obs, tags_p))
                            conn.commit()
                            st.success("¡Expediente creado con éxito!")
                            st.session_state.side_peek_modo = None
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Error: La matrícula ingresada ya se encuentra registrada.")
                        finally: conn.close()
                    else:
                        st.warning("El Nombre y la Matrícula son campos requeridos.")

            # --- CASO B: VER / EDITAR DETALLES DE CITA ---
            elif st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id:
                conn = conectar_db_local()
                datos_cita = conn.cursor().execute("""
                    SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id, e.matricula
                    FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                """, (st.session_state.cita_seleccionada_id,)).fetchone()
                conn.close()

                if datos_cita:
                    st.markdown(f"## {datos_cita[1]}")
                    st.caption(f"Matrícula del Estudiante: {datos_cita[8]}")
                    st.markdown("---")
                    
                    peek_estado = st.selectbox("Estado de Consulta:", ["Pendiente", "Realizada", "Cancelada", "No Asistió"], index=["Pendiente", "Realizada", "Cancelada", "No Asistió"].index(datos_cita[3]), key="f_ver_estado")
                    peek_fecha = st.text_input("Fecha y Hora Asignada:", value=datos_cita[2], disabled=True, key="f_ver_fecha")
                    peek_motivo = st.text_area("Motivo Clínico registrado:", value=datos_cita[4], disabled=True, key="f_ver_motivo")
                    peek_notas = st.text_area("Notas Clínicas y Evolución:", value=datos_cita[5], height=150, key="f_ver_notas")
                    peek_tags = st.text_input("Modificar Etiquetas de Diagnóstico:", value=datos_cita[6], key="f_ver_tags")

                    if st.button("Sincronizar Cambios Clínicos", use_container_width=True, key="btn_actualizar_cita_final"):
                        conn = conectar_db_local()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (peek_estado, peek_notas, datos_cita[0]))
                        cursor.execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (peek_tags.strip().lower(), datos_cita[7]))
                        conn.commit()
                        conn.close()
                        st.success("Base de datos actualizada correctamente.")
                        st.session_state.side_peek_modo = None
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # --- RESTO DE LOS MÓDULOS DEL CONSULTORIO ---
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
        st.info("Utilice el panel principal '🏠 Inicio y Planner' para desplegar la ventana lateral interactiva.")

    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("<h3>Panel de Métricas y Estadísticas Multidimensionales</h3>", unsafe_allow_html=True)