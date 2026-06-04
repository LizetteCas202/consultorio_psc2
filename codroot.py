# =================================================================
#           APLICACIÓN CORREGIDA (EDICIÓN SUEÑO - COMPACTA & SIN ERRORES)
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
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

# --- 2. MOTOR DE CONEXIÓN LOCAL INTEGRADO (SQLite) ---
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
                estado TEXT,
                motivo TEXT,
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

# --- 3. MANEJO DE ESTADOS DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = ""
if "sub_pantalla_auth" not in st.session_state: st.session_state.sub_pantalla_auth = "login"

campos_formulario = ["form_mat", "form_nom", "form_tel", "form_cor", "form_tags", "form_obs"]
for campo in campos_formulario:
    if campo not in st.session_state: st.session_state[campo] = ""

if "form_gen" not in st.session_state: st.session_state.form_gen = "Masculino"
if "form_div" not in st.session_state: st.session_state.form_div = "DACYTI"
if "form_car" not in st.session_state: st.session_state.form_car = "Licenciatura en Tecnologías de la Información"
if "form_sem" not in st.session_state: st.session_state.form_sem = "1ro"

def limpiar_formulario_expediente():
    for campo in campos_formulario:
        st.session_state[campo] = ""
    st.session_state.form_gen = "Masculino"
    st.session_state.form_div = "DACYTI"
    st.session_state.form_car = "Licenciatura en Tecnologías de la Información"
    st.session_state.form_sem = "1ro"

# Catálogo Interdivisional
ESTRUCTURA_UJAT = {
    "DACYTI": [
        "Licenciatura en Tecnologías de la Información",
        "Licenciatura en Sistemas Computacionales",
        "Licenciatura en Telemática",
        "Ingeniería en Informática Administrativa"
    ],
    "DAIA": [
        "Ingeniería Mecánica Eléctrica",
        "Ingeniería Civil",
        "Ingeniería Química",
        "Ingeniería Ambiental"
    ],
    "DACB": [
        "Licenciatura en Ciencias Computacionales",
        "Licenciatura en Matemáticas",
        "Licenciatura en Física",
        "Licenciatura en Química"
    ]
}

# -------------------------------------------------------------------------------------
# FLUJO 1: PANTALLA DE LOGIN (OPTIMIZADA, COMPACTA Y SIN RECTÁNGULOS AZULES)
# -------------------------------------------------------------------------------------
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        .stApp { background-color: #ffffff !important; }
        
        /* Reducir el scroll de la página completa */
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        
        /* Forzar visibilidad del texto general */
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, span { 
            color: #081849 !important; 
            font-weight: 600 !important; 
            margin-bottom: 2px !important;
        }
        
        /* Títulos más compactos */
        h1 { color: #213885 !important; font-weight: 700; text-align: center; font-size: 24px !important; margin-top: 5px !important; margin-bottom: 5px !important; }
        h2 { color: #213885 !important; font-weight: 700; text-align: center; font-size: 20px !important; }
        
        /* REPARACIÓN DE BOTONES: Texto Blanco obligatorio */
        button, div.stButton > button, [data-testid="stForm"] button {
            background-color: #213885 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            border: 1px solid #213885 !important;
            width: 100%;
        }
        
        /* Evitar que el texto cambie a oscuro en el hover o focus */
        button p, div.stButton > button p, .stButton div p {
            color: #ffffff !important;
        }
        
        button:hover, div.stButton > button:hover {
            background-color: #081849 !important;
            color: #ffffff !important;
        }
        
        /* ELIMINAR EL RECTÁNGULO AZÚL DEL INPUT DE CONTRASEÑA */
        div[data-disabled="false"] div[role="presentation"] {
            background-color: transparent !important;
            border: none !important;
        }
        
        /* Asegurar que el contenedor interno de la contraseña no se pinte de azul */
        div.stTextInput div[data-baseweb="input"] div {
            background-color: transparent !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col_izq, col_centro, col_der = st.columns([1.2, 1.2, 1.2])
    with col_centro:
        # Logo más pequeño para evitar scroll involuntario
        st.markdown(f'<div style="text-align:center; margin-top: 10px; margin-bottom: 5px;"><img src="{LOGO_UJAT_URL}" width="105"></div>', unsafe_allow_html=True)
        
        if st.session_state.sub_pantalla_auth == "login":
            st.markdown("<h1>Consultorio Psicológico DACYTI</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#081849; font-size:13px; margin-bottom: 15px;'>Sistema de Gestión Interdivisional - UJAT</p>", unsafe_allow_html=True)
            
            u_login = st.text_input("Usuario Corporativo:")
            p_login = st.text_input("Contraseña:", type="password")
            
            st.write("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
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
                
            st.write("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📝 Registrarse"): st.session_state.sub_pantalla_auth = "registro"; st.rerun()
            with c2:
                if st.button("🔑 Olvidé mi clave"): st.session_state.sub_pantalla_auth = "recuperar"; st.rerun()

        elif st.session_state.sub_pantalla_auth == "registro":
            st.markdown("<h2>📝 Registrar Nuevo Personal</h2>", unsafe_allow_html=True)
            reg_u = st.text_input("Nombre de Usuario:")
            reg_p = st.text_input("Contraseña:", type="password")
            reg_preg = st.selectbox("Pregunta de Seguridad:", ["¿Unidad de origen?", "¿Clave de empleado?"])
            reg_resp = st.text_input("Respuesta Secreta:")
            
            if st.button("Completar Registro"):
                if reg_u and reg_p and reg_resp:
                    conn = conectar_db_local()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios VALUES (?, ?, 'Psicologo', ?, ?)", (reg_u, reg_p, reg_preg, reg_resp))
                        conn.commit()
                        st.success("¡Registrado con éxito!")
                        st.session_state.sub_pantalla_auth = "login"
                        st.rerun()
                    except Exception:
                        st.error("El nombre de usuario ya existe.")
                    finally:
                        conn.close()
            if st.button("⬅️ Cancelar"): st.session_state.sub_pantalla_auth = "login"; st.rerun()

# -------------------------------------------------------------------------------------
# FLUJO 2: INTERFAZ DE ADMINISTRACIÓN INTERNA 
# -------------------------------------------------------------------------------------
else:
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #ffffff !important; }}
        
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, h3, h4, span, .stSelectbox p {{ 
            color: #081849 !important; 
            font-weight: 600 !important; 
        }}
        
        .stDetails summary, div[data-testid="stExpander"] summary p {{ 
            color: #213885 !important; 
            font-weight: 700 !important; 
        }}
        
        /* Contenedores con tu Gris Paleta exacto */
        div[data-testid="stAlert"], .stAlert, div[data-testid="stCallout"] {{
            background-color: #CCCACC !important;
            color: #081849 !important;
            border-left: 6px solid #213885 !important;
            border-radius: 8px;
        }}
        div[data-testid="stAlert"] p, .stAlert p {{ color: #081849 !important; }}
        
        /* Botones internos con texto blanco */
        div.stButton > button, .stButton button {{
            background-color: #213885 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }}
        div.stButton > button p, .stButton button p {{ color: #ffffff !important; }}
        
        [data-testid="stSidebar"] {{ 
            background-color: #f4f5f6 !important; 
            border-right: 2px solid #CCCACC; 
        }}
        
        .constante-header-container {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            border-bottom: 3px solid #CCCACC;
            padding-bottom: 10px;
        }}
        .constante-header-container h1 {{
            margin: 0 !important;
            color: #213885 !important;
            font-weight: 700;
            font-size: 24px;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="40">
            <h1>Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Clínico:** {st.session_state.usuario_actual}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # --- MÓDULO 1: EXPEDIENTES ---
    if seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h3>Repositorio Unificado de Expedientes</h3>", unsafe_allow_html=True)
        c_f1, c_f2 = st.columns(2)
        with c_f1: bus_nom = st.text_input("🔍 Buscar por Nombre o Matrícula:")
        with c_f2: bus_tag = st.text_input("🏷️ Filtrar por Diagnóstico/Etiqueta:")
        
        conn = conectar_db_local()
        query = "SELECT matricula, nombre, division, carrera, semestre, etiquetas, observaciones FROM expedientes WHERE 1=1"
        args = []
        if bus_nom:
            query += " AND (nombre LIKE ? OR matricula LIKE ?)"
            args.extend([f"%{bus_nom}%", f"%{bus_nom}%"])
        if bus_tag:
            query += " AND etiquetas LIKE ?"
            args.append(f"%{bus_tag.lower().strip()}%")
            
        df_exp = pd.read_sql_query(query, conn, params=args)
        conn.close()
        
        if not df_exp.empty:
            st.dataframe(df_exp, use_container_width=True)
        else:
            st.info("No se registran expedientes que coincidan con los filtros aplicados.")

        with st.expander("➕ Crear Nuevo Expediente Clínico (Multidivisional)"):
            nom = st.text_input("Nombre Completo:", key="form_nom")
            c_e1, c_e2 = st.columns(2)
            with c_e1: mat = st.text_input("Matrícula Institucional:", key="form_mat")
            with c_e2: div_sel = st.selectbox("División Académica del Alumno:", list(ESTRUCTURA_UJAT.keys()), key="form_div")
                
            c_e3, c_e4 = st.columns(2)
            with c_e3:
                gen = st.selectbox("Género:", ["Masculino", "Femenino", "No Especificado"], key="form_gen")
                car = st.selectbox("Carrera del Alumno:", ESTRUCTURA_UJAT[div_sel], key="form_car")
            with c_e4:
                sem = st.selectbox("Semestre Actual:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="form_sem")
                tel = st.text_input("Teléfono de Contacto:", key="form_tel")
                cor = st.text_input("Correo Institucional:", key="form_cor")
            
            tags = st.text_input("Etiquetas Clínicas / Diagnóstico:", key="form_tags")
            obs = st.text_area("Notas Clínicas Detalladas del Caso:", key="form_obs")
            
            if st.button("Guardar Expediente"):
                if mat.strip() and nom.strip():
                    conn = conectar_db_local()
                    cursor = conn.cursor()
                    try:
                        tags_procesadas = ",".join([t.strip().lower() for t in tags.split(",") if t.strip()])
                        cursor.execute("""
                            INSERT INTO expedientes (matricula, nombre, genero, division, carrera, semestre, telefono, correo, observaciones, etiquetas)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (mat.strip(), nom.strip(), gen, div_sel, car, sem, tel, cor, obs, tags_procesadas))
                        conn.commit()
                        limpiar_formulario_expediente()
                        st.success("¡Expediente almacenado correctamente!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: La matrícula ya existe.")
                    finally:
                        conn.close()

    # --- MÓDULO 2: CITAS ---
    elif seccion == "📅 Agenda de Citas":
        st.markdown("<h3>Control y Agenda de Citas</h3>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns([1.8, 1.2])
        with col_c1:
            conn = conectar_db_local()
            df_cit = pd.read_sql_query("""
                SELECT c.id AS 'ID Cita', e.matricula AS 'Matrícula', e.nombre AS 'Paciente', c.fecha_hora AS 'Fecha/Hora'
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id ORDER BY c.fecha_hora DESC
            """, conn)
            conn.close()
            if not df_cit.empty: st.dataframe(df_cit, use_container_width=True)
            else: st.info("No hay citas programadas.")
        with col_c2:
            mat_buscar = st.text_input("Ingrese Matrícula del Alumno:")
            if mat_buscar.strip():
                conn = conectar_db_local()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM expedientes WHERE matricula = ?", (mat_buscar.strip(),))
                paciente = cursor.fetchone()
                conn.close()
                if paciente:
                    st.success(f"✅ Paciente: {paciente[1]}")
                    f_cita = st.date_input("Fecha:")
                    h_cita = st.time_input("Hora:")
                    motivo = st.text_area("Motivo:")
                    if st.button("Confirmar Cita"):
                        fecha_iso = datetime.combine(f_cita, h_cita).strftime("%Y-%m-%d %H:%M:%S")
                        conn = conectar_db_local()
                        conn.cursor().execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)", (paciente[0], fecha_iso, motivo))
                        conn.commit()
                        conn.close()
                        st.rerun()

    # --- MÓDULO 3: REPORTES ---
    elif seccion == "📊 Reportes Ejecutivos":
        st.markdown("<h3>Panel de Control</h3>", unsafe_allow_html=True)
        conn = conectar_db_local()
        tot_exp = conn.execute("SELECT COUNT(*) FROM expedientes").fetchone()[0]
        st.metric("Expedientes Totales Registrados", tot_exp)
        conn.close()