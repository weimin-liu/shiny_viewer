from shiny import App, ui, reactive, render, run_app
import pandas as pd
import threading
import time
import webbrowser
import os
import h5py
import plotly.graph_objs as go
from shinywidgets import output_widget, render_widget
import plotly.express as px

def hdf_view_tab():
    return [
        ui.card(
            ui.card_header("HDF File Path"),
            ui.input_text("hdf_path", "HDF5 file path", value="path/to/hdf5"),
        ),
        ui.card(
            ui.card_header("HDF File Keys"),
            ui.input_select("hdf_keys", "HDF5 file keys", choices=[]),
        ),
        ui.card(
            ui.card_header("HDF Dataframe"),
            ui.output_data_frame("hdf_dataframe"),
        ),
    ]

def plot_tab():
    return [
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select('x', label='x_value', choices=[]),
                ui.input_select('y', label='y_value', choices=[]),
            ),
            output_widget('plot')
        )
        ]

app_ui = ui.page_fluid(
    ui.navset_tab(
        ui.nav_panel(
            "HDF5 Viewer",
            *hdf_view_tab()
        ),
        ui.nav_panel(
            "Plot",
            *plot_tab()
        )
    )
)


def server(input, output, session):

    df = reactive.Value(pd.DataFrame())

    def read_hdf_keys(path):
        if os.path.exists(path) and path != "path/to/hdf5":
            with h5py.File(path, "r") as hdf:
                hdf_keys = list(hdf.keys())
                return hdf_keys
        return []

    @reactive.effect
    def update_dynamic_key_selection():
        path = input.hdf_path()
        keys = read_hdf_keys(path)
        ui.update_select("hdf_keys", choices=keys)

    @reactive.effect
    @reactive.event(input.hdf_keys)
    def update_dynamic_axis_selection():
        columns = pd.read_hdf(input.hdf_path(), key=input.hdf_keys()).columns
        ui.update_select("x", choices = list(columns))
        ui.update_select("y", choices = list(columns))


    @reactive.effect
    @reactive.event(input.hdf_keys)
    def read_hdf_dataframe_by_selected_key():
        try:
            df.set(pd.read_hdf(input.hdf_path(), key=input.hdf_keys()))
        except Exception as e:
            print(e)

    @render_widget
    def plot():
        df = pd.read_hdf(input.hdf_path(), key=input.hdf_keys())
        x = input.x()
        y = input.y()
        df = df.sort_values(by=x)
        fig = px.line(
            df,
            x=x,
            y=y,
        ).update_layout(showlegend=False)
        return fig

    @output
    @render.data_frame
    def hdf_dataframe():
        return df()


def main():
    app = App(app_ui, server)

    def start_server():
        run_app(app, port=61235)

    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1)
    webbrowser.open("http://localhost:61235")

    # Prevent the main thread from exiting
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")


if __name__ == "__main__":
    main()