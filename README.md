# 🗂️ Organy - Gestor de Rutas & Proyectos TUI

**Organy** es una potente interfaz de terminal (TUI) desarrollada en Python utilizando la librería **Textual**. Está diseñada para centralizar, organizar y abrir rápidamente tus directorios de desarrollo, permitiendo agruparlos bajo proyectos conceptuales (por ejemplo, Frontend, Backend, AI Services) y abrirlos de forma nativa con un solo clic o atajo de teclado en **OpenCode**, **VS Code** o en el **Explorador de Archivos de Windows**.

---

## 🚀 Características Principales

*   **🔍 Buscador en Tiempo Real**: Filtra instantáneamente tus decenas de rutas guardadas por nombre o path a medida que escribes en la caja de búsqueda.
*   **📁 Árbol de Proyectos Agrupados (`Tree`)**: Organiza tus directorios de desarrollo jerárquicamente en proyectos contenedores (ej. "Proyecto X" -> Frontend, Backend).
*   **🛠️ Lanzadores Rápidos Integrados**:
    *   **Abrir OpenCode [O]**: Abre una pestaña nueva en Windows Terminal (`wt.exe`) ejecutando `opencode .` directamente en el directorio de trabajo (con fallback a CMD si es necesario).
    *   **Abrir VS Code [V]**: Lanza Visual Studio Code (`code .`) en el directorio seleccionado de inmediato.
    *   **Abrir Carpeta [E]**: Abre el explorador de archivos nativo de Windows directamente en la ruta del proyecto.
*   **🔄 Pestaña de Últimos Accesos (Top 5)**: Monitorea tus últimos 5 proyectos más visitados mostrando los días, horas o minutos exactos transcurridos desde tu última interacción.
*   **💾 Persistencia con SQLite**: Almacenamiento seguro, rápido y ligero en una base de datos local (`database.db`).
*   **🛡️ Integridad de Datos**: Eliminar proyectos contenedores **nunca borra tus rutas**; simplemente las desvincula y las deja como "Rutas Independientes/Libres" de forma automática.

---

## 🛠️ Requisitos e Instalación

### Requisitos

*   **Python 3.10** o superior.
*   **Windows 11** (Soporta pestañas de terminal con `wt.exe`).

### Instalación rápida con `uv` (Recomendado)

Si utilizas el gestor de paquetes ultra-rápido `uv`, solo debes agregar la dependencia e iniciar el proyecto:

```bash
# Agregar la librería Textual
uv add textual

# Ejecutar el gestor
python main.py
```

### Instalación estándar con `pip`

```bash
pip install -r requirements.txt
# O bien directamente:
pip install textual

python main.py
```

---

## ⌨️ Atajos de Teclado (Atajos Globales)

El gestor está pensado para maximizar la productividad y permite el uso de atajos en cualquier momento:

| Tecla | Acción |
| :--- | :--- |
| `Q` | **Salir** de la aplicación |
| `O` | **Abrir OpenCode** en el directorio de la ruta seleccionada |
| `V` | **Abrir VS Code** en el directorio de la ruta seleccionada |
| `E` | **Abrir Carpeta** en el explorador de archivos nativo |
| `D` | **Eliminar** la ruta seleccionada |

---

## 📂 Arquitectura de Archivos

El proyecto consta de una estructura minimalista y de alta cohesión:

*   **`main.py`**: Contiene toda la lógica de la interfaz TUI (Textual), estilos CSS embebidos, filtros de búsqueda, vistas de árbol y despachadores de subprocesos del sistema.
*   **`db.py`**: Capa de persistencia que interactúa con SQLite. Maneja la creación automática de tablas, migraciones seguras (alteración de columnas sin pérdida de datos) y funciones CRUD para rutas y agrupaciones.
*   **`database.db`**: Base de datos SQLite local autogenerada.

---

## 📊 Modelo de Datos (Base de Datos)

La base de datos se genera de forma automática al iniciar la aplicación con la siguiente estructura segura:

```sql
-- Tabla de proyectos contenedores
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

-- Tabla de rutas con relación opcional a proyectos
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY,
    name TEXT,
    route TEXT,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL
);
```

---

## 🌟 Guía de Uso del Sistema

1.  **Registrar nuevas rutas**: Ve a la pestaña **"Registrar Nueva Ruta"**, escribe un nombre amigable y pega la ruta absoluta de tu directorio.
2.  **Buscar y lanzar**: En la pestaña **"Seleccionar Rutas"**, escribe en la barra de búsqueda para filtrar al instante. Selecciona una fila con las flechas de tu teclado y presiona `O`, `V` o `E` para abrir tu entorno preferido.
3.  **Agrupar Proyectos**: Ve a la pestaña **"Proyectos Agrupados"**:
    *   Crea un proyecto contenedor (ej. `Proyecto Organy`).
    *   Selecciona tu ruta y tu proyecto en los selectores desplegables y presiona **"Asociar a Proyecto"**.
    *   Ahora la verás organizada dentro de la estructura de árbol colapsable.
4.  **Monitorear**: Revisa la pestaña **"Últimos Accesos (Top 5)"** para ver qué proyectos estás descuidando o cuáles has modificado hoy mismo.
