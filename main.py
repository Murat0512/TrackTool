import flet as ft
import cv2
import database as db
import os
import sqlite3
import time

def main(page: ft.Page):
    db.init_db()
    detector = cv2.QRCodeDetector()

    # --- 1. REGISTRATION LOGIC ---
    def handle_tool(qr_id):
        tool = db.get_tool_by_id(qr_id)
        if not tool:
            name_input = ft.TextField(label="Machine Name")
            def save_tool(e):
                conn = sqlite3.connect("inventory.db")
                conn.execute("INSERT INTO tools (qr_id, name, status) VALUES (?, ?, 'Available')", (qr_id, name_info.value))
                conn.commit()
                conn.close()
                page.dialog.open = False
                page.update()
            
            page.dialog = ft.AlertDialog(
                title=ft.Text(f"New QR: {qr_id}"),
                content=name_input,
                actions=[ft.TextButton("Register", on_click=save_tool)]
            )
            page.dialog.open = True
        else:
            # Simple Toggle if exists
            new_status = "In Use" if tool["status"] == "Available" else "Available"
            db.update_tool_status(qr_id, "Worker", new_status, "Today")
            page.snack_bar = ft.SnackBar(ft.Text(f"Machine {tool['name']} is now {new_status}"))
            page.snack_bar.open = True
        page.update()

    # --- 2. THE STABILIZED SCANNER ---
    def on_result(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                # MANDATORY: Upload the file so the server can see it
                page.upload_files([ft.FilePickerUploadFile(f.name, upload_url=page.get_upload_url(f.name, 600))])
                path = os.path.join("uploads", f.name)
                
                # Wait loop to prevent "file not found" crash
                retries = 0
                while not os.path.exists(path) and retries < 10:
                    time.sleep(0.5)
                    retries += 1

                img = cv2.imread(path)
                if img is not None:
                    data, _, _ = detector.detectAndDecode(img)
                    if data:
                        handle_tool(data) # This triggers the registration box
                
                if os.path.exists(path):
                    os.remove(path)
            page.update()

    picker = ft.FilePicker(on_result=on_result)
    page.overlay.append(picker)

    page.add(
        ft.Text("TrackTool Pro", size=25, weight="bold"),
        ft.ElevatedButton("SCAN QR CODE", icon=ft.Icons.CAMERA, on_click=lambda _: picker.pick_files())
    )

if __name__ == "__main__":
    if not os.path.exists("uploads"): os.makedirs("uploads")
    # Simplest possible deployment command
    ft.app(target=main, view=None, port=int(os.getenv("PORT", 8000)), upload_dir="uploads")