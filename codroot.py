# =================================================================
#           APLICACIÓN PRINCIPAL: codroot.py (VERSIÓN FILTRADA DE LOGOS)
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
    page_icon=LOGO_UJAT_URL,  # Se mantiene en la pestaña del navegador como favicon corporativo
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MOTOR DE CONEXIÓN LOCAL INTEGRADO (SQLite) ---
def conectar_db_local():
    try:
        conn = sqlite3.connect("centro_psicologico.db")
        return conn
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
# FLUJO 1: CONTROL DE ACCESO (PANTALLA DE LOGIN CON LOGO)
# -------------------------------------------------------------------------------------
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        .stApp { background-color: #ffffff !important; }
        div[data-testid="stWidgetLabel"] p, label { color: #37352f !important; font-weight: 500; }
        h1, h2 { color: #002f56 !important; font-weight: 700; text-align: center; }
        
        button, div.stButton > button {
            background-color: #002f56 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            border: 1px solid #002f56 !important;
            width: 100%;
        }
        button:hover, div.stButton > button:hover {
            background-color: #e1e4e6 !important;
            color: #002f56 !important;
            border: 1px solid #002f56 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col_izq, col_centro, col_der = st.columns([1.1, 1.3, 1.1])
    with col_centro:
        st.write("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        # 1. EVENTO ADMITIDO: Logo presente en la pantalla de login
        st.markdown(f'<div style="text-align:center; margin-bottom: 20px;"><img src="{LOGO_UJAT_URL}" width="160"></div>', unsafe_allow_html=True)
        
        if st.session_state.sub_pantalla_auth == "login":
            st.markdown("<h1>Consultorio Psicológico DACYTI</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#666;'>Sistema de Gestión Interdivisional - UJAT</p>", unsafe_allow_html=True)
            
            u_login = st.text_input("Usuario Corporativo:")
            p_login = st.text_input("Contraseña:", type="password")
            
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
                
            st.write("---")
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
# FLUJO 2: INTERFAZ DE ADMINISTRACIÓN INTERNA (ENCABEZADO CONSTANTE)
# -------------------------------------------------------------------------------------
else:
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #ffffff !important; }}
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p {{ color: #37352f !important; font-weight: 500 !important; }}
        .stDetails summary, div[data-testid="stExpander"] summary p {{ color: #213885 !important; font-weight: 600 !important; font-size: 16px !important; }}
        
        /* Contenedores Gris Claro */
        div[data-testid="stAlert"], .stAlert, div[data-testid="stCallout"] {{
            background-color: #f2f3f5 !important;
            color: #333333 !important;
            border-left: 5px solid #002f56 !important;
            border-radius: 6px;
        }}
        
        /* Estilo unificado de botones */
        div.stButton > button, .stButton button {{
            background-color: #002f56 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            border: 1px solid #002f56 !important;
            transition: all 0.2s ease-in-out !important;
        }}
        div.stButton > button:hover, .stButton button:hover {{
            background-color: #e1e4e6 !important;
            color: #002f56 !important;
            border: 1px solid #002f56 !important;
        }}
        [data-testid="stSidebar"] {{ background-color: #f4f5f6 !important; border-right: 1px solid #e0e0e0; }}
        
        /* Contenedor del Encabezado Constante */
        .constante-header-container {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            border-bottom: 2px solid #f0f0f2;
            padding-bottom: 15px;
        }}
        .constante-header-container h1 {{
            margin: 0 !important;
            color: #002f56 !important;
            font-weight: 700;
            font-size: 26px;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 2. EVENTO ADMITIDO: Renderizado global y único del encabezado con el logo junto a la leyenda indicada
    st.markdown(f"""
        <div class="constante-header-container">
            <img src="{LOGO_UJAT_URL}" width="45">
            <h1>Consultorio Psicológico DACYTI</h1>
        </div>
    """, unsafe_allow_html=True)

    # Navegación lateral
    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["📋 Expedientes Electrónicos", "📅 Agenda de Citas"])
    st.sidebar.write(f"👤 **Clínico:** {st.session_state.usuario_actual}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # --- MÓDULO 1: EXPEDIENTES ---
    if seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h3>Repositorio Unificado de Expedientes</h3>", unsafe_allow_html=True)
        
        c_f1, c_f2 = st.columns(2)
        with c_f1: bus_nom = st.text_input("🔍 Buscar por Nombre o Matrícula:")
        with c_f2: bus_tag = st.text_input("🏷️ Filtrar por Diagnóstico/Etiqueta (ej: ansiedad):")
        
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
            st.markdown("<p style='color:gray; font-size:12px;'>Complete todos los datos. Al presionar 'Guardar', el formulario se vaciará solo.</p>", unsafe_allow_html=True)
            
            # Nombre Completo como primera opción
            nom = st.text_input("Nombre Completo:", key="form_nom")
            
            # Matrícula e Indicador de división a un costado
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                mat = st.text_input("Matrícula Institucional:", key="form_mat")
            with c_e2:
                div_sel = st.selectbox("División Académica del Alumno:", list(ESTRUCTURA_UJAT.keys()), key="form_div")
                
            c_e3, c_e4 = st.columns(2)
            with c_e3:
                gen = st.selectbox("Género:", ["Masculino", "Femenino", "No Especificado"], key="form_gen")
                carreras_disponibles = ESTRUCTURA_UJAT[div_sel]
                car = st.selectbox("Carrera del Alumno:", carreras_disponibles, key="form_car")
            with c_e4:
                sem = st.selectbox("Semestre Actual:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="form_sem")
                tel = st.text_input("Teléfono de Contacto:", key="form_tel")
                cor = st.text_input("Correo Institucional:", key="form_cor")
            
            st.markdown("---")
            st.markdown("### 🏷️ Diagnóstico y Clasificación Clínica")
            st.info("💡 **Leyenda de Clasificación:** Escribe los síntomas o padecimientos detectados separados estrictamente por comas (Ejemplo: *ansiedad, depresion*).")
            
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
                        st.success("¡Expediente almacenado correctamente y formulario limpio!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: La matrícula ingresada ya se encuentra registrada en el sistema.")
                    finally:
                        conn.close()
                else:
                    st.warning("Rellene los campos obligatorios (Matrícula y Nombre).")

    # --- MÓDULO 2: CITAS ---
    elif seccion == "📅 Agenda de Citas":
        st.markdown("<h3>Control y Agenda de Citas</h3>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns([1.8, 1.2])
        
        with col_c1:
            st.markdown("### Historial de Sesiones")
            conn = conectar_db_local()
            df_cit = pd.read_sql_query("""
                SELECT c.id AS 'ID Cita', e.matricula AS 'Matrícula', e.nombre AS 'Paciente', 
                       e.division AS 'División', c.fecha_hora AS 'Fecha/Hora', c.motivo AS 'Motivo'
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id
                ORDER BY c.fecha_hora DESC
            """, conn)
            conn.close()
            if not df_cit.empty:
                st.dataframe(df_cit, use_container_width=True)
            else:
                st.info("No hay citas agendadas programadas.")
                
        with col_c2:
            st.markdown("### 🔍 Agendar por Matrícula")
            mat_buscar = st.text_input("Ingrese Matrícula del Alumno a buscar:")
            
            if mat_buscar.strip():
                conn = conectar_db_local()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre, division, carrera FROM expedientes WHERE matricula = ?", (mat_buscar.strip(),))
                paciente = cursor.fetchone()
                conn.close()
                
                if paciente:
                    id_interno, nombre_p, div_p, car_p = paciente
                    st.success(f"✅ **Paciente Encontrado:** {nombre_p} ({div_p} - {car_p})")
                    
                    f_cita = st.date_input("Programar Fecha:", value=datetime.now())
                    h_cita = st.time_input("Programar Hora:")
                    motivo = st.text_area("Motivo de la sesión de apoyo:")
                    
                    if st.button("Confirmar y Agendar Cita"):
                        fecha_iso = datetime.combine(f_cita, h_cita).strftime("%Y-%m-%d %H:%M:%S")
                        conn = conectar_db_local()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)", 
                                       (id_interno, fecha_iso, motivo))
                        conn.commit()
                        conn.close()
                        st.success("¡Cita agendada correctamente!")
                        st.rerun()
                else:
                    st.error("❌ No existe ningún expediente clínico con esa matrícula.")
            else:
                st.caption("Escriba la matrícula arriba para desplegar el formulario.")