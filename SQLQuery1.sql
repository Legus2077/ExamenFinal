
USE BibliotecaDB; 




-- 1. Tabla Encargados
-- Para el login del personal de la biblioteca
CREATE TABLE Encargados (
    EncargadoID INT PRIMARY KEY IDENTITY(1,1),
    CorreoElectronico NVARCHAR(255) UNIQUE NOT NULL,
    ContrasenaHash NVARCHAR(255) NOT NULL,
    Nombre NVARCHAR(100),
    Apellidos NVARCHAR(100)
);

-- 2. Tabla Usuarios (o Lectores) - Simplificada con solo DNI
-- Para registrar a los lectores que realizan un préstamo
CREATE TABLE Usuarios (
    UsuarioID INT PRIMARY KEY IDENTITY(1,1),
    DNI NVARCHAR(20) UNIQUE NOT NULL
);

-- 3. Tabla Autores (No se mantiene genera errores, se retira autores del codigo)
/*CREATE TABLE Autores (
    AutorID INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(100) NOT NULL,
    Apellidos NVARCHAR(100)
);*/

-- 4. Tabla Generos
-- Para clasificar los libros por género 
CREATE TABLE Generos (
    GeneroID INT PRIMARY KEY IDENTITY(1,1),
    NombreGenero NVARCHAR(100) UNIQUE NOT NULL
);

-- 5. Tabla Libros - ACTUALIZADA: Se quita AutorID 
CREATE TABLE Libros (
    LibroID INT PRIMARY KEY IDENTITY(1,1),
    Titulo NVARCHAR(255) NOT NULL,
    ISBN NVARCHAR(20) UNIQUE,
    AnioPublicacion INT,
    Paginas INT,
    
    GeneroID INT, 
    CantidadTotal INT NOT NULL,
    CantidadDisponible INT NOT NULL,
    CONSTRAINT FK_Libros_Generos FOREIGN KEY (GeneroID) REFERENCES Generos(GeneroID)
);


-- 6. Tabla Prestamos 
CREATE TABLE Prestamos (
    PrestamoID INT PRIMARY KEY IDENTITY(1,1),
    LibroID INT NOT NULL,
    UsuarioID INT NOT NULL,
    EncargadoID INT NOT NULL,
    FechaPrestamo DATE NOT NULL,
    FechaDevolucionEsperada DATE NOT NULL,
    FechaDevolucionReal DATE,
    EstadoPrestamo NVARCHAR(50) NOT NULL,
    CONSTRAINT FK_Prestamos_Libros FOREIGN KEY (LibroID) REFERENCES Libros(LibroID),
    CONSTRAINT FK_Prestamos_Usuarios FOREIGN KEY (UsuarioID) REFERENCES Usuarios(UsuarioID),
    CONSTRAINT FK_Prestamos_Encargados FOREIGN KEY (EncargadoID) REFERENCES Encargados(EncargadoID)
);

-- --- Datos de Prueba ---
-- 1. Insertar un Encargado (iniciar sesión)
INSERT INTO Encargados (CorreoElectronico, ContrasenaHash, Nombre, Apellidos)
VALUES ('admin@biblioteca.com', 'password_hash_ejemplo', 'Leonardo', 'Condori');

-- 2. Insertar algunos Géneros (tabla Generos)
INSERT INTO Generos (NombreGenero) VALUES ('Realismo Magico');
INSERT INTO Generos (NombreGenero) VALUES ('Clasicos');
INSERT INTO Generos (NombreGenero) VALUES ('Distopia');
INSERT INTO Generos (NombreGenero) VALUES ('Fantasia');
INSERT INTO Generos (NombreGenero) VALUES ('Videojuegos'); -- Añadido para el ejemplo de Fortnite

-- 3. Insertar algunos Libros (ACTUALIZADO: sin AutorID)
-- Si los IDs de Géneros son 1, 2, 3, 4, 5 respectivamente:
INSERT INTO Libros (Titulo, ISBN, GeneroID, CantidadTotal, CantidadDisponible)
VALUES ('Cien años de soledad', '9780307474728', 1, 5, 5); -- GeneroID 1 es Realismo Mágico
INSERT INTO Libros (Titulo, ISBN, GeneroID, CantidadTotal, CantidadDisponible)
VALUES ('Orgullo y prejuicio', '9780141439518', 2, 3, 3); -- GeneroID 2 es Clásicos
INSERT INTO Libros (Titulo, ISBN, GeneroID, CantidadTotal, CantidadDisponible)
VALUES ('1984', '9780451524935', 3, 4, 4); -- GeneroID 3 es Distopía
INSERT INTO Libros (Titulo, ISBN, GeneroID, CantidadTotal, CantidadDisponible)
VALUES ('Fortnite - La Guía Definitiva', '9781234567890', 5, 2, 2); -- GeneroID 5 es Videojuegos




--pruebas ....
UPDATE Encargados
SET CorreoElectronico = 'admin@biblioteca.com', ContrasenaHash = 'admin123'
WHERE EncargadoID = 1;

SELECT * FROM Prestamos ORDER BY PrestamoID DESC;

SELECT * FROM Generos;

SELECT * FROM Libros;

DELETE FROM Libros WHERE ISBN IS NULL;

