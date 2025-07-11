from flask import Flask, render_template, request, redirect, url_for, Response
from flask_cors import CORS
import pyodbc
import json  


app = Flask(__name__)
app.secret_key = 'clave-secreta-super-segura'
CORS(app)

# 🔌 Conexión con SQL Server
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=BibliotecaDB;"
    "Trusted_Connection=yes;"
)

@app.route('/')
def inicio():
    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')

        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Verifica si existe el encargado con ese correo y contraseña
            cursor.execute("""
                SELECT * FROM Encargados 
                WHERE CorreoElectronico = ? AND ContrasenaHash = ?
            """, (correo, contrasena))

            encargado = cursor.fetchone()
            conn.close()

            if encargado:
                return redirect(url_for('dashboard'))  # ✅ Éxito: ir a dashboard
            else:
                return render_template('login.html', error='Credenciales incorrectas')
        except Exception as e:
            return render_template('login.html', error=f"Error: {str(e)}")
    
    # Si es GET, solo mostrar el formulario
    return render_template('login.html')





@app.route('/dashboard')
def dashboard():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Obtener libros
        cursor.execute("SELECT * FROM Libros")
        libros = cursor.fetchall()

        # Obtener préstamos
        cursor.execute("""
            SELECT 
                p.PrestamoID,
                u.DNI AS UsuarioDNI,
                l.Titulo AS LibroTitulo,
                e.Nombre AS EncargadoNombre,
                p.FechaPrestamo,
                p.FechaDevolucionEsperada,
                p.FechaDevolucionReal,
                p.EstadoPrestamo
            FROM Prestamos p
            JOIN Usuarios u ON p.UsuarioID = u.UsuarioID
            JOIN Libros l ON p.LibroID = l.LibroID
            JOIN Encargados e ON p.EncargadoID = e.EncargadoID
            ORDER BY p.PrestamoID DESC
        """)
        prestamos = cursor.fetchall()

        conn.close()

        return render_template("dashboard.html", libros=libros, prestamos=prestamos)

    except Exception as e:
        print("❌ Error al cargar dashboard:", str(e))
        return render_template("dashboard.html", error=f"Error al cargar dashboard: {str(e)}")













def ejecutar_consulta(query):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(query)
        columnas = [column[0] for column in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        conn.close()
        return Response(
            json.dumps(resultados, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

# Endpoints API
@app.route('/libros')
def obtener_libros():
    return ejecutar_consulta("""
        SELECT L.LibroID, L.Titulo, L.ISBN, G.NombreGenero, 
               L.CantidadTotal, L.CantidadDisponible
        FROM Libros L
        LEFT JOIN Generos G ON L.GeneroID = G.GeneroID
    """)

@app.route('/generos')
def obtener_generos():
    return ejecutar_consulta("SELECT * FROM Generos")

@app.route('/usuarios')
def obtener_usuarios():
    return ejecutar_consulta("SELECT * FROM Usuarios")

@app.route('/prestamos')
def obtener_prestamos():
    return ejecutar_consulta("""
        SELECT P.PrestamoID, U.DNI AS UsuarioDNI, L.Titulo AS LibroTitulo, 
               E.Nombre AS EncargadoNombre, P.FechaPrestamo, 
               P.FechaDevolucionEsperada, P.FechaDevolucionReal, P.EstadoPrestamo
        FROM Prestamos P
        JOIN Usuarios U ON P.UsuarioID = U.UsuarioID
        JOIN Libros L ON P.LibroID = L.LibroID
        JOIN Encargados E ON P.EncargadoID = E.EncargadoID
    """)

@app.route('/encargados')
def obtener_encargados():
    return ejecutar_consulta("""
        SELECT EncargadoID, CorreoElectronico, Nombre, Apellidos
        FROM Encargados
    """)


from datetime import datetime

@app.route('/registrar-prestamo', methods=['POST'])
def registrar_prestamo():
    usuario_dni = request.form.get('usuario_dni')
    libro_id = request.form.get('libro_id')
    fecha_devolucion = request.form.get('fecha_devolucion')

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # 🔍 Verificar si el usuario ya existe
        cursor.execute("SELECT UsuarioID FROM Usuarios WHERE DNI = ?", usuario_dni)
        usuario = cursor.fetchone()

        if not usuario:
            # 🆕 Insertar nuevo usuario automáticamente
            cursor.execute("INSERT INTO Usuarios (DNI) VALUES (?)", usuario_dni)
            conn.commit()
            cursor.execute("SELECT UsuarioID FROM Usuarios WHERE DNI = ?", usuario_dni)
            usuario = cursor.fetchone()

        usuario_id = usuario[0]

        # 📘 Verificar disponibilidad del libro
        cursor.execute("SELECT CantidadDisponible FROM Libros WHERE LibroID = ?", libro_id)
        libro = cursor.fetchone()
        if not libro or libro[0] < 1:
            conn.close()
            return redirect(url_for('dashboard'))  # No hay libros disponibles

        # 👤 Obtener encargado (solo uno provisionalmente)
        cursor.execute("SELECT TOP 1 EncargadoID FROM Encargados")
        encargado = cursor.fetchone()
        if not encargado:
            conn.close()
            return redirect(url_for('dashboard'))  # No hay encargado registrado
        encargado_id = encargado[0]

        # 📝 Insertar el préstamo
        fecha_prestamo = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO Prestamos (UsuarioID, LibroID, EncargadoID, FechaPrestamo, FechaDevolucionEsperada, EstadoPrestamo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, libro_id, encargado_id, fecha_prestamo, fecha_devolucion, 'Prestado'))

        # 📉 Descontar un libro disponible
        cursor.execute("""
            UPDATE Libros SET CantidadDisponible = CantidadDisponible - 1 WHERE LibroID = ?
        """, (libro_id,))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    except Exception as e:
        return render_template('dashboard.html', error=f"Error al registrar préstamo: {str(e)}")







from datetime import datetime

@app.route('/devolver-prestamo', methods=['POST'])
def devolver_prestamo():
    prestamo_id = request.form.get('prestamo_id')

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Obtener datos del préstamo
        cursor.execute("SELECT LibroID FROM Prestamos WHERE PrestamoID = ?", prestamo_id)
        prestamo = cursor.fetchone()

        if not prestamo:
            conn.close()
            return redirect(url_for('dashboard'))  # No existe préstamo

        libro_id = prestamo[0]
        fecha_devolucion = datetime.now().strftime("%Y-%m-%d")

        # Actualizar el préstamo como devuelto
        cursor.execute("""
            UPDATE Prestamos
            SET FechaDevolucionReal = ?, EstadoPrestamo = 'Devuelto'
            WHERE PrestamoID = ?
        """, (fecha_devolucion, prestamo_id))

        # Incrementar la cantidad de libros disponibles
        cursor.execute("""
            UPDATE Libros
            SET CantidadDisponible = CantidadDisponible + 1
            WHERE LibroID = ?
        """, (libro_id,))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    except Exception as e:
        return render_template('dashboard.html', error=f"Error al devolver: {str(e)}")







@app.route('/registrar-libro', methods=['POST'])
def registrar_libro():
    titulo = request.form.get('titulo')
    isbn = request.form.get('isbn')  # Nuevo campo
    genero_id = request.form.get('genero_id')
    cantidad = request.form.get('cantidad')

    try:
        print("🟡 Datos recibidos:", titulo, isbn, genero_id, cantidad)
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Libros (Titulo, ISBN, GeneroID, CantidadDisponible, CantidadTotal)
            VALUES (?, ?, ?, ?, ?)
        """, (titulo, isbn, genero_id, cantidad, cantidad))
        conn.commit()
        conn.close()
        print("✅ Libro registrado correctamente")
        return redirect(url_for('dashboard'))
    except Exception as e:
        print("❌ ERROR al registrar libro:", str(e))
        return render_template("dashboard.html", error=f"Error al registrar libro: {str(e)}")


from flask import session, redirect, url_for

@app.route('/logout', methods=['GET'])  
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)


