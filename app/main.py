import tkinter as tk
from tkinter import ttk

from models.database import Database
from views.main_view import MainView


def create_app():
    bootstrap_data()
    root = tk.Tk()
    root.title("MercadoShop")
    root.geometry("1180x720")
    root.minsize(980, 620)
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    MainView(root)
    return root


def bootstrap_data():
    db = Database.get_instance()
    db.initialize_schema()


def run():
    app = create_app()
    app.mainloop()


if __name__ == "__main__":
    run()
