import flet as ft
import cv2
import database as db
import reports
import os
import sqlite3
import numpy as np
import time

def main(page: ft.Page):
    # Initialize Database and Settings
    db.init_db()
    page.title = "TrackTool Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450
    detector = cv2.QRCodeDetector()

    # --- 1. UI COMPONENTS ---
    tool_list = ft.ListView(expand=True, spacing=10)

    # --- 2. DIALOGS & LOGIC ---

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

    def show_registration_dialog(qr_id):
        new_name = ft.TextField(label="Machine Name")
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
            title=ft.Text(f"Register New Tool: {qr_id}"),
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

    # --- 3. THE SCANNER BRIDGE (FIXED PATHS) ---

    def on_scan_result(e: ft.FilePickerResultEvent):
        if e.files:
            page.snack_bar = ft.SnackBar(ft.Text("Scanning... Please wait."))
            page.snack_bar.open = True
            page.update()

            try:
                for f in e.files:
                    # Physically upload file to Render
                    page.upload_files([
                        ft.FilePickerUploadFile(f.name, upload_url=page.get_upload_url(f.name, 600))
                    ])
                    
                    # FIX: Look in only ONE 'uploads' folder
                    path = os.path.join("uploads", f.name)

                    # Wait for the file to finish writing
                    retries = 0
                    while not os.path.exists(path) and retries < 10:
                        time.sleep(0.5)
                        retries += 1

                    # Scan the file with OpenCV
                    img = cv2.imread(path)
                    if img is not None:
                        data, _, _ = detector.detectAndDecode(img)
                        if data:
                            handle_scanned_tool(data)
                        else:
                            page.snack_bar = ft.SnackBar(ft.Text("QR not detected. Try again."), bgcolor=ft.Colors.RED)
                    
                    # Cleanup server space
                    if os.path.exists(path):
                        os.remove(path)

            except Exception as ex:
                print(f"Scan Error: {ex}")

            # FIX: Ensure snackbar closes and page updates to reset the scanner
            page.snack_bar.open = False
            page.update()

    # --- 4. UI SETUP ---
    scan_picker = ft.FilePicker(on_result=on_scan_result)
    page.overlay.append(scan_picker)

    page.add(
        ft.AppBar(title=ft.Text("TrackTool Pro"), bgcolor=ft.Colors.AMBER_700),
        ft.Row([
            ft.ElevatedButton("Weekly Report", on_click=lambda _: page.launch_url("/weekly_report.pdf")),
            ft.ElevatedButton("Monthly Report", on_click=lambda _: page.launch_url("/monthly_report.pdf")),
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
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    port = int(os.getenv("PORT", 8000))
    # Corrected app call for Render
    ft.app(target=main, view=None, port=port, upload_dir="uploads")