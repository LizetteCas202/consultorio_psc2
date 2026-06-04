# =================================================================
#           APLICACIÓN PRINCIPAL: codroot.py (VERSIÓN WEB STREAMLIT)
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from codconexion import crear_tablas_iniciales, conectar_db
from codauth import verificar_credenciales, inicializar_usuario_admin, registrar_usuario, recuperar_clave_por_pregunta
from codestadisticas import renderizar_reportes_direccion, obtener_dataframe

# Configuración Inicial Estilo Notion
st.set_page_config(
    page_title="Centro Psicológico UJAT",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------------------
# DISEÑO CSS ULTRA-PRECONSTRUIDO: Corrige el contraste sin romper los inputs
# -------------------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Fondo principal de la aplicación */
    .main { 
        background-color: #ffffff !important; 
        color: #111111 !important; 
    }
    
    /* Forzar títulos en color oscuro */
    h1, h2, h3, h4, h5, h6 { 
        color: #111111 !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }
    
    /* BARRA LATERAL: Fondo gris claro y limpio */
    [data-testid="stSidebar"] {
        background-color: #f4f5f6 !important;
        border-right: 1px solid #e0e0e0 !important;
    }
    
    /* ARREGLO DE TEXTO: Apuntar exclusivamente a las letras de las opciones del menú */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span[data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #111111 !important;
        font-weight: 500 !important;
    }
    
    /* Mantener las cajas de texto internas limpias y con fondo blanco */
    [data-testid="stSidebar"] input {
        background-color: #ffffff !important;
        color: #111111 !important;
    }

    /* Estilo elegante para el botón de acción principal */
    div.stButton > button:first-child { 
        background-color: #2eaadc !important; 
        color: white !important; 
        border-radius: 6px !important; 
        border: none !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos y Admin
crear_tablas_iniciales()
inicializar_usuario_admin()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""

# PANTALLA DE LOG-IN
if not st.session_state.autenticado:
    st.title("🧠 Centro Psicológico Unidad Chontalpa - UJAT")
    st.subheader("Sistema Integral de Gestión de Citas y Expedientes")
    
    pestana_login, pestana_registro, pestana_recuperar = st.tabs(["🔒 Iniciar Sesión", "📝 Registrar Personal", "🔑 Recuperar Cuenta"])
    
    with pestana_login:
        user_input = st.text_input("Usuario Corporativo (Prueba: psicologa.sara):")
        pass_input = st.text_input("Contraseña (Prueba: admin123):", type="password")
        if st.button("Ingresar al Portal"):
            if verificar_credenciales(user_input, pass_input):
                st.session_state.autenticado = True
                st.session_state.usuario_actual = user_input
                st.success(f"¡Bienvenida! Ingresando como {user_input}")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
                
    with pestana_registro:
        st.markdown("### Alta de nuevo Terapeuta")
        new_user = st.text_input("Definir nombre de usuario:")
        new_pass = st.text_input("Definir contraseña:", type="password")
        pregunta = st.selectbox("Pregunta de seguridad:", ["¿Unidad de origen?", "¿Clave de empleado?"])
        respuesta = st.text_input("Respuesta Secreta:")
        if st.button("Confirmar Registro"):
            if new_user and new_pass and respuesta:
                exito, msg = registrar_usuario(new_user, new_pass, "Psicologo", pregunta, respuesta)
                if exito: st.success(msg)
                else: st.error(msg)
                
    with pestana_recuperar:
        st.markdown("### Restablecimiento de Credenciales")
        rec_user = st.text_input("Usuario corporativo:")
        rec_resp = st.text_input("Respuesta secreta:")
        new_pass_reset = st.text_input("Nueva contraseña:", type="password")
        if st.button("Reestablecer Acceso"):
            exito, msg = recuperar_clave_por_pregunta(rec_user, rec_resp, new_pass_reset)
            if exito: st.success(msg)
            else: st.error(msg)

# INTERFAZ WEB INTERNA
else:
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

    if seccion == "📋 Expedientes Electrónicos":
        st.title("📋 Repositorio de Expedientes Electrónicos")
        
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
            with st.form("form_expediente"):
                mat = st.text_input("Matrícula Institucional:")
                nom = st.text_input("Nombre Completo:")
                gen = st.selectbox("Género:", ["Masculino", "Femenino", "No Especificado"])
                car = st.selectbox("Carrera:", CARRERAS_UJAT)
                sem = st.selectbox("Semestre:", options=["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no"])
                tel = st.text_input("Teléfono:")
                cor = st.text_input("Correo:")
                tags = st.text_input("Etiquetas (Separadas por comas):")
                obs = st.text_area("Observaciones Clínicas:")
                
                if st.form_submit_button("Guardar Expediente"):
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
                                st.success("¡Expediente guardado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                conn.close()
                    else:
                        st.warning("Matrícula y Nombre obligatorios.")

    elif seccion == "📅 Agenda de Citas":
        st.title("📅 Agenda de Citas del Consultorio")
        col_1, col_2 = st.columns([2, 1])
        
        with col_1:
            st.subheader("Citas Registradas")
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
            st.subheader("Agendar Nueva Cita")
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