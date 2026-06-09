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

# Inyección de CSS para emular la tipografía de Notion y el estilo de la app
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
        
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
        }
        .main {
            background-color: #f8fafc;
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
    
    # Tabla de Expedientes
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
# 3. CONTROL DE ESTADO DE SESIÓN (Navegación e Interfaces de Costado)
# ==============================================================================
if "menu_actual" not in st.session_state:
    st.session_state.menu_actual = "🏠 Inicio y Planner"

# Vista lateral activa: "navegacion", "nuevo_expediente", "nueva_cita"
if "sub_vista_lateral" not in st.session_state:
    st.session_state.sub_vista_lateral = "navegacion"

if "fecha_navegacion_cal" not in st.session_state:
    st.session_state.fecha_navegacion_cal = datetime.today().date()

# ==============================================================================
# 4. BARRA LATERAL DINÁMICA (VENTANA DE COSTADO ESTILO NOTION)
# ==============================================================================
with st.sidebar:
    # --- CASO 1: NAVEGACIÓN GENERAL ---
    if st.session_state.sub_vista_lateral == "navegacion":
        st.markdown("### 🗂️ Módulos de Gestión")
        st.write("Ir a:")
        
        opciones_menu = ["🏠 Inicio y Planner", "📄 Expedientes Electrónicos", "📅 Agenda de Citas", "📊 Reportes Ejecutivos"]
        seleccion = st.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.menu_actual), label_visibility="collapsed")
        st.session_state.menu_actual = seleccion
        
        st.markdown("---")
        st.markdown("### 👤 Personal Encargado:")
        st.caption("psicologa.sara")

    # --- CASO 2: FORMULARIO LATERAL DE NUEVO EXPEDIENTE ---
    elif st.session_state.sub_vista_lateral == "nuevo_expediente":
        st.markdown("### 📝 Abrir Nuevo Expediente")
        st.caption("Complete los datos del alumno en esta ventana lateral.")
        
        if st.button("<< Volver al Menú", use_container_width=True):
            st.session_state.sub_vista_lateral = "navegacion"
            st.rerun()
            
        st.markdown("---")
        st.markdown("#### 🏛️ Ubicación Académica")
        div_aca = st.selectbox("División Académica:", ["DACYTI", "DAIA", "DACEA", "DAMJS"])
        
        carreras_dict = {
            "DACYTI": ["Licenciatura en Tecnologías de la Información", "Licenciatura en Sistemas Computacionales", "Licenciatura en Telemática", "Ingeniería en Informática Administrativa"],
            "DAIA": ["Ingeniería Civil", "Ingeniería Mecánica", "Ingeniería Eléctrica"],
            "DACEA": ["Licenciatura en Administración", "Licenciatura en Contaduría Pública"],
            "DAMJS": ["Licenciatura en Derecho", "Licenciatura en Psicología"]
        }
        carrera_sel = st.selectbox("Carrera Universitaria:", carreras_dict.get(div_aca, ["General"]))
        
        st.markdown("#### 👤 Datos Personales")
        nom_completo = st.text_input("Nombre Completo:")
        mat_institucional = st.text_input("Matrícula Institucional:")
        edad_alumno = st.number_input("Edad:", min_value=15, max_value=90, value=20)
        gen_alumno = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
        sem_alumno = st.selectbox("Semestre:", ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"])
        tel_contacto = st.text_input("Teléfono de Contacto:")
        corr_electronico = st.text_input("Correo Electrónico:")
        tags_diag = st.text_input("Etiquetas (separadas por comas):")
        mot_consulta = st.text_area("Motivo de Consulta Inicial:")
        
        if st.button("Guardar Expediente", use_container_width=True, type="primary"):
            if not nom_completo or not mat_institucional:
                st.error("❌ Nombre y Matrícula obligatorios.")
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
                    st.success("✅ ¡Expediente Guardado!")
                    st.session_state.sub_vista_lateral = "navegacion"
                    st.session_state.menu_actual = "📄 Expedientes Electrónicos"
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ La matrícula ya existe.")

    # --- CASO 3: FORMULARIO LATERAL DE NUEVA CITA ---
    elif st.session_state.sub_vista_lateral == "nueva_cita":
        st.markdown("### 📅 Nueva Agenda (Cita)")
        st.caption("Registre la cita del alumno en esta ventana lateral.")
        
        if st.button("<< Volver al Menú", use_container_width=True):
            st.session_state.sub_vista_lateral = "navegacion"
            st.rerun()
            
        st.markdown("---")
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, matricula FROM expedientes ORDER BY nombre ASC")
        alumnos_db = cursor.fetchall()
        conn.close()
        
        if not alumnos_db:
            st.warning("⚠️ No hay expedientes registrados.")
        else:
            opciones_alumnos = {f"{a[1]} ({a[2]})": a[0] for a in alumnos_db}
            alumno_asignado = st.selectbox("Seleccionar Alumno:", list(opciones_alumnos.keys()))
            
            f_elegida = st.date_input("Fecha de Consulta:", value=datetime.today())
            h_elegida = st.time_input("Hora de Consulta:", value=datetime.now().time())
            mot_cita_new = st.text_area("Motivo de la Sesión:")
            
            if st.button("Confirmar Cita Médica", use_container_width=True, type="primary"):
                timestamp_str = f"{f_elegida} {h_elegida.strftime('%H:%M:%S')}"
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO citas (expediente_id, fecha_hora, estado, motivo) VALUES (?, ?, 'Pendiente', ?)",
                               (opciones_alumnos[alumno_asignado], timestamp_str, mot_cita_new.strip()))
                conn.commit()
                conn.close()
                st.success("✅ ¡Cita Agendada!")
                st.session_state.sub_vista_lateral = "navegacion"
                st.session_state.menu_actual = "🏠 Inicio y Planner"
                st.rerun()

# Carga global de datos para la pantalla principal y calendario
conn = conectar_db()
df_todas_citas = pd.read_sql_query("""
    SELECT c.id as [ID Cita], e.nombre as [Paciente], e.matricula as [Matrícula], 
           c.fecha_hora as [Fecha y Hora], c.estado as [Estado], c.motivo as [Motivo], 
           c.notas_evolucion as [Notas de Evolución]
    FROM citas c JOIN expedientes e ON c.expediente_id = e.id
    ORDER BY c.fecha_hora ASC
""", conn)
conn.close()

if not df_todas_citas.empty:
    df_todas_citas['datetime_obj'] = pd.to_datetime(df_todas_citas['Fecha y Hora'])
    df_todas_citas['fecha_solo'] = df_todas_citas['datetime_obj'].dt.date
    df_todas_citas['hora_solo'] = df_todas_citas['datetime_obj'].dt.strftime('%H:%M')

# ==============================================================================
# MÓDULO 1: INICIO Y PLANNER (DISEÑO LIMPIO ORIGINAL RESTAURADO COMPLETAMENTE)
# ==============================================================================
if st.session_state.menu_actual == "🏠 Inicio y Planner":
    st.title("🏫 Consultorio Psicológico DACYTI")
    st.subheader("Panel General de Control Clínico")
    
    st.markdown("---")
    
    # Botones superiores que abren las ventanas de costado (estilo Notion)
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    with col_btn1:
        if st.button("📝 Abrir Nuevo Expediente", use_container_width=True):
            st.session_state.sub_vista_lateral = "nuevo_expediente"
            st.rerun()
    with col_btn2:
        if st.button("📅 Nueva Agenda (Cita)", use_container_width=True):
            st.session_state.sub_vista_lateral = "nueva_cita"
            st.rerun()

    # Sección de Citas Programadas
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📄 Citas Programadas")
    
    if df_todas_citas.empty:
        st.info("No se encuentran registros de citas programadas en la base de datos.")
    else:
        df_pendientes = df_todas_citas[df_todas_citas['Estado'] == 'Pendiente'].head(5)
        if df_pendientes.empty:
            st.info("No hay citas pendientes prioritarias en la agenda.")
        else:
            st.dataframe(
                df_pendientes[['Paciente', 'Fecha y Hora', 'Estado', 'Motivo']], 
                use_container_width=True
            )

    # Visualizador de Calendario Clínico abajo
    st.markdown("---")
    st.subheader("🗓️ Visualizador de Calendario Clínico")
    
    col_view1, col_view2 = st.columns([2, 3])
    with col_view1:
        rango_tiempo = st.selectbox("Formato Ajustado:", ["Diario", "Semanal", "Mensual (Carga General)", "Anual (Lista)"], index=2, key="cal_rango_view")
    with col_view2:
        st.session_state.fecha_navegacion_cal = st.date_input("Fecha Base Enfoque:", st.session_state.fecha_navegacion_cal, key="cal_fecha_enfoque")
        
    color_status = {"Pendiente": "#2e5bff", "Completada": "#2ecc71", "Cancelada": "#e74c3c"}
    
    if df_todas_citas.empty:
        st.info("Sin registros clínicos para segmentar en formato calendario.")
    else:
        # --- FORMATO DIARIO ---
        if rango_tiempo == "Diario":
            st.markdown(f"#### 🎯 Citas del Día: {st.session_state.fecha_navegacion_cal.strftime('%d/%m/%Y')}")
            df_dia = df_todas_citas[df_todas_citas['fecha_solo'] == st.session_state.fecha_navegacion_cal].sort_values(by='hora_solo')
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
                    df_sem_dia = df_todas_citas[df_todas_citas['fecha_solo'] == dia_eval]
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
                            df_mes_dia = df_todas_citas[df_todas_citas['fecha_solo'] == celda_fecha]
                            for _, row in df_mes_dia.iterrows():
                                bg = color_status.get(row['Estado'], '#718096')
                                st.markdown(f"<div class='cal-event-card' style='background-color:{bg}; padding:2px 4px; font-size:10px;'>{row['hora_solo']} - {row['Paciente'][:8]}</div>", unsafe_allow_html=True)

        # --- FORMATO ANUAL ---
        elif rango_tiempo == "Anual (Lista)":
            target_year = st.session_state.fecha_navegacion_cal.year
            st.markdown(f"#### 📋 Agenda Completa Cronológica - Año {target_year}")
            df_anio = df_todas_citas[df_todas_citas['datetime_obj'].dt.year == target_year].sort_values(by='datetime_obj')
            if df_anio.empty:
                st.caption("No existen registros de citas para este año.")
            else:
                st.dataframe(df_anio.drop(columns=['datetime_obj', 'fecha_solo', 'hora_solo']), use_container_width=True)

# ==============================================================================
# MÓDULO 2: EXPEDIENTES ELECTRÓNICOS (CON CONTADOR DE EXPEDIENTES TOTALES)
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
    
    total_exp = len(df_expedientes)
    st.metric(label="🗂️ Total de Expedientes Abiertos", value=int(total_exp))
    st.markdown("---")
    
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
# MÓDULO 3: AGENDA DE CITAS (CON CONTADORES DE SESIONES PENDIENTES Y CONCLUIDAS)
# ==============================================================================
elif st.session_state.menu_actual == "📅 Agenda de Citas":
    st.title("📅 Agenda de Citas")
    st.subheader("Control de Citas Clínicas e Historial de Sesiones")
    
    if not df_todas_citas.empty:
        citas_pen = len(df_todas_citas[df_todas_citas['Estado'] == 'Pendiente'])
        citas_com = len(df_todas_citas[df_todas_citas['Estado'] == 'Completada'])
    else:
        citas_pen, citas_com = 0, 0
        
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.metric(label="⏳ Sesiones Pendientes por Atender", value=int(citas_pen))
    with col_c2:
        st.metric(label="✅ Sesiones Concluidas / Exitosas", value=int(citas_com))
        
    st.markdown("---")
    
    if df_todas_citas.empty:
        st.info("No hay citas registradas en la agenda actualmente.")
    else:
        st.dataframe(df_todas_citas.drop(columns=['datetime_obj', 'fecha_solo', 'hora_solo'], errors='ignore'), use_container_width=True)
        
        # Panel de actualización rápida de estatus clínico e historial clínico
        st.markdown("---")
        st.subheader("⚙️ Actualización Rápida de Historial Clínico")
        
        mapeo_edicion = {f"Cita ID {r['ID Cita']} - Paciente: {r['Paciente']} ({r['Fecha y Hora']})": r['ID Cita'] for _, r in df_todas_citas.iterrows()}
        seleccion_c = st.selectbox("Seleccione la consulta a modificar:", list(mapeo_edicion.keys()), key="select_edicion_cita")
        
        id_c_sel = mapeo_edicion[seleccion_c]
        info_actual_cita = df_todas_citas[df_todas_citas['ID Cita'] == id_c_sel].iloc[0]
        
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