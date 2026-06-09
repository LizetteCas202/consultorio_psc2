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
        st.error(f"Error al conectar a la base de datos local: {e}")
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
# FLUJO 1: PANTALLA DE LOGIN TOTALMENTE CENTRADA Y CORREGIDA EN VISIBILIDAD
# -------------------------------------------------------------------------------------
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        .stApp { background-color: #ffffff !important; }
        .block-container { max-width: 450px !important; padding-top: 5rem !important; margin: 0 auto !important; }
        
        .login-box {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.08);
            text-align: center;
        }
        
        div[data-testid="stWidgetLabel"] p, label, span { 
            color: #081849 !important; 
            font-weight: 700 !important; 
        }
        input { background-color: #f1f2f6 !important; color: #081849 !important; border-radius: 6px !important; }
        
        div[data-baseweb="input"] { background-color: #f1f2f6 !important; border: 1px solid #CCCACC !important; }
        div[data-baseweb="input"] button { background-color: transparent !important; }
        div[data-baseweb="input"] svg { fill: #081849 !important; color: #081849 !important; }
        
        h1 { color: #213885 !important; font-weight: 700; font-size: 24px !important; margin-bottom: 5px !important; }
        
        button, div.stButton > button {
            background-color: #213885 !important;
            border: 1px solid #213885 !important;
            border-radius: 6px !important;
            height: 45px !important;
            width: 100% !important;
        }
        button p, div.stButton > button p, span[data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 15px !important;
        }
        button:hover, div.stButton > button:hover { background-color: #081849 !important; border-color: #081849 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.image(LOGO_UJAT_URL, width=120)
    
    if st.session_state.sub_pantalla_auth == "login":
        st.markdown("<h1>Consultorio Psicológico DACYTI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#081849; font-size:13px; margin-bottom: 20px;'>Control de Acceso Clínico Universitario</p>", unsafe_allow_html=True)
        
        u_login = st.text_input("Usuario Corporativo:", key="u_login_key")
        p_login = st.text_input("Contraseña:", type="password", key="p_login_key")
        
        if st.button("Ingresar al Portal"):
            conn = conectar_db_local()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND clave_hash=?", (u_login, p_login))
            if cursor.fetchone():
                st.session_state.autenticado = True
                st.session_state.usuario_actual = u_login
                st.rerun()
            else:
                st.error("Credenciales corporativas inválidas.")
            conn.close()
            
        st.write("<hr style='border-top: 1px solid #CCCACC; margin: 15px 0;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 Registrarse"): st.session_state.sub_pantalla_auth = "registro"; st.rerun()
        with c2:
            if st.button("🔑 Recuperar"): st.session_state.sub_pantalla_auth = "recuperar"; st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------------------------------
# FLUJO 2: INTERFAZ INTERNA DE ADMINISTRACIÓN COMPLETA
# -------------------------------------------------------------------------------------
else:
    # INYECCIÓN DE CSS EXTREMO: Reparación total de visibilidad en la barra lateral
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #ffffff !important; }}
        
        /* FIX CRÍTICO BARRA LATERAL: Forzar letras a azul marino oscuro */
        [data-testid="stSidebar"] {{ 
            background-color: #f4f5f6 !important; 
            border-right: 2px solid #CCCACC; 
        }}
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {{
            color: #081849 !important;
            font-weight: 700 !important;
        }}
        /* Modificar el color de los Radio Buttons seleccionados en la barra lateral */
        [data-testid="stSidebar"] div[data-checked="true"] > div {{
            background-color: #213885 !important;
        }}
        
        /* Textos Legibles en el Contenido Principal */
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, h3, h4, span {{ 
            color: #081849 !important; 
            font-weight: 600 !important; 
        }}
        
        div[data-testid="stAlert"], .stAlert, div[data-testid="stCallout"] {{
            background-color: #CCCACC !important;
            color: #081849 !important;
            border-left: 6px solid #213885 !important;
            border-radius: 8px;
        }}
        
        div.stButton > button, .stButton button, [data-testid="stForm"] button {{
            background-color: #213885 !important;
            color: #ffffff !important;
            border: 1px solid #213885 !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
        }}
        div.stButton > button p, .stButton button p {{ color: #ffffff !important; }}
        div.stButton > button:hover {{ background-color: #081849 !important; }}
        
        .constante-header-container {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            border-bottom: 3px solid #CCCACC;
            padding-bottom: 10px;
        }}
        .constante-header-container h1 {{ margin: 0 !important; color: #213885 !important; font-weight: 700; font-size: 24px; }}
        
        /* Clases de Semáforo */
        .status-realizada {{ background-color: #d4edda !important; color: #155724 !important; padding: 10px; border-radius: 6px; border-left: 5px solid #28a745; margin-bottom: 8px; }}
        .status-cancelada {{ background-color: #f8d7da !important; color: #721c24 !important; padding: 10px; border-radius: 6px; border-left: 5px solid #dc3545; margin-bottom: 8px; }}
        .status-noasistio {{ background-color: #e2e3e5 !important; color: #383d41 !important; padding: 10px; border-radius: 6px; border-left: 5px solid #6c757d; margin-bottom: 8px; }}
        .status-pendiente {{ background-color: #cce5ff !important; color: #004085 !important; padding: 10px; border-radius: 6px; border-left: 5px solid #007bff; margin-bottom: 8px; }}
        </style>
    """, unsafe_allow_html=True)

    # Encabezado Fijo Institucional
    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="40">
            <h1>Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Barra lateral de Navegación con Visibilidad Corregida al 100%
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["🏠 Inicio y Planner", "📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Encargada:** {st.session_state.usuario_actual}")
    if st.sidebar.button("🔒 Cerrar Sesión Portal"):
        st.session_state.autenticado = False
        st.rerun()

    # =================================================================================
    # MÓDULO 0: INICIO Y PLANNER DINÁMICO TIPO GOOGLE CALENDAR (SIN LÍMITE DE TIEMPO)
    # =================================================================================
    if seccion == "🏠 Inicio y Planner":
        st.markdown("<h3>Panel de Inicio - Agenda del Día</h3>", unsafe_allow_html=True)
        
        col_izq_p, col_der_p = st.columns([1.1, 1.9])
        
        with col_izq_p:
            st.markdown("#### ⏰ Atenciones de Hoy")
            fecha_hoy_str = date.today().strftime("%Y-%m-%d")
            
            conn = conectar_db_local()
            citas_hoy = pd.read_sql_query(f"""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                WHERE c.fecha_hora LIKE '{fecha_hoy_str}%'
            """, conn)
            conn.close()
            
            if not citas_hoy.empty:
                for idx, fila in citas_hoy.iterrows():
                    est = fila['estado']
                    clase_css = "status-pendiente"
                    if est == "Realizada": clase_css = "status-realizada"
                    elif est == "Cancelada": clase_css = "status-cancelada"
                    elif est == "No Asistió": clase_css = "status-noasistio"
                    
                    st.markdown(f"""
                        <div class="{clase_css}">
                            <strong>{fila['fecha_hora'][11:16]} hrs</strong> - {fila['nombre']}<br>
                            <small>Motivo: {fila['motivo']} | Estado: {est}</small>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No tienes citas registradas para hoy, comadre.")
                
        with col_der_p:
            st.markdown("#### 📅 Planner Interactivo Estilo Google Calendar")
            
            # Controles dinámicos sin límite de tiempo (Cualquier Año o Mes)
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                tipo_formato = st.radio("Formato de Visualización:", ["Semanal (Bloque de Horas)", "Mensual (Carga General)"], horizontal=True)
            with c_p2:
                fecha_pivote = st.date_input("Selecciona Fecha de Enfoque:", value=date.today())

            # Extraer todas las citas de la BD para mapearlas en el calendario
            conn = conectar_db_local()
            df_todas_citas = pd.read_sql_query("""
                SELECT c.fecha_hora, e.nombre, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
            """, conn)
            conn.close()

            # --- FORMATO 1: VISTA SEMANAL (DÍAS VS HORAS) ---
            if tipo_formato == "Semanal (Bloque de Horas)":
                # Calcular los días de la semana de la fecha seleccionada
                inicio_semana = fecha_pivote - timedelta(days=fecha_pivote.weekday())
                dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]
                nombres_columnas = [d.strftime('%A (%d/%m)') for d in dias_semana]
                
                # Definir bloques de horas de oficina (8 AM a 6 PM)
                horas_bloque = [f"{str(h).zfill(2)}:00" for h in range(8, 19)]
                
                # Crear la matriz vacía estructurada como el calendario de Google
                matriz_semana = pd.DataFrame(index=horas_bloque, columns=nombres_columnas).fillna("")
                
                # Llenar la matriz con citas reales si existen
                if not df_todas_citas.empty:
                    for _, cita in df_todas_citas.iterrows():
                        try:
                            dt_cita = datetime.strptime(cita['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                            fecha_cita_date = dt_cita.date()
                            
                            if fecha_cita_date in dias_semana:
                                col_idx = dias_semana.index(fecha_cita_date)
                                hora_str = dt_cita.strftime("%H:00")
                                if hora_str in matriz_semana.index:
                                    matriz_semana.at[hora_str, nombres_columnas[col_idx]] = f"👤 {cita['nombre']} ({cita['estado']})"
                        except: pass
                
                st.caption(f"📅 Visualizando la semana del {inicio_semana.strftime('%d/%m/%Y')} al {(inicio_semana+timedelta(days=6)).strftime('%d/%m/%Y')}")
                st.dataframe(matriz_semana, use_container_width=True)

            # --- FORMATO 2: VISTA MENSUAL (SIN LÍMITE DE TIEMPO) ---
            else:
                año_sel = fecha_pivote.year
                mes_sel = fecha_pivote.month
                
                num_dias = calendar.monthrange(año_sel, mes_sel)[1]
                dias_mes = [date(año_sel, mes_sel, dia) for dia in range(1, num_dias + 1)]
                
                matriz_mes = pd.DataFrame(index=[f"Día {d}" for d in range(1, num_dias + 1)], columns=["Citas Programadas en el Día"]).fillna("Sin citas")
                
                if not df_todas_citas.empty:
                    for _, cita in df_todas_citas.iterrows():
                        try:
                            dt_cita = datetime.strptime(cita['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                            if dt_cita.year == año_sel and dt_cita.month == mes_sel:
                                idx_dia = f"Día {dt_cita.day}"
                                texto_previo = matriz_mes.at[idx_dia, "Citas Programadas en el Día"]
                                txt_cita = f"• {dt_cita.strftime('%H:%M')} - {cita['nombre']} ({cita['estado']})"
                                if texto_previo == "Sin citas":
                                    matriz_mes.at[idx_dia, "Citas Programadas en el Día"] = txt_cita
                                else:
                                    matriz_mes.at[idx_dia, "Citas Programadas en el Día"] = texto_previo + " | " + txt_cita
                        except: pass
                        
                st.caption(f"🗓️ Resumen Mensual de Atenciones: {calendar.month_name[mes_sel]} {año_sel}")
                st.dataframe(matriz_mes, use_container_width=True)

    # =================================================================================
    # MÓDULO 1: EXPEDIENTES CLÍNICOS ELECTRÓNICOS
    # =================================================================================
    elif seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h3>Repositorio General de Expedientes</h3>", unsafe_allow_html=True)
        
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
        
        with st.expander("➕ Apertura de Nuevo Expediente Psicológico"):
            nom = st.text_input("Nombre Completo del Alumno:", key="form_nom")
            c_e1, c_e2, c_e3 = st.columns(3)
            with c_e1: mat = st.text_input("Matrícula Institucional (Única):", key="form_mat")
            with c_e2: edad = st.number_input("Edad del Alumno:", min_value=15, max_value=60, value=20, key="form_edad")
            with c_e3: div_sel = st.selectbox("División Académica:", list(ESTRUCTURA_UJAT.keys()), key="form_div")
            
            c_e4, c_e5 = st.columns(2)
            with c_e4: gen = st.selectbox("Género Biológico:", ["Masculino", "Femenino", "No Especificado"], key="form_gen")
            with c_e5: car = st.selectbox("Carrera Universitaria:", ESTRUCTURA_UJAT[div_sel], key="form_car")
            
            c_e6, c_e7 = st.columns(2)
            with c_e6: sem = st.selectbox("Semestre Vigente:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="form_sem")
            with c_e7: tel = st.text_input("Teléfono:", key="form_tel")
            cor = st.text_input("Correo Institucional (@alumno.ujat.mx):", key="form_cor")
            
            st.markdown("---")
            tags = st.text_input("Diagnóstico Inicial / Etiquetas (Separados por comas):", key="form_tags")
            obs = st.text_area("Notas Iniciales del Expediente Clínico:", key="form_obs")
            
            if st.button("Registrar y Almacenar Expediente"):
                if mat.strip() and nom.strip():
                    conn = conectar_db_local()
                    cursor = conn.cursor()
                    try:
                        tags_p = ",".join([t.strip().lower() for t in tags.split(",") if t.strip()])
                        cursor.execute("""
                            INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (mat.strip(), nom.strip(), gen, int(edad), div_sel, car, sem, tel, cor, obs, tags_p))
                        conn.commit()
                        st.success("¡Expediente creado correctamente, comadre!")
                        limpiar_formulario_expediente()
                        st.rerun()
                    except sqlite3.IntegrityError: st.error("Error crítico: Esa matrícula ya existe.")
                    finally: conn.close()

    # =================================================================================
    # MÓDULO 2: AGENDA DE CITAS Y VENTANA DE EVOLUCIÓN
    # =================================================================================
    elif seccion == "📅 Agenda de Citas":
        st.markdown("<h3>Control de Citas Clínicas e Historial de Sesiones</h3>", unsafe_allow_html=True)
        
        col_ag1, col_ag2 = st.columns([1.6, 1.4])
        
        with col_ag1:
            st.markdown("#### Listado y Control de Sesiones")
            conn = conectar_db_local()
            df_lista_citas = pd.read_sql_query("""
                SELECT c.id as 'ID_Cita', e.matricula as 'Matricula', e.nombre as 'Paciente', 
                       c.fecha_hora as 'Fecha_Hora', c.estado as 'Estado', c.motivo as 'Motivo'
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora DESC
            """, conn)
            conn.close()
            
            if not df_lista_citas.empty:
                st.dataframe(df_lista_citas, use_container_width=True)
                
                st.markdown("---")
                st.markdown("#### 🩺 Ventana de Evaluación / Notas de Evolución")
                id_cita_sel = st.number_input("Digita el ID de la Cita que deseas atender:", min_value=1, step=1)
                
                if id_cita_sel:
                    conn = conectar_db_local()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, c.notas_evolucion, e.etiquetas, e.id
                        FROM citas c JOIN expedientes e ON c.expediente_id = e.id WHERE c.id = ?
                    """, (id_cita_sel,))
                    datos_c = cursor.fetchone()
                    conn.close()
                    
                    if datos_c:
                        st.markdown(f"**Paciente:** {datos_c[1]} | **Cita:** {datos_c[2]}")
                        nuevo_estado = st.selectbox("Cambiar Estado (Semáforo):", ["Pendiente", "Realizada", "Cancelada", "No Asistió"], index=["Pendiente", "Realizada", "Cancelada", "No Asistió"].index(datos_c[3]))
                        nuevas_notas = st.text_area("Notas Clínicas de Evaluación y Evolución del Caso:", value=datos_c[5])
                        nuevo_diag = st.text_input("Modificar/Agregar Diagnóstico (Etiquetas):", value=datos_c[6])
                        
                        if st.button("Guardar Cambios de la Consulta"):
                            conn = conectar_db_local()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (nuevo_estado, nuevas_notas, id_cita_sel))
                            cursor.execute("UPDATE expedientes SET etiquetas = ? WHERE id = ?", (nuevo_diag.strip().lower(), datos_c[7]))
                            conn.commit()
                            conn.close()
                            st.success("¡Consulta guardada con éxito!")
                            st.rerun()
            else: st.info("No se registran citas.")
            
        with col_ag2:
            st.markdown("#### 🔍 Agendar Nueva Sesión (Filtro por Matrícula)")
            mat_b = st.text_input("Paso 1: Ingresa la Matrícula del Alumno:")
            
            if mat_b.strip():
                conn = conectar_db_local()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre, division, carrera FROM expedientes WHERE matricula = ?", (mat_b.strip(),))
                res_alumno = cursor.fetchone()
                conn.close()
                
                if res_alumno:
                    st.success(f"✅ Alumno Identificado: {res_alumno[1]}")
                    f_c = st.date_input("Programar Día:", value=date.today())
                    h_c = st.time_input("Programar Hora:")
                    mot = st.text_area("Motivo de la sesión psicológica:")
                    
                    if st.button("Confirmar Agendación de Cita"):
                        f_iso = datetime.combine(f_c, h_c).strftime("%Y-%m-%d %H:%M:%S")
                        conn = conectar_db_local()
                        conn.cursor().execute("""
                            INSERT INTO citas (expediente_id, fecha_hora, estado, motivo, notas_evolucion)
                            VALUES (?, ?, 'Pendiente', ?, '')
                        """, (res_alumno[0], f_iso, mot))
                        conn.commit()
                        conn.close()
                        st.success("¡Cita agendada correctamente!")
                        st.rerun()
                else:
                    st.error("❌ Error: Este alumno no está registrado. Abre un expediente primero.")

    # =================================================================================
    # MÓDULO 3: REPORTES EJECUTIVOS Y ESTADÍSTICAS MULTIDIMENSIONALES
    # =================================================================================
    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("<h3>Panel de Métricas y Estadísticas Multidimensionales</h3>", unsafe_allow_html=True)
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
                
            col_g3, col_g4 = st.columns(2)
            with col_g3:
                st.markdown("#### 🏫 Casos por División Académica")
                st.bar_chart(df_completo['division'].value_counts())
            with col_g4:
                st.markdown("#### 🎂 Demografía por Rango de Edad (De 2 en 2 años)")
                bins = [16, 18, 20, 22, 24, 26, 28, 30, 60]
                labels = ["16-17", "18-19", "20-21", "22-23", "24-25", "26-27", "28-29", "30+"]
                df_completo['Rango_Edad'] = pd.cut(df_completo['edad'], bins=bins, labels=labels, right=False)
                st.bar_chart(df_completo['Rango_Edad'].value_counts().sort_index())