import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (Identidad Visual Notion/Instagram)
# ==============================================================================
st.set_page_config(
    page_title="Consultorio Psicológico DACYTI",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
        }
        .main {
            background-color: #f8fafc;
        }
        /* Tarjetas estilo Notion */
        .notion-card {
            background: #ffffff;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            margin-bottom: 15px;
        }
        .fc-header {
            font-weight: 600;
            background-color: #f1f5f9;
            padding: 8px;
            text-align: center;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
        }
        .fc-day-box {
            background-color: #ffffff;
            min-height: 100px;
            padding: 6px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
        }
        .fc-event {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-bottom: 4px;
            font-weight: 500;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CAPA DE DATOS (Estructura Corregida con motivo_consulta)
# ==============================================================================
DB_PATH = 'consultorio.db'

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def inicializar_base_datos():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tabla de Expedientes (Columna correcta según Ledger: motivo_consulta)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expedientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE,
            nombre TEXT,
            genero TEXT,
            edad INTEGER,
            division TEXT,
            carrera TEXT,
            semestre TEXT,
            telefono TEXT,
            correo TEXT,
            etiquetas TEXT,
            motivo_consulta TEXT
        )
    """)
    
    # Tabla de Citas Clínicas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente_id INTEGER,
            fecha_hora TEXT,
            estado TEXT DEFAULT 'Pendiente',
            motivo TEXT,
            notas_evolucion TEXT,
            FOREIGN KEY(expediente_id) REFERENCES expedientes(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

inicializar_base_datos()

# ==============================================================================
# 3. CONTROL DE ESTADO DE SESIÓN (Navegación e Interacción)
# ==============================================================================
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "🏠 Inicio y Planner"

if "fecha_base_cal" not in st.session_state:
    st.session_state.fecha_base_cal = datetime.today().date()

# ==============================================================================
# 4. BARRA LATERAL (Panel de Navegación y Contexto)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🗂️ Módulos de Gestión")
    opciones_menu = ["🏠 Inicio y Planner", "📄 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"]
    seleccion = st.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.menu_actual))
    st.session_state.menu_actual = seleccion
    
    st.markdown("---")
    st.markdown("### 👤 Personal Encargado:")
    st.caption("psicologa.sara")

# ==============================================================================
# MÓDULO 1: INICIO Y PLANNER
# ==============================================================================
if st.session_state.menu_actual == "🏠 Inicio y Planner":
    st.title("🏫 Consultorio Psicológico DACYTI")
    st.subheader("Panel General de Control Clínico")
    
    # Tarjetas de Métricas de Carga General
    conn = conectar_db()
    total_exp = pd.read_sql_query("SELECT COUNT(*) as total FROM expedientes", conn)['total'][0]
    citas_pen = pd.read_sql_query("SELECT COUNT(*) as total FROM citas WHERE estado='Pendiente'", conn)['total'][0]
    citas_com = pd.read_sql_query("SELECT COUNT(*) as total FROM citas WHERE estado='Completada'", conn)['total'][0]
    conn.close()
    
    col_inf1, col_inf2, col_inf3 = st.columns(3)
    with col_inf1:
        st.metric(label="Expedientes Totales", value=int(total_exp))
    with col_inf2:
        st.metric(label="Sesiones Pendientes", value=int(citas_pen))
    with col_inf3:
        st.metric(label="Sesiones Concluidas", value=int(citas_com))

    st.markdown("---")
    st.subheader("📌 Próximas Citas Prioritarias (Hoy/Próximas)")
    
    conn = conectar_db()
    df_hoy = pd.read_sql_query("""
        SELECT e.nombre as Paciente, c.fecha_hora as [Fecha/Hora], c.estado as Estado, c.motivo as Motivo
        FROM citas c JOIN expedientes e ON c.expediente_id = e.id
        WHERE c.estado = 'Pendiente' ORDER BY c.fecha_hora ASC LIMIT 5
    """, conn)
    conn.close()
    
    if df_hoy.empty:
        st.info("No hay citas pendientes prioritarias en la agenda.")
    else:
        st.dataframe(df_hoy, use_container_width=True)

# ==============================================================================
# MÓDULO 2: EXPEDIENTES ELECTRÓNICOS
# ==============================================================================
elif st.session_state.menu_actual == "📄 Expedientes Electrónicos":
    st.title("📄 Gestión de Expedientes Electrónicos")
    
    exp_tab1, exp_tab2 = st.tabs(["📝 Abrir Nuevo Expediente", "🔍 Historial de Alumnos"])
    
    with exp_tab1:
        st.subheader("Complete los datos del alumno institucional")
        
        with st.form(key="form_crear_expediente", clear_on_submit=True):
            st.markdown("#### 🏛️ Ubicación Académica")
            div_aca = st.selectbox("División Académica:", ["DACYTI", "DAIA", "DACEA", "DAMJS"], key="exp_div_aca")
            
            carreras_dict = {
                "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
                "DAIA": ["Ingeniería Civil", "Ingeniería Mecánica", "Ingeniería Eléctrica"],
                "DACEA": ["Licenciatura en Administración", "Licenciatura en Contaduría Pública"],
                "DAMJS": ["Licenciatura en Derecho", "Licenciatura en Psicología"]
            }
            carrera_sel = st.selectbox("Carrera Universitaria:", carreras_dict.get(div_aca, ["General"]), key="exp_carrera_sel")
            
            st.markdown("---")
            st.markdown("#### 👤 Datos Personales y Clínicos")
            
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                nom_completo = st.text_input("Nombre Completo del Alumno:", key="exp_nom_completo")
                mat_institucional = st.text_input("Matrícula Institucional:", key="exp_mat_inst")
                edad_alumno = st.number_input("Edad:", min_value=15, max_value=90, value=20, key="exp_edad")
            with col_e2:
                gen_alumno = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"], key="exp_genero")
                sem_alumno = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"], key="exp_semestre")
                tel_contacto = st.text_input("Teléfono de Contacto:", key="exp_telefono")
                
            corr_electronico = st.text_input("Correo Electrónico:", key="exp_correo")
            tags_diag = st.text_input("Etiquetas Diagnósticas (separadas por comas):", key="exp_tags")
            mot_consulta = st.text_area("Motivo de Consulta Inicial:", key="exp_motivo")
            
            submit_exp = st.form_submit_button(label="Registrar Expediente Electrónico")
            
            if submit_exp:
                if not nom_completo or not mat_institucional:
                    st.error("❌ El nombre y la matrícula son obligatorios.")
                else:
                    try:
                        conn = conectar_db()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO expedientes (matricula, nombre, genero, edad, division, carrera, semestre, telefono, correo, etiquetas, motivo_consulta)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (mat_institucional.strip().upper(), nom_completo.strip(), gen_alumno, int(edad_alumno), div_aca, carrera_sel, sem_alumno, tel_contacto.strip(), corr_electronico.strip(), tags_diag.strip(), mot_consulta.strip()))
                        conn.commit()
                        conn.close()
                        st.success("✅ Expediente electrónico creado correctamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Error: Ya existe esa matrícula registrada.")

    with exp_tab2:
        st.subheader("🔍 Alumnos Registrados")
        conn = conectar_db()
        df_expedientes = pd.read_sql_query("SELECT id, matricula, nombre, carrera, etiquetas, motivo_consulta FROM expedientes", conn)
        conn.close()
        if not df_expedientes.empty:
            st.dataframe(df_expedientes, use_container_width=True)
        else:
            st.info("No hay expedientes en el sistema.")

# ==============================================================================
# MÓDULO 3: AGENDA DE CITAS (Visualizador Tipo Google Calendar Nativo)
# ==============================================================================
elif st.session_state.menu_actual == "📅 Agenda de Citas":
    st.title("📆 Control de Citas Clínicas e Historial de Sesiones")
    
    cit_tab1, cit_tab2 = st.tabs(["✨ Programar Nueva Cita", "📅 Visualizador Completo del Calendario"])
    
    with cit_tab1:
        st.subheader("📝 Registrar Nueva Cita")
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, matricula FROM expedientes ORDER BY nombre ASC")
        lista_pacientes = cursor.fetchall()
        conn.close()
        
        if not lista_pacientes:
            st.warning("⚠️ No existen expedientes registrados para asignar una cita.")
        else:
            dict_pacientes = {f"{p[1]} ({p[2]})": p[0] for p in lista_pacientes}
            
            with st.form(key="form_nueva_cita_agenda", clear_on_submit=True):
                paciente_sel = st.selectbox("Seleccionar Alumno Paciente:", options=list(dict_pacientes.keys()), key="agenda_pac_sel")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    fecha_cita = st.date_input("Fecha de la Consulta:", value=datetime.today(), key="agenda_fecha")
                with col_c2:
                    hora_cita = st.time_input("Hora de la Consulta:", value=datetime.now().time(), key="agenda_hora")
                motivo_cita = st.text_area("Motivo de la Sesión:", key="agenda_motivo")
                
                submit_cita = st.form_submit_button(label="Confirmar Cita Médica")
                if submit_cita:
                    fecha_hora_str = f"{fecha_cita} {hora_cita.strftime('%H:%M:%S')}"
                    try:
                        conn = conectar_db()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)",
                                       (dict_pacientes[paciente_sel], fecha_hora_str, motivo_cita.strip()))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Cita agendada de forma manual para {paciente_sel}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with cit_tab2:
        st.subheader("📅 Calendario Clínico Interactivo")
        
        # Selectores de periodo de tiempo estilo Google Calendar
        col_f1, col_f2, col_f3 = st.columns([2, 2, 4])
        with col_f1:
            periodo = st.selectbox("Formato Ajustado:", ["Día", "Semana", "Mes", "Año (Lista)"], index=2, key="cal_periodo")
        with col_f2:
            st.session_state.fecha_base_cal = st.date_input("Fecha Base Enfoque:", st.session_state.fecha_base_cal, key="cal_fecha_base")
            
        # Extraer citas de la base de datos
        conn = conectar_db()
        df_citas = pd.read_sql_query("""
            SELECT c.id, e.nombre, c.fecha_hora, c.estado, c.motivo, e.matricula, c.notas_evolucion
            FROM citas c JOIN expedientes e ON c.expediente_id = e.id
        """, conn)
        conn.close()
        
        df_citas['datetime'] = pd.to_datetime(df_citas['fecha_hora'])
        df_citas['fecha'] = df_citas['datetime'].dt.date
        df_citas['hora_str'] = df_citas['datetime'].dt.strftime('%H:%M')
        
        color_map = {"Pendiente": "#2e5bff", "Completada": "#2ecc71", "Cancelada": "#e74c3c"}
        
        # --- VISTA POR MES ---
        if periodo == "Mes":
            anio, mes = st.session_state.fecha_base_cal.year, st.session_state.fecha_base_cal.month
            st.markdown(f"### 🗓️ Vista de: **{st.session_state.fecha_base_cal.strftime('%B %Y').upper()}**")
            
            # Construcción de la matriz del mes
            primer_dia_mes = datetime(anio, mes, 1)
            dia_semana_inicio = primer_dia_mes.weekday() # 0 = Lunes
            dias_en_mes = (datetime(anio, mes + 1, 1) - primer_dia_mes).days if mes < 12 else 31
            
            dias_semana = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
            cols_header = st.columns(7)
            for idx, d in enumerate(dias_semana):
                cols_header[idx].markdown(f"<div class='fc-header'>{d}</div>", unsafe_allow_html=True)
                
            # Renderizado de días
            lista_dias = [None] * dia_semana_inicio + [primer_dia_mes.date() + timedelta(days=i) for i in range(dias_en_mes)]
            while len(lista_dias) % 7 != 0:
                lista_dias.append(None)
                
            for w in range(len(lista_dias) // 7):
                cols_dias = st.columns(7)
                for d_idx in range(7):
                    curr_date = lista_dias[w * 7 + d_idx]
                    if curr_date:
                        with cols_dias[d_idx]:
                            st.markdown(f"**{curr_date.day}**")
                            citas_del_dia = df_citas[df_citas['fecha'] == curr_date]
                            for _, c in citas_del_dia.iterrows():
                                bg = color_map.get(c['estado'], '#718096')
                                st.markdown(f"<div class='fc-event' style='background-color: {bg};'>⏱️ {c['hora_str']} - {c['nombre'][:12]}...</div>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

        # --- VISTA POR SEMANA ---
        elif periodo == "Semana":
            inicio_semana = st.session_state.fecha_base_cal - timedelta(days=st.session_state.fecha_base_cal.weekday())
            st.markdown(f"### 📅 Semana del {inicio_semana.strftime('%d/%m/%Y')} al {(inicio_semana + timedelta(days=6)).strftime('%d/%m/%Y')}")
            
            cols_sem = st.columns(7)
            dias_letras = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
            for i in range(7):
                dia_evaluar = inicio_semana + timedelta(days=i)
                with cols_sem[i]:
                    st.markdown(f"<div class='fc-header'>{dias_letras[i]} {dia_evaluar.day}</div>", unsafe_allow_html=True)
                    citas_sem = df_citas[df_citas['fecha'] == dia_evaluar]
                    if citas_sem.empty:
                        st.caption("Sin citas")
                    for _, c in citas_sem.iterrows():
                        bg = color_map.get(c['estado'], '#718096')
                        st.markdown(f"<div class='fc-event' style='background-color: {bg};'>{c['hora_str']} {c['nombre']}</div>", unsafe_allow_html=True)

        # --- VISTA POR DIA ---
        elif periodo == "Día":
            st.markdown(f"### 🎯 Citas del Día: {st.session_state.fecha_base_cal.strftime('%d de %B, %Y')}")
            citas_dia = df_citas[df_citas['fecha'] == st.session_state.fecha_base_cal].sort_values(by='hora_str')
            if citas_dia.empty:
                st.info("No hay citas médicas agendadas para este día.")
            else:
                for _, c in citas_dia.iterrows():
                    with st.container():
                        st.markdown(f"#### ⏱️ {c['hora_str']} hrs - Alumno: {c['nombre']} ({c['matricula']})")
                        st.write(f"**Motivo:** {c['motivo']}")
                        st.markdown(f"**Estado:** `{c['estado']}`")
                        st.markdown("---")

        # --- VISTA POR AÑO (LISTA) ---
        elif periodo == "Año (Lista)":
            anio_actual = st.session_state.fecha_base_cal.year
            st.markdown(f"### 📋 Agenda Anual Completa - Ciclo {anio_actual}")
            citas_anio = df_citas[df_citas['datetime'].dt.year == anio_actual].sort_values(by='datetime')
            if citas_anio.empty:
                st.info("No existen citas registradas en este año.")
            else:
                st.dataframe(citas_anio[['fecha_hora', 'nombre', 'matricula', 'estado', 'motivo']], use_container_width=True)

        # --- SECCIÓN INTERACTIVA DE GESTIÓN CLÍNICA ---
        st.markdown("---")
        st.subheader("⚙️ Panel de Actualización e Historial de Sesiones")
        if not df_citas.empty:
            opciones_citas_gestion = {f"{c['fecha']} a las {c['hora_str']} - {c['nombre']}": c['id'] for _, c in df_citas.iterrows()}
            cita_a_gestionar = st.selectbox("Seleccione la cita que desea atender o modificar:", list(opciones_citas_gestion.keys()))
            
            id_sel = opciones_citas_gestion[cita_a_gestionar]
            detalles_sel = df_citas[df_citas['id'] == id_sel].iloc[0]
            
            with st.form(key=f"form_evolucion_{id_sel}"):
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    nuevo_estado = st.selectbox("Cambiar Estado Clínico:", ["Pendiente", "Completada", "Cancelada"], index=["Pendiente", "Completada", "Cancelada"].index(detalles_sel['estado']))
                with col_g2:
                    st.markdown(f"**Matrícula Alumno:** {detalles_sel['matricula']}")
                
                notas_campo = st.text_area("Añadir Notas de Evolución / Seguimiento Clínico:", value=detalles_sel['notas_evolucion'] if detalles_sel['notas_evolucion'] else "")
                
                guardar_cambios = st.form_submit_button("Guardar Cambios Clínicos")
                if guardar_cambios:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (nuevo_estado, notas_campo.strip(), int(id_sel)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Cambios guardados de forma exitosa en el historial.")
                    st.rerun()

# ==============================================================================
# MÓDULO 4: REPORTES EJECUTIVOS
# ==============================================================================
elif st.session_state.menu_actual == "📊 Reportes Executives":
    st.title("📊 Reportes Ejecutivos")
    conn = conectar_db()
    df_rep = pd.read_sql_query("SELECT division, carrera FROM expedientes", conn)
    conn.close()
    
    if df_rep.empty:
        st.info("No hay datos clínicos para computar estadísticas.")
    else:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("##### Alumnos por División Académica")
            st.bar_chart(df_rep['division'].value_counts())
        with col_r2:
            st.markdown("##### Demandas de Atención por Carrera")
            st.bar_chart(df_rep['carrera'].value_counts())