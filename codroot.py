import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (Identidad Visual Notion / Interfaz Limpia)
# ==============================================================================
st.set_page_config(
    page_title="Consultorio Psicológico DACYTI",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS detallados para mantener la estética limpia solicitada
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
        }
        .main {
            background-color: #f8fafc;
        }
        /* Contenedor estilo Notion */
        .notion-card {
            background: #ffffff;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        /* Cabeceras de Calendario Cronológico */
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
        /* Bloques de eventos en el calendario */
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
# 2. CAPA DE DATOS (Conexión Estricta y Estructura Corregida)
# ==============================================================================
DB_PATH = 'consultorio.db'

def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def inicializar_base_datos():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tabla de Expedientes (Mantiene la columna 'motivo_consulta' corregida de tu Ledger)
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
# 3. CONTROL DE ESTADO DE SESIÓN (Navegación Persistente)
# ==============================================================================
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "🏠 Inicio y Planner"

if "fecha_navegacion_cal" not in st.session_state:
    st.session_state.fecha_navegacion_cal = datetime.today().date()

# ==============================================================================
# 4. BARRA LATERAL (Idéntica a la original de tus capturas)
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
# MÓDULO 1: INICIO Y PLANNER (Fiel a la vista de control general)
# ==============================================================================
if st.session_state.menu_actual == "🏠 Inicio y Planner":
    st.title("🏫 Consultorio Psicológico DACYTI")
    st.subheader("Panel General de Control Clínico")
    
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
# MÓDULO 2: EXPEDIENTES ELECTRÓNICOS (Regresado a la versión excelente completa)
# ==============================================================================
elif st.session_state.menu_actual == "📄 Expedientes Electrónicos":
    st.title("📄 Gestión de Expedientes Electrónicos")
    
    exp_tab1, exp_tab2 = st.tabs(["🔍 Base de Datos de Expedientes", "📝 Abrir Nuevo Expediente"])
    
    with exp_tab1:
        st.subheader("🗃️ Registro General de Alumnos")
        conn = conectar_db()
        # Se extrae toda la información sin recortes para la visualización de la BD
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
            # Buscador avanzado integrado sobre la Base de Datos
            busqueda = st.text_input("🔍 Buscar alumno por Nombre o Matrícula:", placeholder="Ej. Alumno o matrícula...")
            if busqueda:
                df_expedientes = df_expedientes[
                    df_expedientes['Nombre Completo'].str.contains(busqueda, case=False, na=False) | 
                    df_expedientes['Matrícula'].str.contains(busqueda, case=False, na=False)
                ]
            st.dataframe(df_expedientes, use_container_width=True)
            
    with exp_tab2:
        st.subheader("📝 Formulario de Alta Clínica")
        with st.form(key="form_alta_expediente", clear_on_submit=True):
            st.markdown("#### 🏛️ Ubicación Académica")
            div_aca = st.selectbox("División Académica:", ["DACYTI", "DAIA", "DACEA", "DAMJS"], key="form_div_aca")
            
            carreras_dict = {
                "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
                "DAIA": ["Ingeniería Civil", "Ingeniería Mecánica", "Ingeniería Eléctrica"],
                "DACEA": ["Licenciatura en Administración", "Licenciatura en Contaduría Pública"],
                "DAMJS": ["Licenciatura en Derecho", "Licenciatura en Psicología"]
            }
            carrera_sel = st.selectbox("Carrera Universitaria:", carreras_dict.get(div_aca, ["General"]), key="form_carrera_sel")
            
            st.markdown("---")
            st.markdown("#### 👤 Datos Demográficos e Iniciales")
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                nom_completo = st.text_input("Nombre Completo del Alumno:", key="form_nom")
                mat_institucional = st.text_input("Matrícula Institucional:", key="form_mat")
                edad_alumno = st.number_input("Edad:", min_value=15, max_value=90, value=20, key="form_edad")
            with col_e2:
                gen_alumno = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"], key="form_gen")
                sem_alumno = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"], key="form_sem")
                tel_contacto = st.text_input("Teléfono de Contacto:", key="form_tel")
                
            corr_electronico = st.text_input("Correo Electrónico:", key="form_correo")
            tags_diag = st.text_input("Etiquetas Diagnósticas (separadas por comas):", key="form_tags")
            mot_consulta = st.text_area("Motivo de Consulta Inicial:", key="form_motivo")
            
            submit_exp = st.form_submit_button(label="Guardar Expediente Completo")
            if submit_exp:
                if not nom_completo or not mat_institucional:
                    st.error("❌ Los campos Nombre y Matrícula son obligatorios.")
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
                        st.success("✅ El expediente se ha registrado de forma impecable en la BD.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Conflicto: La matrícula colocada ya existe en el sistema.")

# ==============================================================================
# MÓDULO 3: AGENDA DE CITAS (Solo Citas: Base de Datos + Filtro Cronológico)
# ==============================================================================
elif st.session_state.menu_actual == "📅 Agenda de Citas":
    st.title("📅 Módulo Exclusivo de Agenda de Citas")
    
    cit_tab1, cit_tab2, cit_tab3 = st.tabs(["🗃️ Base de Datos de Citas", "📅 Segmentación Cronológica (Calendario)", "📝 Registrar Nueva Cita"])
    
    # Extracción unificada para los componentes del módulo
    conn = conectar_db()
    df_citas = pd.read_sql_query("""
        SELECT c.id as [ID Cita], e.nombre as [Paciente], e.matricula as [Matrícula], 
               c.fecha_hora as [Fecha y Hora], c.estado as [Estado], c.motivo as [Motivo], 
               c.notas_evolucion as [Notas de Evolución]
        FROM citas c JOIN expedientes e ON c.expediente_id = e.id
        ORDER BY c.fecha_hora DESC
    """, conn)
    conn.close()
    
    # Procesar campos de tiempo si existen registros
    if not df_citas.empty:
        df_citas['datetime_obj'] = pd.to_datetime(df_citas['Fecha y Hora'])
        df_citas['fecha_solo'] = df_citas['datetime_obj'].dt.date
        df_citas['hora_solo'] = df_citas['datetime_obj'].dt.strftime('%H:%M')

    # --- TAB 1: BASE DE DATOS DE CITAS ---
    with cit_tab1:
        st.subheader("📁 Historial Completo de Citas Registradas")
        if df_citas.empty:
            st.info("No se registran citas agendadas dentro del consultorio.")
        else:
            st.dataframe(df_citas.drop(columns=['datetime_obj', 'fecha_solo', 'hora_solo'], errors='ignore'), use_container_width=True)

    # --- TAB 2: SEGMENTACIÓN CRONOLÓGICA TIPO GOOGLE CALENDAR ---
    with cit_tab2:
        st.subheader("🗓️ Visualización Temporal Avanzada")
        
        col_view1, col_view2 = st.columns([2, 3])
        with col_view1:
            rango_tiempo = st.selectbox("Segmentar vista por:", ["Día", "Semana", "Mes", "Año (Lista)"], index=2, key="sel_rango")
        with col_view2:
            st.session_state.fecha_navegacion_cal = st.date_input("Fecha de Enfoque:", st.session_state.fecha_navegacion_cal, key="input_fecha_nav")
            
        color_status = {"Pendiente": "#2e5bff", "Completada": "#2ecc71", "Cancelada": "#e74c3c"}
        
        if df_citas.empty:
            st.info("Sin registros para segmentar.")
        else:
            # --- VISTA DÍA ---
            if rango_tiempo == "Día":
                st.markdown(f"#### 🎯 Agenda diaria: {st.session_state.fecha_navegacion_cal.strftime('%d/%m/%Y')}")
                df_dia = df_citas[df_citas['fecha_solo'] == st.session_state.fecha_navegacion_cal].sort_values(by='hora_solo')
                if df_dia.empty:
                    st.caption("No existen citas médicas asignadas a esta fecha.")
                else:
                    for _, row in df_dia.iterrows():
                        bg = color_status.get(row['Estado'], '#718096')
                        st.markdown(f"""
                            <div style='background-color:{bg}; padding:12px; border-radius:8px; color:white; margin-bottom:10px;'>
                                <strong>⏱️ {row['hora_solo']} hrs</strong> - {row['Paciente']} ({row['Matrícula']}) <br>
                                <small>Motivo: {row['Motivo']} | Estado: {row['Estado']}</small>
                            </div>
                        """, unsafe_allow_html=True)

            # --- VISTA SEMANA ---
            elif rango_tiempo == "Semana":
                ini_sem = st.session_state.fecha_navegacion_cal - timedelta(days=st.session_state.fecha_navegacion_cal.weekday())
                st.markdown(f"#### 📅 Semana: {ini_sem.strftime('%d/%m/%Y')} al {(ini_sem + timedelta(days=6)).strftime('%d/%m/%Y')}")
                
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

            # --- VISTA MES ---
            elif rango_tiempo == "Mes":
                aa, mm = st.session_state.fecha_navegacion_cal.year, st.session_state.fecha_navegacion_cal.month
                st.markdown(f"#### 🗓️ Periodo Mensual: {st.session_state.fecha_navegacion_cal.strftime('%B %Y').upper()}")
                
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

            # --- VISTA ANUAL ---
            elif rango_tiempo == "Año (Lista)":
                target_year = st.session_state.fecha_navegacion_cal.year
                st.markdown(f"#### 📋 Relación Cronológica de Sesiones - Ciclo {target_year}")
                df_anio = df_citas[df_citas['datetime_obj'].dt.year == target_year].sort_values(by='datetime_obj')
                if df_anio.empty:
                    st.caption("No existen registros clínicos para este año.")
                else:
                    st.dataframe(df_anio.drop(columns=['datetime_obj', 'fecha_solo', 'hora_solo']), use_container_width=True)

        # Interconectividad directa para actualización de estados desde la agenda
        if not df_citas.empty:
            st.markdown("---")
            st.subheader("⚙️ Gestión Rápida de Estados Clínicos")
            mapeo_edicion = {f"Cita ID {r['ID Cita']} - Paciente: {r['Paciente']} ({r['Fecha y Hora']})": r['ID Cita'] for _, r in df_citas.iterrows()}
            seleccion_c = st.selectbox("Seleccione la consulta a modificar:", list(mapeo_edicion.keys()))
            
            id_c_sel = mapeo_edicion[seleccion_c]
            info_actual_cita = df_citas[df_citas['ID Cita'] == id_c_sel].iloc[0]
            
            with st.form(key=f"form_update_c_{id_c_sel}"):
                c_est, c_not = st.columns(2)
                with c_est:
                    nuevo_st = st.selectbox("Estatus clínico:", ["Pendiente", "Completada", "Cancelada"], index=["Pendiente", "Completada", "Cancelada"].index(info_actual_cita['Estado']))
                with c_not:
                    nuevas_notas = st.text_area("Notas de evolución actualizadas:", value=info_actual_cita['Notas de Evolución'] if info_actual_cita['Notas de Evolución'] else "")
                
                submit_update_c = st.form_submit_button("Guardar Cambios en Registro")
                if submit_update_c:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE citas SET estado = ?, notas_evolucion = ? WHERE id = ?", (nuevo_st, 此_not_val := nuevas_notas.strip(), int(id_c_sel)))
                    conn.commit()
                    conn.close()
                    st.success("✅ Registro e historial clínico actualizado de forma correcta.")
                    st.rerun()

    # --- TAB 3: REGISTRAR NUEVA CITA ---
    with cit_tab3:
        st.subheader("📝 Agendación Manual de Sesión")
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, matricula FROM expedientes ORDER BY nombre ASC")
        alumnos_db = cursor.fetchall()
        conn.close()
        
        if not alumnos_db:
            st.warning("⚠️ No se puede agendar debido a que no existen expedientes clínicos creados.")
        else:
            opciones_alumnos = {f"{a[1]} ({a[2]})": a[0] for a in alumnos_db}
            with st.form(key="form_alta_cita_exclusivo", clear_on_submit=True):
                alumno_asignado = st.selectbox("Asignar a Alumno Paciente:", list(opciones_alumnos.keys()))
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_elegida = st.date_input("Fecha programada:", value=datetime.today())
                with col_f2:
                    h_elegida = st.time_input("Hora programada:", value=datetime.now().time())
                mot_cita_new = st.text_area("Breve desglose o motivo de sesión:")
                
                submit_nueva_cita = st.form_submit_button("Confirmar Nueva Cita")
                if submit_nueva_cita:
                    timestamp_str = f"{f_elegida} {h_elegida.strftime('%H:%M:%S')}"
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)",
                                   (opciones_alumnos[alumno_asignado], timestamp_str, mot_cita_new.strip()))
                    conn.commit()
                    conn.close()
                    st.success("✅ Cita ingresada al sistema de manera exitosa.")
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
        st.info("No se localizan datos suficientes en la Base de Datos para generar métricas estadísticas.")
    else:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("##### Distribución por División Académica")
            st.bar_chart(df_rep['division'].value_counts())
        with col_r2:
            st.markdown("##### Demandas de Atención por Carrera")
            st.bar_chart(df_rep['carrera'].value_counts())