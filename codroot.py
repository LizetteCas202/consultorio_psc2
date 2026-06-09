import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (Estética Limpia Notion)
# ==============================================================================
st.set_page_config(
    page_title="Consultorio Psicológico DACYTI",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS para emular la tipografía limpia de Notion
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
        }
        .main {
            background-color: #f8fafc;
        }
        .notion-card {
            background: #ffffff;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        .cal-header {
            font-weight: 600;
            background-color: #f1f5f9;
            padding: 10px;
            text-align: center;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            color: #1e293b;
            font-size: 0.9rem;
        }
        .cal-event-card {
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-top: 5px;
            font-weight: 500;
            color: white;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CAPA DE DATOS Y CONEXIÓN BASE DE DATOS
# ==============================================================================
DB_PATH = 'consultorio.db'

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def inicializar_base_datos():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tabla de Expedientes (Con la columna corregida 'motivo_consulta')
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
# 3. CONTROL DE ESTADO DE SESIÓN (Navegación e Interfaces Expansibles)
# ==============================================================================
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "🏠 Inicio y Planner"

if "mostrar_nuevo_expediente" not in st.session_state:
    st.session_state.mostrar_nuevo_expediente = False

if "mostrar_nueva_agenda" not in st.session_state:
    st.session_state.mostrar_nueva_agenda = False

if "fecha_navegacion_cal" not in st.session_state:
    st.session_state.fecha_navegacion_cal = datetime.today().date()

# ==============================================================================
# 4. BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.markdown("### 🗂️ Módulos de Gestión")
    st.write("Ir a:")
    
    opciones_menu = ["🏠 Inicio y Planner", "📄 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"]
    seleccion = st.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.menu_actual), label_visibility="collapsed")
    st.session_state.menu_actual = seleccion
    
    st.markdown("---")
    st.markdown("### 👤 Personal Encargado:")
    st.caption("psicologa.sara")

# ==============================================================================
# MÓDULO 1: INICIO Y PLANNER (RESTAURADO CON CONTROLES DESPLEGABLES COMPLETOS)
# ==============================================================================
if st.session_state.menu_actual == "🏠 Inicio y Planner":
    st.title("🏫 Consultorio Psicológico DACYTI")
    st.subheader("Panel General de Control Clínico")
    
    # Consultas para Métricas de la Pantalla de Inicio
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
    
    # Botones superiores de la pantalla de inicio para desplegar formularios avanzados
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("📝 Abrir Nuevo Expediente", use_container_width=True):
            st.session_state.mostrar_nuevo_expediente = not st.session_state.mostrar_nuevo_expediente
            st.session_state.mostrar_nueva_agenda = False
    with col_btn2:
        if st.button("📅 Nueva Agenda (Cita)", use_container_width=True):
            st.session_state.mostrar_nueva_agenda = not st.session_state.mostrar_nueva_agenda
            st.session_state.mostrar_nuevo_expediente = False

    # --------------------------------------------------------------------------
    # DESPLEGABLE INTERACTIVO: ABRIR NUEVO EXPEDIENTE (Estructura Fiel)
    # --------------------------------------------------------------------------
    if st.session_state.mostrar_nuevo_expediente:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            col_tit_exp, col_ret_exp = st.columns([3, 1])
            with col_tit_exp:
                st.markdown("### 📝 Abrir Nuevo Expediente")
                st.caption("Complete los datos del alumno institucional.")
            with col_ret_exp:
                if st.button("Retraer >>", key="btn_retraer_exp", use_container_width=True):
                    st.session_state.mostrar_nuevo_expediente = False
                    st.st.rerun()
            
            st.markdown("#### 🏛️ Ubicación Académica")
            div_aca = st.selectbox("División Académica:", ["DACYTI", "DAIA", "DACEA", "DAMJS"], key="inc_div_aca")
            
            carreras_dict = {
                "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
                "DAIA": ["Ingeniería Civil", "Ingeniería Mecánica", "Ingeniería Eléctrica"],
                "DACEA": ["Licenciatura en Administración", "Licenciatura en Contaduría Pública"],
                "DAMJS": ["Licenciatura en Derecho", "Licenciatura en Psicología"]
            }
            carrera_sel = st.selectbox("Carrera Universitaria:", carreras_dict.get(div_aca, ["General"]), key="inc_carrera_sel")
            
            st.markdown("---")
            st.markdown("#### 👤 Datos Personales y Clínicos")
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                nom_completo = st.text_input("Nombre Completo del Alumno:", key="inc_nom")
                mat_institucional = st.text_input("Matrícula Institucional:", key="inc_mat")
                edad_alumno = st.number_input("Edad:", min_value=15, max_value=90, value=20, key="inc_edad")
            with col_e2:
                gen_alumno = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"], key="inc_gen")
                sem_alumno = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"], key="inc_sem")
                tel_contacto = st.text_input("Teléfono de Contacto:", key="inc_tel")
                
            corr_electronico = st.text_input("Correo Electrónico:", key="inc_correo")
            tags_diag = st.text_input("Etiquetas Diagnósticas (separadas por comas):", key="inc_tags")
            mot_consulta = st.text_area("Motivo de Consulta Inicial:", key="inc_motivo")
            
            if st.button("Guardar Expediente Completo", key="btn_guardar_exp_inc"):
                if not nom_completo or not mat_institucional:
                    st.error("❌ Los campos Nombre y Matrícula son completamente obligatorios.")
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
                        st.success("✅ El expediente se ha registrado con éxito en la base de datos.")
                        st.session_state.mostrar_nuevo_expediente = False
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Conflicto: Esta matrícula ya se encuentra registrada en el sistema.")

    # --------------------------------------------------------------------------
    # DESPLEGABLE INTERACTIVO: NUEVA AGENDA (Estructura Fiel)
    # --------------------------------------------------------------------------
    if st.session_state.mostrar_nueva_agenda:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            col_tit_age, col_ret_age = st.columns([3, 1])
            with col_tit_age:
                st.markdown("### 📅 Nueva Agenda")
                st.caption("Complete los datos del alumno institucional para su cita.")
            with col_ret_age:
                if st.button("Retraer >>", key="btn_retraer_age", use_container_width=True):
                    st.session_state.mostrar_nueva_agenda = False
                    st.rerun()
                    
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, matricula FROM expedientes ORDER BY nombre ASC")
            alumnos_db = cursor.fetchall()
            conn.close()
            
            if not alumnos_db:
                st.warning("⚠️ No existen expedientes en el sistema. Abra un expediente primero.")
            else:
                opciones_alumnos = {f"{a[1]} ({a[2]})": a[0] for a in alumnos_db}
                alumno_asignado = st.selectbox("Seleccionar Alumno Paciente:", list(opciones_alumnos.keys()), key="inc_age_paciente")
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_elegida = st.date_input("Fecha de la Consulta:", value=datetime.today(), key="inc_age_fecha")
                with col_f2:
                    h_elegida = st.time_input("Hora de la Consulta:", value=datetime.now().time(), key="inc_age_hora")
                    
                mot_cita_new = st.text_area("Motivo o Descripción de Sesión:", key="inc_age_motivo")
                
                if st.button("Confirmar Cita Médica", key="btn_guardar_cita_inc", use_container_width=True):
                    timestamp_str = f"{f_elegida} {h_elegida.strftime('%H:%M:%S')}"
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)",
                                   (opciones_alumnos[alumno_asignado], timestamp_str, mot_cita_new.strip()))
                    conn.commit()
                    conn.close()
                    st.success("✅ Cita registrada de manera exitosa en la agenda.")
                    st.session_state.mostrar_nueva_agenda = False
                    st.rerun()

    # Sección inferior fija: Citas prioritarias
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
# MÓDULO 2: EXPEDIENTES ELECTRÓNICOS (PANTALLA EXCELENTE DE VISUALIZACIÓN DE BD)
# ==============================================================================
elif st.session_state.menu_actual == "📄 Expedientes Electrónicos":
    st.title("📄 Expedientes Electrónicos")
    st.subheader("🗃️ Base de Datos Completa de Expedientes Clínicos")
    
    conn = conectar_db()
    df_expedientes = pd.read_sql_query("""
        SELECT id as ID, matricula as [Matrícula], nombre as [Nombre Completo], 
               genero as [Género], edad as [Edad], division as [División], 
               carrera as [Carrera Universitaria], semestre as [Semestre], 
               telefono as [Teléfono], correo as [Correo], etiquetas as [Etiquetas Diagnósticas],
               motivo_consulta as [Motivo de Consulta Inicial]
        FROM expedientes ORDER BY id DESC
    """, conn)
    conn.close()
    
    if df_expedientes.empty:
        st.info("No se han localizado expedientes guardados en la Base de Datos.")
    else:
        busqueda = st.text_input("🔍 Filtrar expedientes por Nombre o Matrícula:", placeholder="Escriba aquí para buscar...")
        if busqueda:
            df_expedientes = df_expedientes[
                df_expedientes['Nombre Completo'].str.contains(busqueda, case=False, na=False) | 
                df_expedientes['Matrícula'].str.contains(busqueda, case=False, na=False)
            ]
        st.dataframe(df_expedientes, use_container_width=True)

# ==============================================================================
# MÓDULO 3: AGENDA DE CITAS (EXCLUSIVO CITAS: BD + CALENDARIO CRONOLÓGICO)
# ==============================================================================
elif st.session_state.menu_actual == "📅 Agenda de Citas":
    st.title("📅 Agenda de Citas")
    
    cit_tab1, cit_tab2 = st.tabs(["🗃️ Base de Datos de Citas", "📅 Segmentación Cronológica en Calendario"])
    
    conn = conectar_db()
    df_citas = pd.read_sql_query("""
        SELECT c.id as [ID Cita], e.nombre as [Paciente], e.matricula as [Matrícula], 
               c.fecha_hora as [Fecha y Hora], c.estado as [Estado], c.motivo as [Motivo], 
               c.notas_evolucion as [Notas de Evolución]
        FROM citas c JOIN expedientes e ON c.expediente_id = e.id
        ORDER BY c.fecha_hora DESC
    """, conn)
    conn.close()
    
    if not df_citas.empty:
        df_citas['datetime_obj'] = pd.to_datetime(df_citas['Fecha y Hora'])
        df_citas['fecha_solo'] = df_citas['datetime_obj'].dt.date
        df_citas['hora_solo'] = df_citas['datetime_obj'].dt.strftime('%H:%M')

    # --- TAB 1: BASE DE DATOS DE TODAS LAS CITAS ---
    with cit_tab1:
        st.subheader("📁 Registro Completo e Historial de Citas")
        if df_citas.empty:
            st.info("No hay citas registradas en el sistema.")
        else:
            st.dataframe(df_citas.drop(columns=['datetime_obj', 'fecha_solo', 'hora_solo'], errors='ignore'), use_container_width=True)

    # --- TAB 2: SECCIONAR DE FORMA CRONOLÓGICA (FORMATO CALENDARIO) ---
    with cit_tab2:
        st.subheader("🗓️ Visualizador de Calendario Clínico")
        
        col_view1, col_view2 = st.columns([2, 3])
        with col_view1:
            rango_tiempo = st.selectbox("Formato Ajustado:", ["Diario", "Semanal", "Mensual (Carga General)", "Anual (Lista)"], index=2, key="cal_rango_view")
        with col_view2:
            st.session_state.fecha_navegacion_cal = st.date_input("Fecha Base Enfoque:", st.session_state.fecha_navegacion_cal, key="cal_fecha_enfoque")
            
        color_status = {"Pendiente": "#2e5bff", "Completada": "#2ecc71", "Cancelada": "#e74c3c"}
        
        if df_citas.empty:
            st.info("Sin registros clínicos para segmentar en formato calendario.")
        else:
            # --- FORMATO DIARIO ---
            if rango_tiempo == "Diario":
                st.markdown(f"#### 🎯 Citas del Día: {st.session_state.fecha_navegacion_cal.strftime('%d/%m/%Y')}")
                df_dia = df_citas[df_citas['fecha_solo'] == st.session_state.fecha_navegacion_cal].sort_values(by='hora_solo')
                if df_dia.empty:
                    st.caption("No existen citas programadas para este día.")
                else:
                    for _, row in df_dia.iterrows():
                        bg = color_status.get(row['Estado'], '#718096')
                        st.markdown(f"""
                            <div style='background-color:{bg}; padding:12px; border-radius:8px; color:white; margin-bottom:10px;'>
                                <strong>⏱️ {row['hora_solo']} hrs</strong> - {row['Paciente']} ({row['Matrícula']}) <br>
                                <small>Motivo: {row['Motivo']} | Estado: {row['Estado']}</small>
                            </div>
                        """, unsafe_allow_html=True)

            # --- FORMATO SEMANAL ---
            elif rango_tiempo == "Semanal":
                ini_sem = st.session_state.fecha_navegacion_cal - timedelta(days=st.session_state.fecha_navegacion_cal.weekday())
                st.markdown(f"#### 📅 Periodo Semanal: {ini_sem.strftime('%d/%m/%Y')} al {(ini_sem + timedelta(days=6)).strftime('%d/%m/%Y')}")
                
                cols_semanales = st.columns(7)
                dias_nom = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                
                for i in range(7):
                    dia_eval = ini_sem + timedelta(days=i)
                    with cols_semanales[i]:
                        st.markdown(f"<div class='cal-header'>{dias_nom[i]} {dia_eval.day}</div>", unsafe_allow_html=True)
                        df_sem_dia = df_citas[df_citas['fecha_solo'] == dia_eval]
                        for _, row in df_sem_dia.iterrows():
                            bg = color_status.get(row['Estado'], '#718096')
                            st.markdown(f"<div class='cal-event-card' style='background-color:{bg};'>⏱️ {row['hora_solo']}<br>{row['Paciente'][:12]}...</div>", unsafe_allow_html=True)

            # --- FORMATO MENSUAL ---
            elif rango_tiempo == "Mensual (Carga General)":
                aa, mm = st.session_state.fecha_navegacion_cal.year, st.session_state.fecha_navegacion_cal.month
                st.markdown(f"#### 🗓️ Vista Mensual: {st.session_state.fecha_navegacion_cal.strftime('%B %Y').upper()}")
                
                prim_dia = datetime(aa, mm, 1)
                offset = prim_dia.weekday()
                tot_dias = (datetime(aa, mm + 1, 1) - prim_dia).days if mm < 12 else 31
                
                headers_mes = st.columns(7)
                dias_abreviados = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                for idx, h in enumerate(dias_abreviados):
                    headers_mes[idx].markdown(f"<div class='cal-header'>{h}</div>", unsafe_allow_html=True)
                    
                celdas = [None] * offset + [prim_dia.date() + timedelta(days=i) for i in range(tot_dias)]
                while len(celdas) % 7 != 0:
                    celdas.append(None)
                    
                for fila in range(len(celdas) // 7):
                    cols_mes_render = st.columns(7)
                    for c_idx in range(7):
                        celda_fecha = celdas[fila * 7 + c_idx]
                        if celda_fecha:
                            with cols_mes_render[c_idx]:
                                st.markdown(f"**{celda_fecha.day}**")
                                df_mes_dia = df_citas[df_citas['fecha_solo'] == celda_fecha]
                                for _, row in df_mes_dia.iterrows():
                                    bg = color_status.get(row['Estado'], '#718096')
                                    st.markdown(f"<div class='cal-event-card' style='background-color:{bg}; padding:2px 4px; font-size:10px;'>{row['hora_solo']} - {row['Paciente'][:8]}</div>", unsafe_allow_html=True)

            # --- FORMATO ANUAL ---
            elif rango_tiempo == "Anual (Lista)":
                target_year = st.session_state.fecha_navegacion_cal.year
                st.markdown(f"#### 📋 Agenda Completa Cronológica - Año {target_year}")
                df_anio = df_citas[df_citas['datetime_obj'].dt.year == target_year].sort_values(by='datetime_obj')
                if df_anio.empty:
                    st.caption("No existen registros de citas para este año.")
                else:
                    st.dataframe(df_anio.drop(columns=['datetime_obj', 'fecha_solo', 'hora_solo']), use_container_width=True)

        # Gestión rápida externa para cambiar estados o guardar evolución clínica
        if not df_citas.empty:
            st.markdown("---")
            st.subheader("⚙️ Actualización Rápida de Historial Clínico")
            
            mapeo_edicion = {f"Cita ID {r['ID Cita']} - Paciente: {r['Paciente']} ({r['Fecha y Hora']})": r['ID Cita'] for _, r in df_citas.iterrows()}
            seleccion_c = st.selectbox("Seleccione la consulta a modificar:", list(mapeo_edicion.keys()), key="select_edicion_cita")
            
            id_c_sel = mapeo_edicion[seleccion_c]
            info_actual_cita = df_citas[df_citas['ID Cita'] == id_c_sel].iloc[0]
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                nuevo_st = st.selectbox("Estatus Clínico:", ["Pendiente", "Completada", "Cancelada"], index=["Pendiente", "Completada", "Cancelada"].index(info_actual_cita['Estado']), key=f"est_ut_{id_c_sel}")
            with col_u2:
                nuevas_notas = st.text_area("Notas de Evolución:", value=info_actual_cita['Notas de Evolución'] if info_actual_cita['Notas de Evolución'] else "", key=f"not_ut_{id_c_sel}")
            
            if st.button("Guardar Cambios en Registro", key=f"btn_save_ut_{id_c_sel}"):
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (nuevo_st, nuevas_notas.strip(), int(id_c_sel)))
                conn.commit()
                conn.close()
                st.success("✅ Historial clínico guardado correctamente.")
                st.rerun()

# ==============================================================================
# MÓDULO 4: REPORTES EJECUTIVOS
# ==============================================================================
elif st.session_state.menu_actual == "📊 Reportes Ejecutivos":
    st.title("📊 Reportes Ejecutivos")
    conn = conectar_db()
    df_rep = pd.read_sql_query("SELECT division, carrera FROM expedientes", conn)
    conn.close()
    
    if df_rep.empty:
        st.info("No se localizan datos en la Base de Datos para generar métricas estadísticas.")
    else:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("##### Distribución por División Académica")
            st.bar_chart(df_rep['division'].value_counts())
        with col_r2:
            st.markdown("##### Demandas de Atención por Carrera")
            st.bar_chart(df_rep['carrera'].value_counts())