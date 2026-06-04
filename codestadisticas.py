# =================================================================
#                     MÓDULO DE ESTADÍSTICAS: codestadisticas.py
# =================================================================
import pandas as pd
import streamlit as st
from codconexion import conectar_db

def obtener_dataframe(query, params=None):
    """Helper para transformar consultas SQL directas en DataFrames de Pandas de bajo peso."""
    conn = conectar_db()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Error procesando analíticas: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def renderizar_reportes_direccion():
    st.markdown("### 📊 Panel de Control e Informe de Dirección")
    
    # 1. KPIs Rápidos
    df_citas = obtener_dataframe("SELECT estado FROM citas")
    df_exp = obtener_dataframe("SELECT genero, carrera FROM expedientes")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Expedientes Totales", len(df_exp))
    col2.metric("Citas Agendadas", len(df_citas))
    col3.metric("Consultas Completadas", len(df_citas[df_citas['estado'] == 'Completada']) if not df_citas.empty else 0)
    
    st.write("---")
    
    # 2. Distribución de Género (Gráfico de Pastel)
    st.subheader("💡 Demografía por Género")
    if not df_exp.empty and 'genero' in df_exp.columns:
        conteo_genero = df_exp['genero'].value_counts()
        st.pie_chart = st.dataframe(conteo_genero) # Vista minimalista de datos
        
        # Gráfico visual ligero
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 3))
        fig.patch.set_facecolor('#0e1117') # Match tema oscuro de Streamlit
        ax.set_facecolor('#0e1117')
        
        colors = ['#FF9F43', '#00D1B2', '#4B4B4B']
        ax.pie(conteo_genero.values, labels=conteo_genero.index, autopct='%1.1f%%', startangle=90, textprops={'color':"w"}, colors=colors[:len(conteo_genero)])
        ax.axis('equal')
        st.pyplot(fig)
    else:
        st.info("Sin datos demográficos suficientes.")

    # 3. Distribución por Carrera de la DACYTI
    st.subheader("🏫 Casos de Atención por Carrera")
    if not df_exp.empty and 'carrera' in df_exp.columns:
        conteo_carrera = df_exp['carrera'].value_counts()
        st.bar_chart(conteo_carrera)
