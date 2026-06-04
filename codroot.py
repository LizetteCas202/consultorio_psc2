# =================================================================
#           APLICACIÓN PRINCIPAL: codroot.py (FIX BOTONES Y LIMPIEZA)
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from codconexion import crear_tablas_iniciales, conectar_db
from codauth import verificar_credenciales, inicializar_usuario_admin, registrar_usuario, recuperar_clave_por_pregunta
from codestadisticas import renderizar_reportes_direccion, obtener_dataframe

# Configuración Inicial Estilo Web Profesional UJAT
st.set_page_config(
    page_title="Centro Psicológico UJAT",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Base de Datos y Admin
crear_tablas_iniciales()
inicializar_usuario_admin()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""
if "sub_pantalla_auth" not in st.session_state:
    st.session_state.sub_pantalla_auth = "login"

# Inicializar variables del formulario en session_state para la limpieza automática
if "form_mat" not in st.session_state: st.session_state.form_mat = ""
if "form_nom" not in st.session_state: st.session_state.form_nom = ""
if "form_gen" not in st.session_state: st.session_state.form_gen = "Masculino"
if "form_car" not in st.session_state: st.session_state.form_car = "Licenciatura en Tecnologías de la Información"
if "form_sem" not in st.session_state: st.session_state.form_sem = "1ro"
if "form_tel" not in st.session_state: st.session_state.form_tel = ""
if "form_cor" not in st.session_state: st.session_state.form_cor = ""
if "form_tags" not in st.session_state: st.session_state.form_tags = ""
if "form_obs" not in st.session_state: st.session_state.form_obs = ""

# Función para vaciar los campos del formulario tras un guardado exitoso
def limpiar_formulario_expediente():
    st.session_state.form_mat = ""
    st.session_state.form_nom = ""
    st.session_state.form_gen = "Masculino"
    st.session_state.form_car = "Licenciatura en Tecnologías de la Información"
    st.session_state.form_sem = "1ro"
    st.session_state.form_tel = ""
    st.session_state.form_cor = ""
    st.session_state.form_tags = ""
    st.session_state.form_obs = ""

# URL Alternativa del Escudo UJAT
LOGO_UJAT_URL = "https://images.seeklogo.com/logo-png/23/1/ujat-tabasco-logo-png_seeklogo-233582.png"

# -------------------------------------------------------------------------------------
# FLUJO 1: PANTALLA DE LOG-IN EXCLUSIVA
# -------------------------------------------------------------------------------------
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        
        .stApp {
            background-color: #ffffff !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p {
            color: #37352f !important;
            font-weight: 500 !important;
            font-size: 14px !important;
        }
        
        h1 {
            color: #002f56 !important;
            font-weight: 700 !important;
            font-size: 28px !important;
        }
        
        p.subtitulo-ujat {
            color: #666666 !important;
            font-size: 14px !important;
            text-align: center !important;
        }
        
        input {
            color: #111111 !important;
            background-color: #f9f9fb !important;
            border: 1px solid #e1e4e6 !important;
            border-radius: 8px !important;
        }
        
        /* FIX BOTÓN LOG-IN CONSTANTE */
        div.stButton > button:first-child { 
            background-color: #002f56 !important; 
            color: #ffffff !important; 
            border-radius: 8px !important; 
            font-weight: 600 !important;
            padding: 12px !important;
            border: 1px solid #002f56 !important;
        }
        div.stButton > button:first-child:hover {
            background-color: #e1e4e6 !important;
            color: #002f56 !important;
            border: 1px solid #002f56 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col_izq, col_centro, col_der = st.columns([1.1, 1.3, 1.1])
    with col_centro:
        st.write("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        st.markdown(f'<div style="display: flex; justify-content: center; margin-bottom: 15px;"><img src="{LOGO_UJAT_URL}" width="120"></div>', unsafe_allow_html=True)
        
        if st.session_state.sub_pantalla_auth == "login":
            st.markdown("<h1 style='text-align: center;'>Centro Psicológico</h1>", unsafe_allow_html=True)
            st.markdown("<p class='subtitulo-ujat'>División Académica de Ciencias y Tecnologías de la Información</p>", unsafe_allow_html=True)
            
            user_input = st.text_input("Usuario Corporativo:")
            pass_input = st.text_input("Contraseña:", type="password")
            
            if st.button("Ingresar al Portal"):
                if verificar_credenciales(user_input, pass_input):
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = user_input
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            
            st.write("<div style='margin-top: 25px; border-top: 1px solid #eee; padding-top: 15px;'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📝 Registrarse"):
                    st.session_state.sub_pantalla_auth = "registro"
                    st.rerun()
            with c2:
                if st.button("🔑 Olvidé mi clave"):
                    st.session_state.sub_pantalla_auth = "recuperar"
                    st.rerun()

        elif st.session_state.sub_pantalla_auth == "registro":
            st.markdown("<h2 style='text-align: center;'>📝 Registro de Personal</h2>", unsafe_allow_html=True)
            new_user = st.text_input("Definir nombre de usuario:")
            new_pass = st.text_input("Definir contraseña:", type="password")
            pregunta = st.selectbox("Pregunta de seguridad:", ["¿Unidad de origen?", "¿Clave de empleado?"])
            respuesta = st.text_input("Respuesta Secreta:")
            if st.button("Confirmar Registro"):
                if new_user and new_pass and respuesta:
                    exito, msg = registrar_usuario(new_user, new_pass, "Psicologo", pregunta, respuesta)
                    if exito: st.session_state.sub_pantalla_auth = "login"; st.rerun()
            if st.button("⬅️ Volver al Login"): st.session_state.sub_pantalla_auth = "login"; st.rerun()

        elif st.session_state.sub_pantalla_auth == "recuperar":
            st.markdown("<h2 style='text-align: center;'>🔑 Restablecer Acceso</h2>", unsafe_allow_html=True)
            rec_user = st.text_input("Usuario corporativo:")
            rec_resp = st.text_input("Respuesta secreta:")
            new_pass_reset = st.text_input("Nueva contraseña:", type="password")
            if st.button("Reestablecer Contraseña"):
                exito, msg = recuperar_clave_por_pregunta(rec_user, rec_resp, new_pass_reset)
                if exito: st.session_state.sub_pantalla_auth = "login"; st.rerun()
            if st.button("⬅️ Volver al Login"): st.session_state.sub_pantalla_auth = "login"; st.rerun()

# -------------------------------------------------------------------------------------
# FLUJO 2: INTERFAZ CLÍNICA INTERNA (FIX SUPREMO DE VISIBILIDAD DE BOTONES EN HOVER)
# -------------------------------------------------------------------------------------
else:
    st.markdown("""
        <style>
        .stApp { 
            background-color: #ffffff !important; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        
        /* Forzar visibilidad en textos y etiquetas internas */
        div[data-testid="stWidgetLabel"] p, label, .stMarkdown p, span[data-testid="stWidgetLabel"] p {
            color: #37352f !important;
            font-weight: 500 !important;
        }
        
        /* Título del Expander */
        .stDetails summary, div[data-testid="stExpander"] details summary p, div[data-testid="stExpander"] p {
            color: #37352f !important;
            font-weight: 600 !important;
        }
        
        h1, h2, h3 { 
            color: #002f56 !important; 
            font-weight: 700 !important;
        }
        
        /* --- CORE FIX: CONTROL TOTAL DE BOTONES (NORMAL VS HOVER) --- */
        /* Aplica a botones normales, de formularios y de envío */
        div.stButton > button, 
        div[data-testid="stForm"] div.stButton > button,
        .stButton button { 
            background-color: #002f56 !important; 
            color: #ffffff !important; 
            border-radius: 6px !important; 
            font-weight: 600 !important;
            border: 1px solid #002f56 !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        /* Al pasar el cursor, cambia el fondo y el texto cambia a azul oscuro de forma segura */
        div.stButton > button:hover, 
        div[data-testid="stForm"] div.stButton > button:hover,
        .stButton button:hover {
            background-color: #e1e4e6 !important; 
            color: #002f56 !important; 
            border: 1px solid #002f56 !important;
        }
        
        /* Barra lateral */
        [data-testid="stSidebar"] {
            background-color: #f4f5f6 !important;
            border-right: 1px solid #e0e0e0 !important;
        }
        [data-testid="stSidebar"] h3 {
            color: #002f56 !important;
            font-size: 18px !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label p {
            color: #002f56 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }
        
        input, select, textarea { 
            color: #111111 !important; 
            background-color: #ffffff !important; 
            border: 1px solid #cccccc !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Panel de Navegación Lateral Interno
    st.sidebar.markdown("### 🗂️ Navegación")
    seccion = st.sidebar.radio(
        "Seleccione un módulo:", 
        ["📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"]
    )
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Operador:** {st.session_state.usuario_actual}")
    if st.sidebar.button("Cerrar Sesión Segura"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.rerun()
        
    CARRERAS_UJAT = [
        "Licenciatura en Tecnologías de la Información",
        "Licenciatura en Sistemas Computacionales",
        "Licenciatura en Telemática",
        "Ingeniería en Informática Administrativa"
    ]

    # --- CONTENIDO DE LOS MÓDULOS ---
    if seccion == "📋 Expedientes Electrónicos":
        st.markdown("<h1>📋 Repositorio de Expedientes Electrónicos</h1>", unsafe_allow_html=True)
        
        busqueda_col1, busqueda_col2 = st.columns([2, 1])
        with busqueda_col1:
            filtro_nombre = st.text_input("🔍 Buscar paciente por Nombre o Matrícula:")
        with busqueda_col2:
            filtro_tag = st.text_input("🏷️ Filtrar por etiqueta (ej: Ansiedad, Estrés):")

        query = "SELECT * FROM expedientes WHERE 1=1"
        params = []
        if filtro_nombre:
            query += " AND (nombre LIKE ? OR matricula LIKE ?)"
            params.extend([f"%{filtro_nombre}%", f"%{filtro_nombre}%"])
        if filtro_tag:
            query += " AND etiquetas LIKE ?"
            params.append(f"%{filtro_tag}%")
            
        df_expedientes = obtener_dataframe(query, tuple(params) if params else None)
        
        if not df_expedientes.empty:
            st.dataframe(df_expedientes[["matricula", "nombre", "carrera", "semestre", "etiquetas", "observaciones"]], use_container_width=True)
        else:
            st.info("No se encontraron registros clínicos.")
            
        with st.expander("➕ Crear Nuevo Expediente Clínico"):
            # Usamos inputs enlazados al session_state para limpiarlos automáticamente al guardar
            mat = st.text_input("Matrícula Institucional:", key="form_mat")
            nom = st.text_input("Nombre Completo:", key="form_nom")
            gen = st.selectbox("Género:", ["Masculino", "Femenino", "No Especificado"], key="form_gen")
            car = st.selectbox("Carrera:", CARRERAS_UJAT, key="form_car")
            sem = st.selectbox("Semestre:", options=["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"], key="form_sem")
            tel = st.text_input("Teléfono:", key="form_tel")
            cor = st.text_input("Correo:", key="form_cor")
            tags = st.text_input("Etiquetas (Separadas por comas):", key="form_tags")
            obs = st.text_area("Observaciones Clínicas:", key="form_obs")
            
            # Botón con contraste perfecto y callback de limpieza automática
            if st.button("Guardar Expediente"):
                if mat and nom:
                    conn = conectar_db()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO expedientes (matricula, nombre, genero, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (mat, nom, gen, car, sem, tel, cor, obs, tags))
                            conn.commit()
                            
                            # Ejecutar limpieza de variables
                            limpiar_formulario_expediente()
                            st.success("¡Expediente guardado exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                        finally:
                            conn.close()
                else:
                    st.warning("Matrícula y Nombre obligatorios.")

    elif seccion == "📅 Agenda de Citas":
        st.markdown("<h1>📅 Agenda de Citas del Consultorio</h1>", unsafe_allow_html=True)
        col_1, col_2 = st.columns([2, 1])
        
        with col_1:
            st.markdown("<h3>Citas Registradas</h3>", unsafe_allow_html=True)
            df_citas_completas = obtener_dataframe("""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id 
                ORDER BY c.fecha_hora DESC
            """)
            if not df_citas_completas.empty:
                st.dataframe(df_citas_completas, use_container_width=True)
            else:
                st.info("No hay citas agendadas.")
                
        with col_2:
            st.markdown("<h3>Agendar Nueva Cita</h3>", unsafe_allow_html=True)
            df_pacientes = obtener_dataframe("SELECT id, nombre, matricula FROM expedientes")
            if not df_pacientes.empty:
                lista_pacientes = {f"{row['nombre']} ({row['matricula']})": row['id'] for _, row in df_pacientes.iterrows()}
                paciente_sel = st.selectbox("Seleccionar Alumno:", options=list(lista_pacientes.keys()))
                fecha_cita = st.date_input("Fecha:")
                hora_cita = st.time_input("Hora:")
                motivo_cita = st.text_area("Motivo:")
                
                if st.button("Confirmar Cita"):
                    exp_id = lista_pacientes[paciente_sel]
                    fecha_completa = datetime.combine(fecha_cita, hora_cita).strftime("%Y-%m-%d %H:%M:%S")
                    conn = conectar_db()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) 
                                VALUES (?, ?, 'Pendiente', ?)
                            """, (exp_id, fecha_completa, motivo_cita))
                            conn.commit()
                            st.success("¡Cita agendada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()
            else:
                st.warning("Primero debes registrar un expediente.")

    elif seccion == "📊 Reportes Ejecutivos":
        renderizar_reportes_direccion()