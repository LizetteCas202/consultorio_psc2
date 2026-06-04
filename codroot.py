# =================================================================
#           APLICACIÓN PRINCIPAL: codroot.py (VERSIÓN INSTITUCIONAL)
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

# URL Oficial del Escudo UJAT (Solicitado para Pestaña y Login)
LOGO_UJAT_URL = "https://images.seeklogo.com/logo-png/23/1/ujat-tabasco-logo-png_seeklogo-233582.png"

# --- 1. CONFIGURACIÓN DE PÁGINA (CAMBIO DE EMOJI A LOGO UJAT) ---
st.set_page_config(
    page_title="Centro Psicológico UJAT",
    page_icon=LOGO_UJAT_URL,  # Reemplazado el emoji por el logo oficial
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. MOTOR DE CONEXIÓN LOCAL INTEGRADO (SQLite) ---
def conectar_db_local():
    """Establece conexión con la base de datos SQLite local."""
    try:
        conn = sqlite3.connect("centro_psicologico.db")
        return conn
    except Exception as e:
        st.error(f"Error al conectar a la base de datos local: {e}")
        return None

def inicializar_sistema_db():
    """Crea las tablas con la estructura de autenticación, divisiones y etiquetas."""
    conn = conectar_db_local()
    if conn:
        cursor = conn.cursor()
        # Tabla de usuarios (personal administrativo/clínico)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                clave_hash TEXT NOT NULL,
                rol TEXT NOT NULL,
                pregunta_secreta TEXT,
                respuesta_secreta_hash TEXT
            )
        """)
        # Tabla de expedientes clínicos
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
        # Tabla de citas
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
        # Insertar usuario administrador por defecto si no existe
        cursor.execute("SELECT * FROM usuarios WHERE usuario = 'psicologa.sara'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave_hash, rol, pregunta_secreta, respuesta_secreta_hash)
                VALUES ('psicologa.sara', 'admin123', 'Director/Psicólogo', '¿Unidad de origen?', 'chontalpa')
            """)
        conn.commit()
        conn.close()

# Inicializar Base de Datos al arrancar
inicializar_sistema_db()

# --- 3. MANEJO DE ESTADOS DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = ""
if "sub_pantalla_auth" not in st.session_state: st.session_state.sub_pantalla_auth = "login"

# Estados para la autolimpieza de contenedores del formulario
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

# --- 4. DICCIONARIO DE DIVISIONES Y CARRERAS UJAT ---
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
# FLUJO 1: CONTROL DE ACCESO (LOGIN)
# -------------------------------------------------------------------------------------
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        .stApp { background-color: #ffffff !important; }
        div[data-testid="stWidgetLabel"] p, label { color: #37352f !important; font-weight: 500; }
        h1, h2 { color: #002f56 !important; font-weight: 700; text-align: center; }
        
        /* Contraste estricto en botones de ingreso */
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
        # Despliegue de la imagen solicitada en el Login
        st.markdown(f'<div style="text-align:center; margin-bottom: 20px;"><img src="{LOGO_UJAT_URL}" width="160"></div>', unsafe_allow_html=True)
        
        if st.session_state.sub_pantalla_auth == "login":
            st.markdown("<h1>Centro Psicológico</h1>", unsafe_allow_html=True)
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
                        st.error("El nombre de usuario ya se encuentra registrado.")
                    finally:
                        conn.close()
            if st.button("⬅️ Cancelar"): st.session_state.sub_pantalla_auth = "login"; st.rerun()

        elif st.session_state.sub_pantalla_auth == "recuperar":
            st.markdown("<h2>🔑 Restablecer Acceso</h2>", unsafe_allow_html=True)
            rec_user = st.text_input("Usuario corporativo:")
            rec_resp = st.text_input("Respuesta secreta:")
            new_pass_reset = st.text_input("Nueva contraseña:", type="password")
            
            if st.button("Reestablecer Contraseña"):
                conn = conectar_db_local()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND respuesta_secreta_hash=?", (rec_user, rec_resp))
                if cursor.fetchone():
                    cursor.execute("UPDATE usuarios SET clave_hash=? WHERE usuario=?", (new_pass_reset, rec_user))
                    conn.commit()
                    st.success("¡Contraseña actualizada correctamente!")
                    st.session_state.sub_pantalla_auth = "login"
                    st.rerun()
                else:
                    st.error("Respuesta de seguridad o usuario incorrectos.")
                conn.close()
            if st.button("⬅️ Volver al Login"): st.session_state.sub_pantalla_auth = "login"; st.rerun()

# -------------------------------------------------------------------------------------
# FLUJO 2: INTERFAZ DE ADMINISTRACIÓN INTERNA
# -------------------------------------------------------------------------------------
else:
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff !important; }
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p { color: #37352f !important; font-weight: 500 !important; }
        .stDetails summary, div[data-testid="stExpander"] summary p { color: #213885 !important; font-weight: 600 !important; font-size: 16px !important; }
        h1, h2, h3 { color: #002f56 !important; font-weight: 700; }
        
        /* Regla de diseño dinámico para botones */
        div.stButton > button, .stButton button {
            background-color: #002f56 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            border: 1px solid #002f56 !important;
            transition: all 0.2s ease-in-out !important;
        }
        div.stButton > button:hover, .stButton button:hover {
            background-color: #e1e4e6 !important;
            color: #002f56 !important;
            border: 1px solid #002f56 !important;
        }
        [data-testid="stSidebar"] { background-color: #f4f5f6 !important; border-right: 1px solid #e0e0e0; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🗂️ Módulos de Gestión")
    seccion = st.sidebar.radio("Ir a:", ["📋 Expedientes Electrónicos", "📅 Agenda de Citas"])
    st.sidebar.write(f"👤 **Clínico:** {st.session_state.usuario_actual}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # --- MÓDULO 1: EXPEDIENTES ---
    if seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h1>📋 Repositorio Unificado de Expedientes</h1>", unsafe_allow_html=True)
        
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
            
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                mat = st.text_input("Matrícula Institucional:", key="form_mat")
                nom = st.text_input("Nombre Completo:", key="form_nom")
                gen = st.selectbox("Género:", ["Masculino", "Femenino", "No Especificado"], key="form_gen")
                div_sel = st.selectbox("División Académica:", list(ESTRUCTURA_UJAT.keys()), key="form_div")
            with c_e2:
                carreras_disponibles = ESTRUCTURA_UJAT[div_sel]
                car = st.selectbox("Carrera del Alumno:", carreras_disponibles, key="form_car")
                sem = st.selectbox("Semestre Actual:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="form_sem")
                tel = st.text_input("Teléfono de Contacto:", key="form_tel")
                cor = st.text_input("Correo Institucional:", key="form_cor")
            
            st.markdown("---")
            st.markdown("### 🏷️ Diagnóstico y Clasificación Clínica")
            st.info("💡 **Leyenda de Clasificación:** Escribe los síntomas o padecimientos detectados separados estrictamente por comas (Ejemplo: *ansiedad, depresion, estres academico*). Esto permitirá localizarlos al instante en el buscador principal estilo Notion.")
            
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

    # --- MÓDULO 2: CITAS OPTIMIZADO POR MATRÍCULA ---
    elif seccion == "📅 Agenda de Citas":
        st.markdown("<h1>📅 Control y Agenda de Citas</h1>", unsafe_allow_html=True)
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
            st.markdown("### 🔍 Agendar por Matrícula (Optimizado)")
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
                st.caption("Escriba la matrícula arriba para desplegar el formulario de asignación de cita.")