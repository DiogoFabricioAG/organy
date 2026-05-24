import os
import shutil
import subprocess
from datetime import datetime, timezone
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane, Input, Button, Label, DataTable, Static, Tree, Select

import db

def get_days_diff(last_accessed_str):
    if not last_accessed_str:
        return "Nunca"
    try:
        dt = datetime.strptime(last_accessed_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        days = diff.days
        if days == 0:
            seconds = diff.total_seconds()
            if seconds < 60:
                return "Hace un momento"
            mins = int(seconds // 60)
            if mins < 60:
                return f"Hoy ({mins} min)"
            hours = int(seconds // 3600)
            return f"Hoy ({hours} h)"
        if days == 1:
            return "Ayer (1 día)"
        return f"Hace {days} días"
    except Exception:
        return "Nunca"

class TextApp(App):
    CSS = """
    Screen {
        background: #1a1a1a;
    }
    
    TabbedContent {
        background: #1e1e1e;
        border: solid #333333;
    }
    
    #actions-container {
        margin: 1 0;
        height: auto;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
        content-align: center middle;
    }
    
    .input-group {
        margin: 1 2;
    }
    
    .input-label {
        color: #888888;
        margin-bottom: 1;
    }
    
    #status-msg {
        margin: 1 2;
        color: #00ff00;
    }
    
    DataTable {
        height: 1fr;
        border: solid #444444;
    }
    
    #recent-list {
        border: solid #444444;
        background: #2a2a2a;
        padding: 1;
        margin: 1;
        height: auto;
    }
    
    #tree-column {
        width: 60%;
        height: 100%;
        border-right: solid #333333;
        padding-right: 1;
    }
    
    #project-management-column {
        width: 40%;
        padding-left: 2;
        height: 100%;
    }
    
    #projects-tree {
        height: 1fr;
        border: solid #444444;
        margin-bottom: 1;
    }
    
    #tree-actions-container {
        height: auto;
        align: center middle;
    }
    
    Select {
        margin: 1 0;
    }
    
    #search-input {
        margin-bottom: 1;
    }
    """

    TITLE = "Organy - Gestor de Rutas"
    BINDINGS = [
        ("q", "quit", "Salir"),
        ("o", "open_opencode", "Abrir OpenCode"),
        ("v", "open_vscode", "Abrir VS Code"),
        ("e", "open_explorer", "Abrir Carpeta"),
        ("d", "delete_selected", "Eliminar Ruta"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("Seleccionar Rutas", id="select_tab"):
                yield Label("[bold cyan]Selecciona una ruta de la tabla y elige una opción:[/bold cyan]")
                yield Input(placeholder="?? Buscar por nombre o ruta...", id="search-input")
                yield DataTable(id="routes-table")
                with Horizontal(id="actions-container"):
                    yield Button("Abrir OpenCode [O]", id="btn-opencode", variant="success")
                    yield Button("Abrir VS Code [V]", id="btn-vscode", variant="primary")
                    yield Button("Abrir Carpeta [E]", id="btn-explorer", variant="default")
                    yield Button("Eliminar [D]", id="btn-delete", variant="error")
                yield Label(id="selection-status")
                
            with TabPane("Proyectos Agrupados", id="grouped_tab"):
                yield Label("[bold green]Organiza y agrupa tus rutas en Proyectos (Frontend, Backend, etc):[/bold green]")
                with Horizontal():
                    with Vertical(id="tree-column"):
                        yield Tree("Mis Proyectos", id="projects-tree")
                        with Horizontal(id="tree-actions-container"):
                            yield Button("Abrir OpenCode [O]", id="btn-tree-opencode", variant="success")
                            yield Button("Abrir VS Code [V]", id="btn-tree-vscode", variant="primary")
                            yield Button("Abrir Carpeta [E]", id="btn-tree-explorer", variant="default")
                    with Vertical(id="project-management-column"):
                        yield Label("[bold yellow]Crear Proyecto Contenedor:[/bold yellow]")
                        yield Input(placeholder="Ej. Proyecto Alpha", id="input-project-name")
                        yield Button("Crear Proyecto", id="btn-create-project", variant="success")
                        
                        yield Label("[bold yellow]Asociar Ruta a Proyecto:[/bold yellow]")
                        yield Select([], id="select-route", prompt="Selecciona Ruta...")
                        yield Select([], id="select-project", prompt="Selecciona Proyecto...")
                        yield Button("Asociar a Proyecto", id="btn-assign-project", variant="primary")
                        
                        yield Label("[bold red]Eliminar Proyecto (Desagrupa rutas):[/bold red]")
                        yield Select([], id="select-delete-project", prompt="Selecciona Proyecto a eliminar...")
                        yield Button("Eliminar Proyecto", id="btn-delete-project", variant="error")
                yield Label(id="grouped-status")
                
            with TabPane("Registrar Nueva Ruta", id="create_tab"):
                with Vertical(classes="input-group"):
                    yield Label("Nombre del Proyecto:", classes="input-label")
                    yield Input(placeholder="Ej. Mi Proyecto", id="input-name")
                with Vertical(classes="input-group"):
                    yield Label("Ruta Absoluta del Directorio:", classes="input-label")
                    yield Input(placeholder="Ej. D:\\Proyectos2026\\mi-proyecto", id="input-path")
                yield Button("Registrar Ruta", id="btn-register", variant="success")
                yield Label(id="status-msg")
                
            with TabPane("Últimos Accesos (Top 5)", id="recent_tab"):
                yield Label("[bold yellow]Últimos 5 proyectos accedidos y días desde el último acceso:[/bold yellow]")
                yield Static(id="recent-list")
                
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#routes-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Nombre", "Ruta (Path)", "Último Acceso")
        
        # Expand tree root
        tree = self.query_one("#projects-tree", Tree)
        tree.root.expand()
        
        self.refresh_data()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.refresh_data(search_query=event.value)

    def refresh_data(self, search_query="") -> None:
        table = self.query_one("#routes-table", DataTable)
        table.clear()
        routes = db.get_routes()
        search_query = search_query.strip().lower()
        for route in routes:
            if search_query:
                if search_query not in route.name.lower() and search_query not in route.route.lower():
                     continue
            days_diff = get_days_diff(route.last_accessed)
            table.add_row(route.name, route.route, days_diff, key=route.name)
            
        # 2. Refresh Recent List
        recent_list = self.query_one("#recent-list", Static)
        recent_routes = db.get_recent_routes()
        
        if not recent_routes:
            recent_list.update("No hay rutas accedidas recientemente.")
        else:
            content = ""
            for i, route in enumerate(recent_routes, 1):
                days_diff = get_days_diff(route.last_accessed)
                content += f"[bold green]{i}. {route.name}[/bold green]\n"
                content += f"   Ruta: {route.route}\n"
                content += f"   Último acceso: {route.last_accessed if route.last_accessed else 'Nunca'}\n"
                content += f"   Días transcurridos: [bold yellow]{days_diff}[/bold yellow]\n\n"
            recent_list.update(content)
            
        # 3. Refresh Tree
        tree = self.query_one("#projects-tree", Tree)
        tree.clear()
        grouped, ungrouped = db.get_grouped_routes()
        
        for p_name, p_routes in grouped.items():
            p_node = tree.root.add(f"?? {p_name}", data={"type": "project", "name": p_name}, expand=True)
            for r in p_routes:
                p_node.add(f"?? {r.name}", data={"type": "route", "name": r.name, "route": r.route})
                
        if ungrouped:
            u_node = tree.root.add("?? Rutas Independientes (Libres)", data={"type": "unassigned_root"}, expand=True)
            for r in ungrouped:
                u_node.add(f"?? {r.name}", data={"type": "route", "name": r.name, "route": r.route})
                
        # 4. Refresh Select options
        projects = db.get_projects()
        options_routes = [(r.name, r.name) for r in routes]
        options_projects = [(p[1], p[1]) for p in projects]
        
        try:
            sel_route = self.query_one("#select-route", Select)
            sel_route.set_options(options_routes)
        except Exception:
            pass
            
        try:
            sel_project = self.query_one("#select-project", Select)
            sel_project.set_options(options_projects)
            
            sel_del_project = self.query_one("#select-delete-project", Select)
            sel_del_project.set_options(options_projects)
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node = event.node
        if node.data and node.data.get("type") in ("project", "unassigned_root"):
            node.toggle()

    def get_selected_route(self):
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active
        
        if active_tab == "select_tab":
            table = self.query_one("#routes-table", DataTable)
            row_index = table.cursor_row
            if row_index is not None and 0 <= row_index < table.row_count:
                row_data = table.get_row_at(row_index)
                if row_data:
                    return row_data[0], row_data[1]
        elif active_tab == "grouped_tab":
            tree = self.query_one("#projects-tree", Tree)
            node = tree.cursor_node
            if node and node.data and node.data.get("type") == "route":
                return node.data["name"], node.data["route"]
                
        return None, None

    def perform_action(self, action_type: str) -> None:
        name, route = self.get_selected_route()
        status_label = self.query_one("#selection-status", Label)
        tree_status_label = self.query_one("#grouped-status", Label)
        
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active
        lbl = tree_status_label if active_tab == "grouped_tab" else status_label
        
        if not name or not route:
            lbl.update("[red]Error: Selecciona una ruta (nodo final) primero.[/red]")
            return
            
        if not os.path.exists(route):
            lbl.update(f"[red]Error: La ruta '{route}' no existe en este equipo.[/red]")
            return
            
        db.update_last_accessed(name)
        self.refresh_data()
        
        try:
            if action_type == "opencode":
                wt_alias = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe")
                wt_path = wt_alias if os.path.exists(wt_alias) else (shutil.which("wt") or shutil.which("wt.exe"))
                
                if wt_path:
                    subprocess.Popen(f'"{wt_path}" -d "{route}" cmd /k "opencode ."', shell=True)
                    lbl.update(f"[green]Abriendo Opencode en nueva pestaña de Terminal para {name}...[/green]")
                else:
                    subprocess.Popen("start cmd /k \"opencode .\"", cwd=route, shell=True)
                    lbl.update(f"[green]Abriendo Opencode en {name} (CMD fallback)...[/green]")
            elif action_type == "vscode":
                subprocess.Popen("code .", cwd=route, shell=True)
                lbl.update(f"[green]Abriendo VS Code en {name}...[/green]")
            elif action_type == "explorer":
                os.startfile(route)
                lbl.update(f"[green]Abriendo Carpeta de {name}...[/green]")
        except Exception as e:
            lbl.update(f"[red]Error al abrir: {e}[/red]")

    def action_open_opencode(self) -> None:
        self.perform_action("opencode")

    def action_open_vscode(self) -> None:
        self.perform_action("vscode")

    def action_open_explorer(self) -> None:
        self.perform_action("explorer")

    def action_delete_selected(self) -> None:
        name, _ = self.get_selected_route()
        status_label = self.query_one("#selection-status", Label)
        if name:
            db.delete_route(name)
            status_label.update(f"[yellow]Ruta '{name}' eliminada.[/yellow]")
            self.refresh_data()
        else:
            status_label.update("[red]Error: Selecciona una ruta para eliminar.[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        status_msg = self.query_one("#status-msg", Label)
        grouped_status = self.query_one("#grouped-status", Label)
        
        if button_id in ("btn-opencode", "btn-tree-opencode"):
            self.perform_action("opencode")
        elif button_id in ("btn-vscode", "btn-tree-vscode"):
            self.perform_action("vscode")
        elif button_id in ("btn-explorer", "btn-tree-explorer"):
            self.perform_action("explorer")
        elif button_id == "btn-delete":
            self.action_delete_selected()
        elif button_id == "btn-register":
            name_input = self.query_one("#input-name", Input)
            path_input = self.query_one("#input-path", Input)
            
            name = name_input.value.strip()
            path = path_input.value.strip()
            
            if not name or not path:
                status_msg.update("[red]Por favor completa ambos campos.[/red]")
                return
                
            if not os.path.exists(path):
                status_msg.update("[yellow]Advertencia: La ruta no existe, pero se guardar?.[/yellow]")
                
            try:
                db.add_route(name, path)
                name_input.value = ""
                path_input.value = ""
                status_msg.update(f"[green]Ruta '{name}' registrada con éxito![/green]")
                self.refresh_data()
            except Exception as e:
                status_msg.update(f"[red]Error al guardar: {e}[/red]")
        elif button_id == "btn-create-project":
            p_input = self.query_one("#input-project-name", Input)
            p_name = p_input.value.strip()
            if not p_name:
                grouped_status.update("[red]Error: Escribe un nombre para el proyecto.[/red]")
                return
            db.add_project(p_name)
            p_input.value = ""
            grouped_status.update(f"[green]Proyecto '{p_name}' creado con éxito![/green]")
            self.refresh_data()
        elif button_id == "btn-assign-project":
            sel_route = self.query_one("#select-route", Select)
            sel_project = self.query_one("#select-project", Select)
            
            r_val = sel_route.value
            p_val = sel_project.value
            
            if r_val is Select.BLANK or p_val is Select.BLANK:
                grouped_status.update("[red]Error: Selecciona una ruta y un proyecto.[/red]")
                return
                
            db.assign_route_to_project(r_val, p_val)
            grouped_status.update(f"[green]Asociada ruta '{r_val}' al proyecto '{p_val}'[/green]")
            self.refresh_data()
        elif button_id == "btn-delete-project":
            sel_del_project = self.query_one("#select-delete-project", Select)
            p_val = sel_del_project.value
            if p_val is Select.BLANK:
                grouped_status.update("[red]Error: Selecciona un proyecto a eliminar.[/red]")
                return
            db.delete_project(p_val)
            grouped_status.update(f"[yellow]Proyecto '{p_val}' eliminado (rutas desagrupadas).[/yellow]")
            self.refresh_data()

if __name__ == "__main__":
    app = TextApp()
    app.run()
