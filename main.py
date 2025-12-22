import flet as ft
import cv2
from pyzbar.pyzbar import decode
import database as db
import reports  # Handles the PDF generation logic
import os
import sqlite3
from datetime import datetime


def main(page: ft.Page):
    db.init_db()
    page.title = "TrackTool Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450

    # --- FUNCTION 1: PDF Reporting ---
    def create_pdf(e):
        """Generates a PDF report and opens it automatically."""
        report_type = e.control.text.split()[0]
        filename = reports.generate_report(report_type)
        # os.startfile is specific to Windows
        os.startfile(filename)
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Generated {filename}"), bgcolor=ft.Colors.BLUE
        )
        page.snack_bar.open = True
        page.update()

    # --- FUNCTION 2: New Tool Registration ---
    def show_registration_dialog(qr_id):
        """Allows users to register an unknown QR code as a new tool."""
        new_name = ft.TextField(label="New Tool Name (e.g., Makita Drill)")

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
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Registered {new_name.value}!"), bgcolor=ft.Colors.GREEN
                )
                page.snack_bar.open = True
                refresh_dashboard()
                page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(f"Register New QR: {qr_id}"),
            content=new_name,
            actions=[ft.TextButton("Save Tool", on_click=save_new_tool)],
        )
        page.dialog.open = True
        page.update()

    def handle_scanned_tool(qr_id):
        """Determines if a tool needs registration, checkout, or return."""
        tool = db.get_tool_by_id(qr_id)

        if not tool:
            # Trigger the registration function if tool is missing from DB
            show_registration_dialog(qr_id)
        elif tool["status"] == "Available":
            show_checkout_dialog(qr_id)
        else:
            db.update_tool_status(qr_id, "Warehouse", "Available", None)
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Tool {qr_id} Returned!"), bgcolor=ft.Colors.GREEN
            )
            page.snack_bar.open = True
            refresh_dashboard()
        page.update()

    def show_checkout_dialog(qr_id):
        worker_name = ft.TextField(label="Worker Name", prefix_icon=ft.Icons.PERSON)
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
            refresh_dashboard()
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(f"Check-Out: {qr_id}"),
            content=ft.Column([worker_name, overnight], tight=True),
            actions=[ft.TextButton("Confirm", on_click=confirm_checkout)],
        )
        page.dialog.open = True
        page.update()

    def open_scanner(e):
        cap = cv2.VideoCapture(0)
        found_qr = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            for barcode in decode(frame):
                found_qr = barcode.data.decode("utf-8")
                break
            if found_qr:
                break
            cv2.imshow("TrackTool Scanner (Q to Quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()
        if found_qr:
            handle_scanned_tool(found_qr)

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

    # --- UI Layout ---
    tool_list = ft.ListView(expand=True, spacing=10)

    page.add(
        ft.AppBar(title=ft.Text("TrackTool Pro"), bgcolor=ft.Colors.AMBER_700),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Weekly Report", icon=ft.Icons.PICTURE_AS_PDF, on_click=create_pdf
                ),
                ft.ElevatedButton(
                    "Monthly Report", icon=ft.Icons.PICTURE_AS_PDF, on_click=create_pdf
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Divider(),
        ft.Text("Active Inventory", size=20, weight="bold"),
        tool_list,
        ft.FloatingActionButton(
            icon=ft.Icons.QR_CODE_SCANNER,
            text="Scan Tool",
            on_click=open_scanner,
            bgcolor=ft.Colors.AMBER_ACCENT_400,
        ),
    )
    refresh_dashboard()


# This forces the app to run as a web portal, preventing desktop errors
ft.app(target=main, view=ft.AppView.WEB_BROWSER)
