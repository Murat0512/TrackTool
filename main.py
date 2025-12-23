import flet as ft
import cv2
import database as db
import reports
import os
import sqlite3
import numpy as np

def main(page: ft.Page):
    # Basic Page Setup
    db.init_db()
    page.title = "TrackTool Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450
    detector = cv2.QRCodeDetector()

    # --- 1. DEFINE UI COMPONENTS FIRST ---
    tool_list = ft.ListView(expand=True, spacing=10)

    # --- 2. DEFINE HELPER FUNCTIONS (Order matters to prevent "not defined" errors) ---

    def refresh_dashboard():
        tool_list.controls.clear()
        for tool in db.get_all_tools():
            status_color = ft.Colors.GREEN if tool[3] == "Available" else ft.Colors.RED
            tool_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.BUILD, color=status_color),
                    title=ft.Text(f"{tool[2]} ({tool[1]})"),
                    subtitle=ft.Text(f"User: {tool[4]} | Return: {tool[5]}"),
                )
            )
        page.update()

    def create_pdf(e):
        report_type = e.control.text.split()[0]
        filename = reports.generate_report(report_type)
        # Web-safe way to handle files without static_dir
        page.launch_url(f"/{filename}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Opening {filename}..."))
        page.snack_bar.open = True
        page.update()

    def show_registration_dialog(qr_id):
        new_name = ft.TextField(label="Machine Name (e.g., Excavator)")
        
        def save_new_tool(e):
            if new_name.value:
                conn = sqlite3.connect("inventory.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tools (qr_id, name, status) VALUES (?, ?, 'Available')",
                    (qr_id, new_name.value),
                )
                conn.commit()
                conn.close()
                page.dialog.open = False
                refresh_dashboard()

        page.dialog = ft.AlertDialog(
            title=ft.Text(f"Register New QR: {qr_id}"),
            content=new_name,
            actions=[ft.TextButton("Save", on_click=save_new_tool)],
        )
        page.dialog.open = True
        page.update()

    def show_checkout_dialog(qr_id):
        worker_name = ft.TextField(label="Worker Name")
        
        def confirm_checkout(e):
            if worker_name.value:
                db.update_tool_status(qr_id, worker_name.value, "In Use", "Today")
                page.dialog.open = False
                refresh_dashboard()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Check-Out Machine"),
            content=worker_name,
            actions=[ft.TextButton("Confirm", on_click=confirm_checkout)],
        )
        page.dialog.open = True
        page.update()

    def handle_scanned_tool(qr_id):
        tool = db.get_tool_by_id(qr_id)
        if not tool:
            show_registration_dialog(qr_id)
        elif tool["status"] == "Available":
            show_checkout_dialog(qr_id)
        else:
            db.update_tool_status(qr_id, "Warehouse", "Available", None)
            refresh_dashboard()

    def on_scan_result(e: ft.FilePickerResultEvent):
        if e.files:
            page.snack_bar = ft.SnackBar(ft.Text("Scanning..."))
            page.snack_bar.open = True
            page.update()
            
            for f in e.files:
                # Use f.path for local/desktop and fallback for web
                path = f.path if f.path else f.name
                img = cv2.imread(path)
                if img is not None:
                    data, _, _ = detector.detectAndDecode(img)
                    if data:
                        handle_scanned_tool(data)
                    else:
                        page.snack_bar = ft.SnackBar(ft.Text("QR not detected. Try a clearer photo."), bgcolor=ft.Colors.RED)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Error reading image file."), bgcolor=ft.Colors.RED)
            page.update()

    # --- 3. INITIALIZE PICKER & UI ---
    scan_picker = ft.FilePicker(on_result=on_scan_result)
    page.overlay.append(scan_picker)

    page.add(
        ft.AppBar(title=ft.Text("TrackTool Pro"), bgcolor=ft.Colors.AMBER_700),
        ft.Row([
            ft.ElevatedButton("Weekly Report", on_click=create_pdf),
            ft.ElevatedButton("Monthly Report", on_click=create_pdf),
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        tool_list,
        ft.FloatingActionButton(
            icon=ft.Icons.CAMERA_ALT,
            text="Scan Tool",
            on_click=lambda _: scan_picker.pick_files(allow_multiple=False),
        ),
    )
    refresh_dashboard()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Removed problematic static_dir to fix deployment crash
    ft.app(target=main, view=None, port=port)