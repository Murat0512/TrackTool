import flet as ft
import cv2
from pyzbar.pyzbar import decode
import database as db
from datetime import datetime

def main(page: ft.Page):
    db.init_db()
    page.title = "TrackTool Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450 

    # --- UI Logic Functions ---

    def handle_scanned_tool(qr_id):
        """Processes the QR data and decides the next action."""
        tool = db.get_tool_by_id(qr_id)
        
        if not tool:
            page.snack_bar = ft.SnackBar(ft.Text(f"Tool {qr_id} not registered!"))
            page.snack_bar.open = True
        elif tool['status'] == 'Available':
            # Tool is here, so we check it OUT
            show_checkout_dialog(qr_id)
        else:
            # Tool is out, so we check it IN
            db.update_tool_status(qr_id, "Warehouse", "Available", None)
            page.snack_bar = ft.SnackBar(ft.Text(f"Tool {qr_id} returned successfully!"), bgcolor="green")
            page.snack_bar.open = True
            refresh_dashboard()
        
        page.update()

    def show_checkout_dialog(qr_id):
        """Form for assigning a tool to a worker and handling overnight status."""
        worker_name = ft.TextField(label="Worker Name", prefix_icon=ft.icons.PERSON)
        overnight = ft.Checkbox(label="Keeping Overnight? (Next Day Return)")

        def confirm_checkout(e):
            if not worker_name.value:
                worker_name.error_text = "Name required"
                page.update()
                return

            status = "Off-Site" if overnight.value else "In Use"
            return_date = "Next Day" if overnight.value else "Today"
            
            db.update_tool_status(qr_id, worker_name.value, status, return_date)
            page.dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Assigned to {worker_name.value}"), bgcolor="blue")
            page.snack_bar.open = True
            refresh_dashboard()
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(f"Check-Out: {qr_id}"),
            content=ft.Column([worker_name, overnight], tight=True),
            actions=[ft.TextButton("Confirm", on_click=confirm_checkout)]
        )
        page.dialog.open = True
        page.update()

    def open_scanner(e):
        """Triggers the Windows Camera to find a QR code."""
        cap = cv2.VideoCapture(0)
        found_qr = None

        while True:
            ret, frame = cap.read()
            if not ret: break

            for barcode in decode(frame):
                found_qr = barcode.data.decode('utf-8')
                break

            if found_qr: break

            cv2.imshow("TrackTool Scanner (Press 'Q' to cancel)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        cap.release()
        cv2.destroyAllWindows()

        if found_qr:
            handle_scanned_tool(found_qr)

    def refresh_dashboard():
        """Updates the list on the screen."""
        tool_list.controls.clear()
        for tool in db.get_all_tools():
            status_color = "green" if tool[3] == "Available" else "red"
            tool_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.BUILD, color=status_color),
                    title=ft.Text(f"{tool[2]} ({tool[1]})"),
                    subtitle=ft.Text(f"User: {tool[4]} | Return: {tool[5]}"),
                )
            )
        page.update()

    # --- Initial Page Layout ---
    tool_list = ft.ListView(expand=True, spacing=10)
    
    page.add(
        ft.AppBar(title=ft.Text("TrackTool Pro"), bgcolor=ft.colors.AMBER_700),
        ft.Text("Active Inventory", size=20, weight="bold"),
        tool_list,
        ft.FloatingActionButton(
            icon=ft.icons.QR_CODE_SCANNER, 
            text="Scan Tool", 
            on_click=open_scanner,
            bgcolor=ft.colors.AMBER_accent_400
        )
    )
    
    refresh_dashboard()

ft.app(target=main)