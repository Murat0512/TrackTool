import flet as ft
import database as db
import cv2 # Make sure to: pip install opencv-python

def main(page: ft.Page):
    db.init_db()
    page.title = "ToolGuard Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450 # Mobile feel for testing

    # --- Functions ---
    def open_scanner(e):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            # Simple QR Detection (Placeholder for real decoding)
            cv2.imshow("Scanning Tool QR...", frame)
            
            # Press 'q' to stop or imagine a QR is detected
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        page.snack_bar = ft.SnackBar(ft.Text("Tool Scanned Successfully!"))
        page.snack_bar.open = True
        page.update()

    # --- UI Elements ---
    title_section = ft.Text("Inventory Overview", size=25, weight="bold")
    
    # Tool List View
    tool_list = ft.ListView(expand=True, spacing=10)
    
    # Load initial data
    for tool in db.get_all_tools():
        tool_list.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.icons.BUILD_CIRCLE, color="blue"),
                title=ft.Text(f"{tool[2]} ({tool[1]})"),
                subtitle=ft.Text(f"With: {tool[4]} | Status: {tool[3]}"),
                trailing=ft.Text(tool[5] if tool[5] else "")
            )
        )

    # --- Main Layout ---
    page.add(
        ft.AppBar(title=ft.Text("ToolGuard"), bgcolor=ft.colors.AMBER_400),
        title_section,
        ft.Divider(),
        tool_list,
        ft.FloatingActionButton(
            icon=ft.icons.QR_CODE_SCANNER, 
            text="Scan Tool", 
            on_click=open_scanner,
            bgcolor=ft.colors.AMBER_700
        )
    )

ft.app(target=main)