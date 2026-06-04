=================================================================
#           MÓDULO DE CONEXIÓN OPTIMIZADO (SQLITE): codconexion.py
# =================================================================
import sqlite3
import streamlit as st

def conectar_db():
    """Establece y devuelve una conexión a la base de datos SQLite local en el servidor."""
    try:
        conn = sqlite3.connect("consultorio.db", check_same_thread=False)
        return conn
    except Exception as e:
        st.error(f"Error de Conexión: {e}")
        return None

def crear_tablas_iniciales():
    """Crea todas las tablas necesarias en SQLite para el consultorio de la UJAT."""
    conn = conectar_db()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        
        # 1. Tabla de Usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                clave_hash TEXT NOT NULL,
                rol TEXT DEFAULT 'psicologo',
                pregunta_secreta TEXT NOT NULL,
                respuesta_secreta_hash TEXT NOT NULL
            );
        """)
        
        # 2. Tabla de Expedientes (Alumnos DACYTI)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expedientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                genero TEXT NOT NULL,
                carrera TEXT NOT NULL,
                semestre TEXT NOT NULL,
                telefono TEXT,
                correo TEXT,
                observaciones TEXT,
                ocupacion TEXT DEFAULT '',
                etiquetas TEXT DEFAULT ''
            );
        """)
        
        # 3. Tabla de Citas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expediente_id INTEGER,
                fecha_hora TEXT NOT NULL,
                estado TEXT DEFAULT 'Pendiente',
                motivo TEXT,
                FOREIGN KEY (expediente_id) REFERENCES expedientes(id) ON DELETE CASCADE
            );
        """)
        
        # 4. Tabla de Notas de Consulta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas_consulta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cita_id INTEGER,
                expediente_id INTEGER,
                fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                vivencias_clave TEXT,
                notas_evolucion TEXT,
                medicamento_psiquiatrico TEXT,
                FOREIGN KEY (cita_id) REFERENCES citas(id) ON DELETE CASCADE,
                FOREIGN KEY (expediente_id) REFERENCES expedientes(id) ON DELETE CASCADE
            );
        """)
        
        conn.commit()
    except Exception as e:
        st.error(f"Error al estructurar las tablas: {e}")
    finally:
        if conn:
            conn.close()