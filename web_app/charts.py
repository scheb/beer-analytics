from pandas import DataFrame
from plotly import express as px
from plotly.graph_objs import Figure


class Plot:
    def __init__(self, figure: Figure) -> None:
        self.figure = figure

    def render_json(self) -> str:
        return self.figure.to_json()

    def render_png(self, file_path) -> bytes:
        return self.figure.to_image(format="png")

    def render_svg(self, file_path) -> bytes:
        return self.figure.to_image(format="svg")


class LinesChart:
    def plot(
        self,
        df: DataFrame,
        x_field: str,
        y_field: str,
        category_field: str,
        x_title: str=None,
        y_title: str=None,
        legend_title: str=None,
        category_names: dict=None
    ) -> Plot:
        fig = px.line(df, x=x_field, y=y_field, color=category_field)

        # Relabel traces
        if category_names is not None:
            for trace in fig.data:
                if trace.name in category_names:
                    trace.name = category_names[trace.name]

        if x_title is not None:
            fig.update_xaxes(title_text=x_title)
        if y_title is not None:
            fig.update_yaxes(title_text=y_title)

        fig.update_layout(legend=dict(title=legend_title))
        fig.update_layout(
            title=None,
            margin=dict(l=10, r=0, t=20, b=10),
            xaxis=dict(
                fixedrange=True,
            ),
            yaxis=dict(
                fixedrange=True,
                title=dict(
                    standoff=30,
                ),
            ),
            yaxis2=dict(
                fixedrange=True,
            ),
        )

        return Plot(fig)
