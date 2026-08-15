"""
desktop_run.py - Point d'entrée de l'application desktop Smart Callender

Lance l'interface Tkinter/ttkbootstrap (fenêtre de connexion puis tableau de bord
selon le rôle). À exécuter avec Python dans un environnement virtuel (venv).
"""
import ttkbootstrap as ttk
from app.gui.main import DesktopApp


def main():
    # themename options: flatly, cosmo, journal, superhero, darkly, cyborg...
    root = ttk.Window(themename="flatly")
    app = DesktopApp(root)
    
    # Centre la fenêtre au démarrage
    root.place_window_center()
    
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
