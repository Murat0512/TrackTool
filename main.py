import flet as ft
import cv2
import database as db
import reports
import os
import sqlite3
import numpy as np
import time

def main(page: ft.Page):
    db.init_db()
    page.title = "TrackTool Pro"
    detector = cv2.QRCodeDetector()
    
    # --- 1. RESTORED MACHINERY LIST ---
    tool_list = ft.ListView(expand=True, spacing=10)

    def refresh_dashboard():
        tool_list.controls.clear()
        tools = db.get_all_tools()
        for tool in tools:
            # tool[3] is status, tool[2] is name
            status_color = ft.Colors.GREEN if tool[3] == "Available" else ft.Colors.RED
            tool_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.BUILD, color=status_color),
                    title=ft.Text(f"{tool[2]} ({tool[1]})"),
                    subtitle=ft.Text(f"Status: {tool[3]} | User: {tool[4]}"),
                )
            )
        page.update()

    # --- 2. RESTORED PDF REPORTING ---
    def create_pdf(e):
        report_type = e.control.text.split()[0]
        filename = reports.generate_report(report_type)
        page.launch_url(f"/{filename}") # Stable method for Render
        page.update()

    # --- 3. FIXED REGISTRATION DIALOG ---
    def show_registration(qr_id):
        name_input = ft.TextField(label="Machine Name", autofocus=True)
        def save_click(e):
            if name_input.value:
                conn = sqlite3.connect("inventory.db")
                # Direct SQL insert to ensure the record is created immediately
                conn.execute("INSERT INTO tools (qr_id, name, status) VALUES (?, ?, 'Available')", (qr_id, name_input.value))
                conn.commit()
                conn.close()
                page.dialog.open = False
                refresh_dashboard()
        
        page.dialog = ft.AlertDialog(
            title=ft.Text(f"New QR Detected: {qr_id}"),
            content=ft.Column([ft.Text("Register this machine:"), name_input], tight=True),
            actions=[ft.TextButton("Save to Inventory", on_click=save_click)],
            modal=True # Dialog won't disappear until Saved
        )
        page.dialog.open = True
        page.update()

    # --- 4. FIXED PHONE SCANNER BRIDGE (THE SOLUTION) ---
    def on_scan_result(e: ft.FilePickerResultEvent):
        if e.files:
            page.snack_bar = ft.SnackBar(ft.Text("Scanning QR... Please wait for registration box."))
            page.snack_bar.open = True
            page.update()

            try:
                for f in e.files:
                    # 1. Start the physical upload to Render
                    page.upload_files([ft.FilePickerUploadFile(f.name, upload_url=page.get_upload_url(f.name, 600))])
                    path = os.path.join("uploads", f.name)
                    
                    # 2. THE FIX: Loop until the file actually exists on the server
                    timeout = 0
                    while not os.path.exists(path) and timeout < 30: # 30 retries = 15 seconds max
                        time.sleep(0.5)
                        timeout += 1

                    # 3. Read and Decode
                    img = cv2.imread(path)
                    if img is not None:
                        data, _, _ = detector.detectAndDecode(img)
                        if data:
                            tool = db.get_tool_by_id(data)
                            if not tool:
                                show_registration(data) # This triggers your registration
                            else:
                                # Status toggle if already registered
                                new_status = "In Use" if tool["status"] == "Available" else "Available"
                                db.update_tool_status(data, "Operator", new_status, "Today")
                                refresh_dashboard()
                    
                    if os.path.exists(path): os.remove(path)
            except Exception as ex:
                print(f"Scan failed: {ex}")
            
            page.snack_bar.open = False
            page.update()

    # --- 5. UI LAYOUT ---
    picker = ft.FilePicker(on_result=on_scan_result)
    page.overlay.append(picker)

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
            on_click=lambda _: picker.pick_files()
        )
    )
    refresh_dashboard()

if __name__ == "__main__":
    if not os.path.exists("uploads"): os.makedirs("uploads")
    # Removed crashing 'static_dir' to fix deployment
    ft.app(target=main, view=None, port=int(os.getenv("PORT", 8000)), upload_dir="uploads")