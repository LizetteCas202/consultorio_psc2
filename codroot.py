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

# --- 3. CONTROL DE ESTADOS DE SESIÓN (SIDE PEEK MULTIMODAL SUPERPUESTO) ---
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
# INYECCIÓN MAESTRA DE CSS - VENTANA DE COSTADO SUPERPUESTA CON SCROLL FLOTANTE
# -------------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    /* Fondo e interfaz clara y limpia */
    .stApp {{ background-color: #ffffff !important; }}
    
    /* RESET DE COLORES PARA CONTROLES DE STREAMLIT */
    div[data-testid="stForm"] {{ background-color: #ffffff !important; border: 1px solid #e9e9e8 !important; }}
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {{
        background-color: #fafafa !important;
        border: 1px solid #e0e0e0 !important;
        color: #37352f !important;
    }}
    
    /* BARRA LATERAL IZQUIERDA DE NAVEGACIÓN */
    [data-testid="stSidebar"] {{ 
        background-color: #f4f5f6 !important; 
        border-right: 1px solid #e9e9e8; 
    }}
    
    /* CONFIGURACIÓN DE TIPOGRAFÍAS DE NOTION */
    div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, h1, h3, h4, h5, span {{ 
        color: #37352f !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    
    /* TABLAS PLANAS ESTILO NOTION */
    .notion-table-header {{
        display: flex; 
        background-color: #f7f7f5; 
        font-weight: 600; 
        padding: 8px 12px; 
        border-bottom: 1px solid #e9e9e8; 
        font-size: 13px; 
        color: #6a6a65;
    }}
    
    /* BADGES DE ESTADO */
    .badge-notion {{
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        display: inline-block;
    }}
    .badge-done {{ background-color: #e2f6ea; color: #11683b; }}
    .badge-progress {{ background-color: #e2f2ff; color: #0c66e4; }}
    .badge-canceled {{ background-color: #ffebe9; color: #c9372c; }}
    .badge-empty {{ background-color: #f1f1ef; color: #5a5d56; }}

    /* BOTONES ESTILO NOTION */
    div.stButton > button, .stButton button {{
        background-color: #ffffff !important;
        color: #37352f !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 5px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        font-size: 13px !important;
        padding: 5px 12px !important;
    }}
    div.stButton > button:hover {{
        background-color: #f7f7f5 !important;
        border-color: #d0d0d0 !important;
    }}
    
    .btn-principal button {{
        background-color: #2383e2 !important;
        color: white !important;
        border: 1px solid #2383e2 !important;
    }}
    .btn-principal button:hover {{
        background-color: #1a66b8 !important;
    }}
    
    /* CABECERA GENERAL */
    .constante-header-container {{
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
        border-bottom: 1px solid #e9e9e8;
        padding-bottom: 10px;
    }}
    .constante-header-container h1 {{ margin: 0 !important; color: #37352f !important; font-size: 22px; font-weight: 600; }}
    
    /* INTERCEPTOR DE CLIC AFUERA (CAPA TRANSPARENTE DE FONDO) */
    .side-peek-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0,0,0,0.15);
        z-index: 99998;
    }}

    /* VENTANA DE COSTADO (SIDE PEEK) SUPERPUESTA CON SCROLL INTERNO */
    .side-peek-floating {{
        position: fixed;
        top: 0;
        right: 0;
        width: 450px; /* Ancho idéntico al solicitado */
        height: 100vh;
        background-color: #fbfbfa !important;
        box-shadow: -4px 0px 25px rgba(0,0,0,0.08);
        border-left: 1px solid #e0e0de;
        z-index: 99999;
        padding: 24px;
        overflow-y: auto; /* Permite deslizar si el formulario es muy extenso */
        box-sizing: border-box;
    }}
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
        
        # El contenido principal ahora ocupa toda la pantalla para que la ventana se superponga libremente
        col_principal = st.container()

        with col_principal:
            st.markdown("### Panel de la Agenda e Historial Clínico")
            
            # --- BOTONES INTERACTIVOS CON EFECTO ALTERNADOR (ANIMACIÓN EN REVERSA) ---
            c_btn1, c_btn2, _ = st.columns([1, 1, 2])
            with c_btn1:
                if st.button("➕ Nuevo Expediente", use_container_width=True):
                    if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                        st.session_state.side_peek_modo = None  # Cierre inverso
                    else:
                        st.session_state.side_peek_modo = "NUEVO_EXPEDIENTE"
                    st.rerun()
            with c_btn2:
                if st.button("📅 Agendar Nueva Cita", use_container_width=True):
                    if st.session_state.side_peek_modo == "NUEVA_CITA":
                        st.session_state.side_peek_modo = None  # Cierre inverso
                    else:
                        st.session_state.side_peek_modo = "NUEVA_CITA"
                    st.rerun()

            st.markdown("---")

            # --- TABLILLA DE CITAS PROGRAMADAS ESTILO NOTION ---
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
                    est = fila['estado']
                    badge_class = "badge-progress"
                    if est == "Realizada": badge_class = "badge-done"
                    elif est == "Cancelada": badge_class = "badge-canceled"
                    elif est == "No Asistió": badge_class = "badge-empty"

                    c_fila1, c_fila2, c_fila3, c_fila4 = st.columns([2, 1.5, 1, 1])
                    with c_fila1:
                        st.markdown(f"<div style='padding-top:6px; font-size:14px;'>📄 {fila['nombre']}</div>", unsafe_allow_html=True)
                    with c_fila2:
                        st.markdown(f"<div style='padding-top:6px; font-size:14px; color:#5a5d56;'>{fila['fecha_hora']}</div>", unsafe_allow_html=True)
                    with c_fila3:
                        st.markdown(f"<div style='padding-top:6px;'><span class='badge-notion {badge_class}'>{est}</span></div>", unsafe_allow_html=True)
                    with c_fila4:
                        if st.button("📄 Abrir", key=f"open_t_{fila['id']}", use_container_width=True):
                            if st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id == fila['id']:
                                st.session_state.side_peek_modo = None
                                st.session_state.cita_seleccionada_id = None
                            else:
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
                                            if st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id == cita_dia['id']:
                                                st.session_state.side_peek_modo = None
                                                st.session_state.cita_seleccionada_id = None
                                            else:
                                                st.session_state.side_peek_modo = "VER_CITA"
                                                st.session_state.cita_seleccionada_id = cita_dia['id']
                                            st.rerun()
                            else:
                                st.write("")
                    st.markdown("<hr style='margin:4px 0; border-top:1px solid #f1f1ef;'>", unsafe_allow_html=True)

            else:
                inicio_semana = fecha_pivote - timedelta(days=fecha_pivote.weekday())
                dias_laborales = [inicio_semana + timedelta(days=i) for i in range(5)]
                columnas_laborales = [d.strftime('%A (%d/%m)') for d in dias_laborales]
                
                horas_bloque = [f"{str(h).zfill(2)}:00" for h in range(8, 18)]
                matriz_semana = pd.DataFrame(index=horas_bloque, columns=columnas_laborales).fillna("")
                
                for _, c_act in citas_tabla.iterrows():
                    try:
                        dt_c = datetime.strptime(c_act['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                        if dt_c.date() in dias_laborales:
                            col_idx = dias_laborales.index(dt_c.date())
                            h_str = dt_c.strftime("%H:00")
                            if h_str in matriz_semana.index:
                                matriz_semana.at[h_str, columnas_laborales[col_idx]] = f"📄 {c_act['nombre']} ({c_act['estado']})"
                    except: pass
                
                st.caption("Horario institucional coordinado de Lunes a Viernes.")
                st.dataframe(matriz_semana, use_container_width=True)

        # =================================================================================
        # CAPA SUPERPUESTA REAL (SIDE PEEK FLOTANTE CON DESPLAZAMIENTO VERTICAL INTEGRADO)
        # =================================================================================
        if st.session_state.side_peek_modo:
            # Botón invisible/transparente de fondo que actúa como "clic afuera" para minimizar
            st.markdown('<div class="side-peek-overlay"></div>', unsafe_allow_html=True)
            
            # Contenedor flotante que rompe el flujo y se superpone a todo a la derecha
            st.markdown('<div class="side-peek-floating">', unsafe_allow_html=True)
            
            # Fila superior de controles de la ventana
            c_cierre1, c_cierre2 = st.columns([2.5, 1.5])
            with c_cierre1:
                st.caption("Página de Costado Flotante")
            with c_cierre2:
                if st.button("➡️ Cerrar", key="btn_cerrar_side_peek", use_container_width=True):
                    st.session_state.side_peek_modo = None
                    st.session_state.cita_seleccionada_id = None
                    st.rerun()
            st.markdown("---")

            # --- MODO A: CREAR NUEVO EXPEDIENTE CLINICO ---
            if st.session_state.side_peek_modo == "NUEVO_EXPEDIENTE":
                st.markdown("### 📄 Abrir Nuevo Expediente Clínico")
                st.caption("Rellene los datos. Deslice hacia abajo si requiere ver más campos.")
                
                exp_nom = st.text_input("Nombre Completo del Alumno:", key="f_exp_nom")
                exp_mat = st.text_input("Matrícula Institucional Única:", key="f_exp_mat")
                
                exp_edad = st.number_input("Edad:", min_value=15, max_value=60, value=20, key="f_exp_edad")
                exp_gen = st.selectbox("Género Biológico:", ["Masculino", "Femenino", "No Especificado"], key="f_exp_gen")
                
                exp_div = st.selectbox("División Académica:", list(ESTRUCTURA_UJAT.keys()), key="f_exp_div")
                exp_car = st.selectbox("Carrera Universitaria:", ESTRUCTURA_UJAT[exp_div], key="f_exp_car")
                
                exp_sem = st.selectbox("Semestre Activo:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="f_exp_sem")
                exp_tel = st.text_input("Teléfono Móvil:", key="f_exp_tel")
                exp_cor = st.text_input("Correo Institucional:", key="f_exp_cor")
                exp_tag = st.text_input("Diagnóstico (Etiquetas por comas):", key="f_exp_tag")
                
                # Nombre de columna correcto de acuerdo al mapeo clínico
                exp_obs = st.text_area("Motivo de Consulta:", height=140, key="f_exp_obs")
                
                st.markdown('<div class="btn-principal">', unsafe_allow_html=True)
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
                            st.success("Expediente guardado con éxito.")
                            st.session_state.side_peek_modo = None
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("La matrícula ya existe.")
                        finally: conn.close()
                    else: st.warning("Nombre y Matrícula son requeridos.")
                st.markdown('</div>', unsafe_allow_html=True)

            # --- MODO B: AGENDAR NUEVA CITA ---
            elif st.session_state.side_peek_modo == "NUEVA_CITA":
                st.markdown("### 📅 Programar Consulta")
                
                b_mat_c = st.text_input("Buscar Matrícula del Alumno:", key="f_cita_bus_mat")
                if b_mat_c.strip():
                    conn = conectar_db_local()
                    res_paciente = conn.cursor().execute("SELECT id, nombre, carrera FROM expedientes WHERE matricula = ?", (b_mat_c.strip(),)).fetchone()
                    conn.close()
                    
                    if res_paciente:
                        st.info(f"Paciente: {res_paciente[1]}")
                        c_fecha = st.date_input("Fecha Programada:", key="f_cita_date")
                        c_hora = st.time_input("Hora Programada:", key="f_cita_time")
                        c_motivo = st.text_area("Motivo Clínico de Consulta:", height=120, key="f_cita_motivo")
                        
                        st.markdown('<div class="btn-principal">', unsafe_allow_html=True)
                        if st.button("Confirmar y Agendar Cita", use_container_width=True, key="btn_guardar_cita_final"):
                            f_iso = datetime.combine(c_fecha, c_hora).strftime("%Y-%m-%d %H:%M:%S")
                            conn = conectar_db_local()
                            conn.cursor().execute("""
                                INSERT INTO citas (expediente_id, fecha_hora, estado, motivo, notas_evolucion)
                                VALUES (?, ?, 'Pendiente', ?, '')
                            """, (res_paciente[0], f_iso, c_motivo))
                            conn.commit()
                            conn.close()
                            st.success("Cita agendada.")
                            st.session_state.side_peek_modo = None
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error("Matrícula no encontrada.")

            # --- MODO C: VER / EDITAR CITA EXISTENTE ---
            elif st.session_state.side_peek_modo == "VER_CITA" and st.session_state.cita_seleccionada_id:
                conn = conectar_db_local()
                datos_cita = conn.cursor().execute("""
                    SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id, e.matricula
                    FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                """, (st.session_state.cita_seleccionada_id,)).fetchone()
                conn.close()

                if datos_cita:
                    st.markdown(f"## {datos_cita[1]}")
                    st.caption(f"Matrícula: {datos_cita[8]}")
                    st.markdown("---")
                    
                    peek_estado = st.selectbox("Estado de Consulta:", ["Pendiente", "Realizada", "Cancelada", "No Asistió"], index=["Pendiente", "Realizada", "Cancelada", "No Asistió"].index(datos_cita[3]), key="f_ver_estado")
                    peek_fecha = st.text_input("Fecha y Hora Asignada:", value=datos_cita[2], disabled=True, key="f_ver_fecha")
                    peek_motivo = st.text_area("Motivo de la Ficha:", value=datos_cita[4], disabled=True, key="f_ver_motivo")
                    peek_notas = st.text_area("Notas Clínicas y Evolución:", value=datos_cita[5], height=150, key="f_ver_notas")
                    peek_tags = st.text_input("Modificar Etiquetas:", value=datos_cita[6], key="f_ver_tags")

                    st.markdown('<div class="btn-principal">', unsafe_allow_html=True)
                    if st.button("Guardar Cambios Clínicos", use_container_width=True, key="btn_actualizar_cita_final"):
                        conn = conectar_db_local()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (peek_estado, peek_notas, datos_cita[0]))
                        cursor.execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (peek_tags.strip().lower(), datos_cita[7]))
                        conn.commit()
                        conn.close()
                        st.success("Sincronizado.")
                        st.session_state.side_peek_modo = None
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Cierre del Div flotante
            st.markdown('</div>', unsafe_allow_html=True)

    # =================================================================================
    # RESTO DE MÓDULOS DE GESTIÓN (MANTIENEN LA ESTRUCTURA)
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h3>Repositorio General de Expedientes Clínicos</h3>")
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
        st.markdown("<h3>Control de Citas Clínicas e Historial de Sesiones</h3>")
        st.info("Utilice el panel principal '🏠 Inicio y Planner' para desplegar de forma superpuesta la ventana lateral sin obstrucciones.")

    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("<h3>Panel de Métricas y Estadísticas Multidimensionales</h3>")
        conn = conectar_db_local()
        df_completo = pd.read_sql_query("SELECT * FROM expedientes", conn)
        conn.close()
        
        if not df_completo.empty:
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1: st.metric("Expedientes Abiertos", len(df_completo))
            with c_m2: st.metric("Divisiones Atendidas", len(df_completo['division'].unique()))
            with c_m3: st.metric("Licenciaturas Cubiertas", len(df_completo['carrera'].unique()))