# =================================================================
#                     MÓDULO DE ESTADÍSTICAS: codestadisticas.py
# =================================================================
import pandas as pd
import streamlit as st
import sqlite3

def obtener_dataframe(query, params=None):
    """Genera un DataFrame limpio desde SQLite."""
    try:
        conn = sqlite3.connect("consultorio.db")
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error analítico: {e}")
        return pd.DataFrame()

def renderizar_reportes_direccion():
    st.markdown("### 📊 Panel de Control e Informe de Dirección")
    
    df_citas = obtener_dataframe("SELECT estado FROM citas")
    df_exp = obtener_dataframe("SELECT genero, carrera FROM expedientes")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Expedientes Totales", len(df_exp))
    col2.metric("Citas Agendadas", len(df_citas))
    col3.metric("Consultas Completadas", len(df_citas[df_citas['estado'] == 'Completada']) if not df_citas.empty else 0)
    
    st.write("---")
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("💡 Demografía por Género")
        if not df_exp.empty and 'genero' in df_exp.columns:
            conteo_genero = df_exp['genero'].value_counts()
            st.dataframe(conteo_genero, use_container_width=True)
        else:
            st.info("Sin datos demográficos registrados.")

    with col_der:
        st.subheader("🏫 Casos por Carrera (DACYTI)")
        if not df_exp.empty and 'carrera' in df_exp.columns:
            conteo_carrera = df_exp['carrera'].value_counts()
            st.bar_chart(conteo_carrera)
        else:
            st.info("Sin datos de carreras registrados.")
