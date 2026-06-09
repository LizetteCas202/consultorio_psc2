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
if "sub_pantalla_auth" not in st.session_state: st.session_state.sub_pantalla_auth = "login"
if "cita_seleccionada_id" not in st.session_state: st.session_state.cita_seleccionada_id = None

campos_formulario = ["form_mat", "form_nom", "form_tel", "form_cor", "form_tags", "form_obs", "form_edad"]
for campo in campos_formulario:
    if campo not in st.session_state: st.session_state[campo] = ""

if "form_gen" not in st.session_state: st.session_state.form_gen = "Masculino"
if "form_div" not in st.session_state: st.session_state.form_div = "DACYTI"
if "form_car" not in st.session_state: st.session_state.form_car = "Licenciatura en Tecnologías de la Información"
if "form_sem" not in st.session_state: st.session_state.form_sem = "1ro"

def limpiar_formulario_expediente():
    for campo in campos_formulario: st.session_state[campo] = ""
    st.session_state.form_gen = "Masculino"
    st.session_state.form_div = "DACYTI"
    st.session_state.form_sem = "1ro"

ESTRUCTURA_UJAT = {
    "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
    "DAIA": ["Ingeniería Mecánica Eléctrica", "Ingeniería Civil", "Ingeniería Química", "Ingeniería Ambiental"],
    "DACB": ["Licenciatura en Ciencias Computacionales", "Licenciatura en Matemáticas", "Licenciatura en Física"]
}

# -------------------------------------------------------------------------------------
# ESTILOS GLOBALES - LENGUAJE CORPORAL E INTERFAZ INSPIRADA EN NOTION (image_528383.png)
# -------------------------------------------------------------------------------------
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    
    /* BARRA LATERAL NAVEGACIÓN */
    [data-testid="stSidebar"] {{ 
        background-color: #f4f5f6 !important; 
        border-right: 1px solid #e0e0e0; 
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {{
        color: #37352f !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* ENTORNO VISUAL NOTION STYLE */
    div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, h3, h4, h5, span {{ 
        color: #37352f !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* TABLAS ESTILO NOTION (FILAS PLANAS CON BORDE) */
    .notion-table-row {{
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-bottom: 1px solid #e9e9e8;
        transition: background 0.2s ease;
        font-size: 14px;
        color: #37352f;
    }}
    .notion-table-row:hover {{
        background-color: #f7f7f5;
    }}
    
    /* BADGES DE ESTADO - INSPIRADOS EN NOTION */
    .badge-notion {{
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        display: inline-block;
    }}
    .badge-done {{ background-color: #e2f6ea; color: #11683b; }} /* Realizada */
    .badge-progress {{ background-color: #e2f2ff; color: #0c66e4; }} /* Pendiente */
    .badge-canceled {{ background-color: #ffebe9; color: #c9372c; }} /* Cancelada */
    .badge-empty {{ background-color: #f1f1ef; color: #5a5d56; }} /* No Asistió */

    /* BOTONES */
    div.stButton > button, .stButton button {{
        background-color: #ffffff !important;
        color: #37352f !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 5px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        font-size: 13px !important;
    }}
    div.stButton > button:hover {{
        background-color: #f7f7f5 !important;
        border-color: #d0d0d0 !important;
    }}
    
    /* CABECERA */
    .constante-header-container {{
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
        border-bottom: 1px solid #e9e9e8;
        padding-bottom: 10px;
    }}
    .constante-header-container h1 {{ margin: 0 !important; color: #37352f !important; font-size: 22px; font-weight: 600; }}
    
    /* CONTENEDOR SIDE PEEK (PANEL LATERAL) */
    .side-peek-container {{
        background-color: #fbfbfa;
        border-left: 1px solid #e9e9e8;
        padding: 20px;
        height: 100%;
        border-radius: 4px;
    }}
    </style>
""", unsafe_allow_html=True)

if not st.session_state.autenticado:
    # --- PANTALLA DE ACCESO DE SEGURIDAD ---
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
    # Encabezado Único del Sistema
    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="35">
            <h1>Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Menú Lateral
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["🏠 Inicio y Planner", "📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Profesional:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.cita_seleccionada_id = None
        st.rerun()

    # =================================================================================
    # MÓDULO 0: INICIO Y PLANNER DINÁMICO (SOPORTE SIDE PEEK ESTILO NOTION)
    # =================================================================================
    if seccion == "🏠 Inicio y Planner":
        
        # Determinar el layout base: si hay una cita seleccionada, abrimos el panel lateral (Side Peek)
        if st.session_state.cita_seleccionada_id:
            col_principal, col_side_peek = st.columns([1.8, 1.2])
        else:
            col_principal = st.container()
            col_side_peek = None

        with col_principal:
            st.markdown("### Panel del Agenda e Historial Clínico")
            
            # --- ACCIONES RÁPIDAS INSTITUCIONALES ---
            c_acc1, c_acc2 = st.columns(2)
            with c_acc1:
                with st.popover("➕ Registrar Nuevo Expediente"):
                    quick_nom = st.text_input("Nombre Completo:")
                    quick_mat = st.text_input("Matrícula:")
                    quick_div = st.selectbox("División Académica:", list(ESTRUCTURA_UJAT.keys()))
                    quick_car = st.selectbox("Carrera Universitaria:", ESTRUCTURA_UJAT[quick_div])
                    quick_obs = st.text_area("Motivo de Consulta:")
                    if st.button("Crear Expediente"):
                        if quick_mat.strip() and quick_nom.strip():
                            conn = conectar_db_local()
                            try:
                                conn.cursor().execute("""
                                    INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                    VALUES (?, ?, 'No Especificado', 20, ?, ?, '1ro', '', '', ?, '')
                                """, (quick_mat.strip(), quick_nom.strip(), quick_div, quick_car, quick_obs))
                                conn.commit()
                                st.success("Expediente creado.")
                                st.rerun()
                            except: st.error("La matrícula ya existe.")
                            finally: conn.close()

            with c_acc2:
                with st.popover("📅 Registrar Nueva Cita"):
                    quick_c_mat = st.text_input("Matrícula del Alumno:")
                    if quick_c_mat.strip():
                        conn = conectar_db_local()
                        res_al = conn.cursor().execute("SELECT id, nombre FROM expedientes WHERE matricula = ?", (quick_c_mat.strip(),)).fetchone()
                        conn.close()
                        if res_al:
                            st.caption(f"Paciente: {res_al[1]}")
                            q_f = st.date_input("Fecha:")
                            q_h = st.time_input("Hora:")
                            q_m = st.text_area("Motivo Clínico:")
                            if st.button("Agendar Sesión"):
                                f_iso = datetime.combine(q_f, q_h).strftime("%Y-%m-%d %H:%M:%S")
                                conn = conectar_db_local()
                                conn.cursor().execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)", (res_al[0], f_iso, q_m))
                                conn.commit()
                                conn.close()
                                st.success("Cita agendada.")
                                st.rerun()

            st.markdown("---")

            # --- TABLILLA DE CITAS PENDIENTES ESTILO NOTION (image_528383.png) ---
            st.markdown("#### 📄 Citas Programadas")
            fecha_hoy_str = date.today().strftime("%Y-%m-%d")
            
            conn = conectar_db_local()
            citas_tabla = pd.read_sql_query("""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora ASC
            """, conn)
            conn.close()

            if not citas_tabla.empty:
                # Fila de Encabezados de la Tabla
                st.markdown("""
                    <div style="display: flex; background-color: #f7f7f5; font-weight: 600; padding: 6px 12px; border-bottom: 1px solid #e9e9e8; font-size: 13px; color: #6a6a65;">
                        <div style="flex: 2;">Aa Nombre de Paciente</div>
                        <div style="flex: 1.5;">📅 Fecha y Hora</div>
                        <div style="flex: 1;">✨ Estado</div>
                        <div style="flex: 1;">⚙️ Acción</div>
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
                        st.markdown(f"<div style='padding-top:5px; font-size:14px;'>📄 {fila['nombre']}</div>", unsafe_allow_html=True)
                    with c_fila2:
                        st.markdown(f"<div style='padding-top:5px; font-size:14px; color:#5a5d56;'>{fila['fecha_hora']}</div>", unsafe_allow_html=True)
                    with c_fila3:
                        st.markdown(f"<div style='padding-top:5px;'><span class='badge-notion {badge_class}'>{est}</span></div>", unsafe_allow_html=True)
                    with c_fila4:
                        if st.button("📄 Abrir", key=f"btn_open_table_{fila['id']}"):
                            st.session_state.cita_seleccionada_id = fila['id']
                            st.rerun()
            else:
                st.info("No hay registros de consultas en la base de datos.")

            st.markdown("---")

            # --- PLANNER CLÍNICO (OPCIONES SEMANAL L-V / MENSUAL CUADRÍCULA) ---
            st.markdown("#### 📅 Visualizador de Calendario Clínico")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                tipo_formato = st.selectbox("Formato Ajustado:", ["Mensual (Cuadrícula General)", "Semanal (Horario Laboral L-V)"])
            with c_p2:
                fecha_pivote = st.date_input("Fecha Base Enfoque:", value=date.today())

            # --- OPCIÓN 1: VISTA MENSUAL EN CUADRÍCULA CON ACCESO DIRECTO ---
            if tipo_formato == "Mensual (Cuadrícula General)":
                año_sel, mes_sel = fecha_pivote.year, fecha_pivote.month
                cal_objeto = calendar.Calendar(firstweekday=0)
                semanas_mes = cal_objeto.monthdatescalendar(año_sel, mes_sel)

                # Mapear las citas del mes
                diccionario_citas_mes = {}
                for _, c_act in citas_tabla.iterrows():
                    try:
                        dt_c = datetime.strptime(c_act['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                        f_str = dt_c.strftime("%Y-%m-%d")
                        if f_str not in diccionario_citas_mes:
                            diccionario_citas_mes[f_str] = []
                        diccionario_citas_mes[f_str].append(c_act)
                    except: pass

                # Dibujar la cuadrícula mensual estructurada en renglones
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
                                        # Botón compacto para abrir la edición directamente en el Side Peek
                                        if st.button(f"⏱️ {hora_c}\n{cita_dia['nombre'][:12]}...", key=f"cal_m_{cita_dia['id']}"):
                                            st.session_state.cita_seleccionada_id = cita_dia['id']
                                            st.rerun()
                            else:
                                st.write("")
                    st.markdown("<hr style='margin:4px 0; border-top:1px solid #f1f1ef;'>", unsafe_allow_html=True)

            # --- OPCIÓN 2: VISTA SEMANAL LABORAL (ESTRICTAMENTE LUNES A VIERNES) ---
            else:
                inicio_semana = fecha_pivote - timedelta(days=fecha_pivote.weekday())
                # Solo procesamos 5 días correspondientes a la jornada de la universidad
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
        # DINÁMICA DE PANEL LATERAL "SIDE PEEK" ESTILO NOTION (image_527fff.png)
        # =================================================================================
        if col_side_peek and st.session_state.cita_seleccionada_id:
            with col_side_peek:
                st.markdown('<div class="side-peek-container">', unsafe_allow_html=True)
                
                # Botón de cierre superior del panel lateral
                if st.button("➡️ Cerrar Vista Lateral"):
                    st.session_state.cita_seleccionada_id = None
                    st.rerun()
                
                conn = conectar_db_local()
                datos_cita = conn.cursor().execute("""
                    SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id, e.matricula
                    FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                """, (st.session_state.cita_seleccionada_id,)).fetchone()
                conn.close()

                if datos_cita:
                    st.markdown(f"## {datos_cita[1]}")
                    st.caption(f"Matrícula Universitaria: {datos_cita[8]}")
                    st.markdown("---")
                    
                    st.markdown("##### ⚙️ Propiedades de la Consulta")
                    peek_estado = st.selectbox("Estado Clínico:", ["Pendiente", "Realizada", "Cancelada", "No Asistió"], index=["Pendiente", "Realizada", "Cancelada", "No Asistió"].index(datos_cita[3]), key="peek_est")
                    peek_fecha = st.text_input("Fecha programada original:", value=datos_cita[2], disabled=True)
                    peek_motivo = st.text_area("Motivo Registrado de Consulta:", value=datos_cita[4], disabled=True)
                    
                    st.markdown("---")
                    st.markdown("##### 📝 Notas Clínicas de Evolución")
                    peek_notas = st.text_area("Evolución del Paciente:", value=datos_cita[5], height=180, key="peek_note")
                    peek_tags = st.text_input("Etiquetas / Diagnóstico Clínico:", value=datos_cita[6], key="peek_tag")

                    if st.button("💾 Guardar y Actualizar Ficha"):
                        conn = conectar_db_local()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (peek_estado, peek_notas, datos_cita[0]))
                        cursor.execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (peek_tags.strip().lower(), datos_cita[7]))
                        conn.commit()
                        conn.close()
                        st.success("Cambios sincronizados en el expediente.")
                        st.session_state.cita_seleccionada_id = None
                        st.rerun()
                        
                st.markdown('</div>', unsafe_allow_html=True)

    # =================================================================================
    # RESTO DE MÓDULOS DE GESTIÓN (MANTENIDOS SIN CAMBIOS DE LÓGICA)
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("### Repositorio General de Expedientes Clínicos")
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
        st.markdown("### Control de Citas Clínicas e Historial de Sesiones")
        st.info("Utilice el panel principal '🏠 Inicio y Planner' para una gestión fluida e interactiva en formato Notion Side Peek.")

    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("### Panel de Métricas y Estadísticas Multidimensionales")
        conn = conectar_db_local()
        df_completo = pd.read_sql_query("SELECT * FROM expedientes", conn)
        conn.close()
        
        if not df_completo.empty:
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1: st.metric("Expedientes Abiertos", len(df_completo))
            with c_m2: st.metric("Divisiones Atendidas", len(df_completo['division'].unique()))
            with c_m3: st.metric("Licenciaturas Cubiertas", len(df_completo['carrera'].unique()))
            
            st.markdown("---")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("#### 🏷️ Prevalencia de Diagnósticos (Etiquetas)")
                lista_tags = []
                for t in df_completo['etiquetas'].dropna():
                    lista_tags.extend([x.strip() for x in t.split(",") if x.strip()])
                if lista_tags: st.bar_chart(pd.Series(lista_tags).value_counts())
            with col_g2:
                st.markdown("#### 🧬 Distribución por Género")
                st.bar_chart(df_completo['genero'].value_counts())