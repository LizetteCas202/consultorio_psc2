# =================================================================
#                     MÓDULO DE CONEXIÓN: codconexion.py
# =================================================================
import psycopg2
from psycopg2 import Error
import streamlit as st

# Configuración de base de datos (Usa variables de entorno en producción/despliegue)
DB_HOST = st.secrets.get("DB_HOST", "localhost")
DB_NAME = st.secrets.get("DB_NAME", "consultorio_db")
DB_USER = st.secrets.get("DB_USER", "postgres")
DB_PASS = st.secrets.get("DB_PASS", "12345")
DB_PORT = st.secrets.get("DB_PORT", "5432")

def conectar_db():
    """Establece y devuelve una conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Error as e:
        st.error(f"Error de Conexión a la BD: No se pudo conectar a PostgreSQL. Detalle: {e}")
        return None

def crear_tablas_iniciales():
    """Crea todas las tablas necesarias si no existen conforme al esquema del PDF."""
    conn = conectar_db()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        
        # 1. Tabla de Usuarios (Psicólogos/Administradores)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE NOT NULL,
                clave_hash VARCHAR(255) NOT NULL,
                rol VARCHAR(20) DEFAULT 'psicologo',
                pregunta_secreta VARCHAR(255) NOT NULL,
                respuesta_secreta_hash VARCHAR(255) NOT NULL
            );
        """)
        
        # 2. Tabla de Expedientes (Estudiantes de la UJAT con estilo Notion)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expedientes (
                id SERIAL PRIMARY KEY,
                matricula VARCHAR(20) UNIQUE NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                genero VARCHAR(20) NOT NULL,
                carrera VARCHAR(100) NOT NULL,
                semestre VARCHAR(20) NOT NULL,
                telefono VARCHAR(20),
                correo VARCHAR(100),
                observaciones TEXT,
                ocupacion VARCHAR(100) DEFAULT '',
                etiquetas TEXT DEFAULT '' -- Para emular las etiquetas dinámicas de Notion (separadas por comas)
            );
        """)
        
        # 3. Tabla de Citas (Agenda cronológica)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id SERIAL PRIMARY KEY,
                expediente_id INT REFERENCES expedientes(id) ON DELETE CASCADE,
                fecha_hora TIMESTAMP NOT NULL,
                estado VARCHAR(20) DEFAULT 'Pendiente', -- 'Pendiente', 'Completada', 'Cancelada'
                motivo TEXT
            );
        """)
        
        # 4. Tabla de Notas de Consulta (Datos clínicos del paciente)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas_consulta (
                id SERIAL PRIMARY KEY,
                cita_id INT REFERENCES citas(id) ON DELETE CASCADE,
                expediente_id INT REFERENCES expedientes(id) ON DELETE CASCADE,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vivencias_clave TEXT,
                notas_evolucion TEXT,
                medicamento_psiquiatrico TEXT
            );
        """)
        
        conn.commit()
    except Error as e:
        st.error(f"Error al estructurar las tablas iniciales: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
