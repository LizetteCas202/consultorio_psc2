# =================================================================
#                     MÓDULO DE AUTENTICACIÓN: codauth.py
# =================================================================
import bcrypt
from codconexion import conectar_db

def verificar_credenciales(usuario, clave_ingresada):
    """Verifica las credenciales del usuario usando el formato ? de SQLite."""
    conn = conectar_db()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT clave_hash FROM usuarios WHERE usuario = ?", (usuario,))
        resultado = cursor.fetchone()
        if resultado:
            clave_hash_almacenada = resultado[0].encode('utf-8')
            return bcrypt.checkpw(clave_ingresada.encode('utf-8'), clave_hash_almacenada)
        return False
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def registrar_usuario(usuario, clave_simple, rol, pregunta_secreta, respuesta_secreta_simple):
    """Registra un nuevo psicólogo en el consultorio."""
    conn = conectar_db()
    if not conn:
        return False, "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT usuario FROM usuarios WHERE usuario = ?", (usuario,))
        if cursor.fetchone():
            return False, "El usuario ya existe."
            
        salt = bcrypt.gensalt(rounds=12)
        clave_hashed = bcrypt.hashpw(clave_simple.encode('utf-8'), salt).decode('utf-8')
        respuesta_hashed = bcrypt.hashpw(respuesta_secreta_simple.encode('utf-8'), salt).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO usuarios (usuario, clave_hash, rol, pregunta_secreta, respuesta_secreta_hash) 
            VALUES (?, ?, ?, ?, ?);
        """, (usuario, clave_hashed, rol, pregunta_secreta, respuesta_hashed))
        conn.commit()
        return True, "Usuario creado exitosamente."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        if conn:
            conn.close()

def recuperar_clave_por_pregunta(usuario, respuesta_ingresada, nueva_clave):
    """Permite el restablecimiento de contraseñas con sintaxis de SQLite."""
    conn = conectar_db()
    if not conn:
        return False, "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT respuesta_secreta_hash FROM usuarios WHERE usuario = ?", (usuario,))
        resultado = cursor.fetchone()
        if resultado:
            resp_hash_almacenada = resultado[0].encode('utf-8')
            if bcrypt.checkpw(respuesta_ingresada.encode('utf-8'), resp_hash_almacenada):
                salt = bcrypt.gensalt(rounds=12)
                nueva_clave_hashed = bcrypt.hashpw(nueva_clave.encode('utf-8'), salt).decode('utf-8')
                cursor.execute("UPDATE usuarios SET clave_hash = ? WHERE usuario = ?", (nueva_clave_hashed, usuario))
                conn.commit()
                return True, "Contraseña actualizada con éxito."
            return False, "La respuesta secreta es incorrecta."
        return False, "El usuario no existe."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        if conn:
            conn.close()

def inicializar_usuario_admin():
    """Garantiza el usuario inicial de prueba corregido."""
    conn = conectar_db()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            salt = bcrypt.gensalt(rounds=12)
            c_hash = bcrypt.hashpw("admin123".encode('utf-8'), salt).decode('utf-8')
            r_hash = bcrypt.hashpw("Chontalpa".encode('utf-8'), salt).decode('utf-8')
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave_hash, rol, pregunta_secreta, respuesta_secreta_hash)
                VALUES ('psicologa.sara', ?, 'Director/Psicólogo', '¿Unidad de origen?', ?)
            """, (c_hash, r_hash))
            conn.commit()
    except Exception:
        pass
    finally:
        if conn: conn.close()
        