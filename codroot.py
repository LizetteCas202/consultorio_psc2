# =================================================================
#           APLICACIÓN PRINCIPAL: codroot.py (VERSIÓN WEB STREAMLIT)
# =================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from codconexion import crear_tablas_iniciales, conectar_db
from codauth import verificar_credenciales, inicializar_usuario_admin, registrar_usuario, recuperar_clave_por_pregunta
from codestadisticas import renderizar_reportes_direccion, obtener_dataframe

# Configuración Inicial de la Página Web estilo Minimalista
st.set_page_config(
    page_title="Centro Psicológico UJAT",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo Personalizado para emular la estética limpia de Notion
st.markdown("""
    <style>
    .main { background-color: #fafafa; color: #333333; }
    [data-testid="stSidebar"] { background-color: #f4f5f6; }
    h1, h2, h3 { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-weight: 600; }
    div.stButton > button:first-child { background-color: #2eaadc; color: white; border-radius: 6px; border: none; }
    </style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos en la Nube / Local
crear_tablas_iniciales()
inicializar_usuario_admin()

# Control de Estado de Sesión Autenticada
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""

# -----------------------------------------------------------------
# PANTALLA DE LOG-IN / CONTROL DE ACCESO
# -----------------------------------------------------------------
if not st.session_state.autenticado:
    st.title("🧠 Centro Psicológico Unidad Chontalpa - UJAT")
    st.subheader("Sistema Integral de Gestión de Citas y Expedientes Clínicos")
    
    pestana_login, pestana_registro, pestana_recuperar = st.tabs(["🔒 Iniciar Sesión", "📝 Registrar Nuevo Personal", "🔑 Recuperar Cuenta"])
    
    with pestana_login:
        user_input = st.text_input("Usuario Corporativo:")
        pass_input = st.text_input("Contraseña:", type="password")
        if st.button("Ingresar al Portal"):
            if verificar_credenciales(user_input, pass_input):
                st.session_state.autenticado = True
                st.session_state.usuario_actual = user_input
                st.success(f"¡Bienvenida comadre! Iniciando sesión como {user_input}")
                st.rerun()
            else:
                st.error("Credenciales incorrectas. Verifica tu usuario o contraseña.")
                
    with pestana_registro:
        st.markdown("### Alta de nuevo Psicólogo/Terapeuta")
        new_user = st.text_input("Definir nombre de usuario:")
        new_pass = st.text_input("Definir contraseña de acceso:", type="password")
        pregunta = st.selectbox("Selecciona una pregunta de seguridad:", [
            "¿Cuál es tu división académica de adscripción?",
            "¿Cuál es el nombre de tu primer paciente de prueba?",
            "¿Clave de empleado institucional?"
        ])
        respuesta = st.text_input("Respuesta Secreta:")
        if st.button("Confirmar Registro"):
            if new_user and new_pass and respuesta:
                exito, msg = registrar_usuario(new_user, new_pass, "Psicologo", pregunta, respuesta)
                if exito: st.success(msg)
                else: st.error(msg)
            else:
                st.warning("Por favor rellena todos los campos.")
                
    with pestana_recuperar:
        st.markdown("### Restablecimiento de Credenciales de Seguridad")
        rec_user = st.text_input("Ingresa tu usuario corporativo:")
        rec_resp = st.text_input("Escribe tu respuesta secreta a la pregunta configurada:")
        new_pass_reset = st.text_input("Nueva contraseña de acceso:", type="password")
        if st.button("Reestablecer Acceso"):
            exito, msg = recuperar_clave_por_pregunta(rec_user, rec_resp, new_pass_reset)
            if exito: st.success(msg)
            else: st.error(msg)

# -----------------------------------------------------------------
# INTERFAZ WEB INTERNA (USUARIO AUTENTICADO)
# -----------------------------------------------------------------
else:
    # Barra Lateral Estilo Notion (Filtrado Global Ligero y Navegación)
    st.sidebar.title("🗂️ Navegación")
    seccion = st.sidebar.radio("Ir a:", ["📋 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"])
    
    st.sidebar.write("---")
    st.sidebar.write(f"**Operador:** {st.session_state.usuario_actual}")
    if st.sidebar.button("Cerrar Sesión Segura"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.rerun()
        
    # Carreras oficiales de la DACYTI/UJAT para control de catálogos sin errores
    CARRERAS_UJAT = [
        "Licenciatura en Tecnologías de la Información",
        "Licenciatura en Sistemas Computacionales",
        "Licenciatura en Telemática",
        "Ingeniería en Informática Administrativa"
    ]

    # SECCIÓN 1: EXPEDIENTES ELECTRÓNICOS (Estilo Notion con filtrado reactivo)
    if seccion == "📋 Expedientes Electrónicos":
        st.title("📋 Repositorio de Expedientes Electrónicos")
        st.caption("Filtros instantáneos optimizados para bajo ancho de banda del campus.")
        
        # Barra de búsqueda integrada estilo Notion en la parte superior
        busqueda_col1, busqueda_col2 = st.columns([2, 1])
        with busqueda_col1:
            filtro_nombre = st.text_input("🔍 Buscar paciente por Nombre o Matrícula:")
        with busqueda_col2:
            filtro_tag = st.text_input("🏷️ Filtrar por etiqueta de Notion (ej: Ansiedad, Estrés):")

        # Construcción dinámica de Query para ahorrar consumo de servidor
        query = "SELECT * FROM expedientes WHERE 1=1"
        params = []
        if filtro_nombre:
            query += " AND (nombre ILIKE %s OR matricula ILIKE %s)"
            params.extend([f"%{filtro_nombre}%", f"%{filtro_nombre}%"])
        if filtro_tag:
            query += " AND etiquetas ILIKE %s"
            params.append(f"%{filtro_tag}%")
            
        df_expedientes = obtener_dataframe(query, tuple(params) if params else None)
        
        # Tabla Interactiva Simplificada
        if not df_expedientes.empty:
            st.dataframe(df_expedientes[["matricula", "nombre", "carrera", "semestre", "etiquetas", "observaciones"]], use_container_width=True)
        else:
            st.info("No se encontraron registros clínicos coincidentes.")
            
        # Formulario de Registro / Modificación colapsable para no saturar la pantalla
        with st.expander("➕ Crear Nuevo Expediente Clínico"):
            with st.form("form_expediente"):
                mat = st.text_input("Matrícula Institucional (Clave única):")
                nom = st.text_input("Nombre Completo del Alumno:")
                gen = st.selectbox("Género:", ["Masculino", "Femenino", "No Especificado"])
                car = st.selectbox("Carrera Universitaria:", CARRERAS_UJAT)
                sem = st.select_slider("Semestre Actual:", options=["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "Pasante"])
                tel = st.text_input("Teléfono de Contacto:")
                cor = st.text_input("Correo Institucional:")
                tags = st.text_input("Etiquetas de Seguimiento (Separadas por comas, ej: Estrés, Académico):")
                obs = st.text_area("Observaciones Clínicas Iniciales:")
                
                if st.form_submit_button("Guardar Expediente de Forma Permanente"):
                    if mat and nom:
                        conn = conectar_db()
                        if conn:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO expedientes (matricula, nombre, genero, carrera, semestre, telefono, correo, observaciones, etiquetas)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (mat, nom, gen, car, sem, tel, cor, obs, tags))
                                conn.commit()
                                st.success("¡Expediente almacenado correctamente!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al insertar en DB: {e}")
                            finally:
                                conn.close()
                    else:
                        st.warning("La matrícula y el nombre son obligatorios.")

    # SECCIÓN 2: AGENDA CRONOLÓGICA DE CITAS
    elif seccion == "📅 Agenda de Citas":
        st.title("📅 Agenda de Citas del Consultorio")
        
        col_agenda_1, col_agenda_2 = st.columns([2, 1])
        
        with col_agenda_1:
            st.subheader("Citas Programadas de la Semana")
            df_citas_completas = obtener_dataframe("""
                SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo 
                FROM citas c JOIN expedientes e ON c.expediente_id = e.id 
                ORDER BY c.fecha_hora DESC
            """)
            if not df_citas_completas.empty:
                st.dataframe(df_citas_completas, use_container_width=True)
            else:
                st.info("No hay citas pendientes agendadas.")
                
        with col_agenda_2:
            st.subheader("Agendar Nueva Cita")
            df_pacientes = obtener_dataframe("SELECT id, nombre, matricula FROM expedientes")
            if not df_pacientes.empty:
                lista_pacientes = {f"{row['nombre']} ({row['matricula']})": row['id'] for _, row in df_pacientes.iterrows()}
                paciente_seleccionado = st.selectbox("Seleccionar Alumno:", options=list(lista_pacientes.keys()))
                
                fecha_cita = st.date_input("Fecha de Consulta:", min_value=datetime.today())
                hora_cita = st.time_input("Hora de Consulta:")
                motivo_cita = st.text_area("Motivo o Síntomas declarados:")
                
                if st.button("Confirmar Espacio de Cita"):
                    exp_id = lista_pacientes[paciente_seleccionado]
                    fecha_completa = datetime.combine(fecha_cita, hora_cita)
                    
                    conn = conectar_db()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) 
                                VALUES (%s, %s, 'Pendiente', %s)
                            """, (exp_id, fecha_completa, motivo_cita))
                            conn.commit()
                            st.success("¡Cita agendada de forma exitosa!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al agendar cita: {e}")
                        finally:
                            conn.close()
            else:
                st.warning("Primero debes registrar un Expediente Clínico para poder agendar una cita.")

    # SECCIÓN 3: REPORTES ESTADÍSTICOS (CONECTADO AL MÓDULO DE ANALÍTICA)
    elif seccion == "📊 Reportes Ejecutivos":
        renderizar_reportes_direccion()
