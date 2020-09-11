from typing import Optional

from pandas import DataFrame
from plotly import express as px
from plotly.graph_objs import Figure


class Plot:
    def __init__(self, figure: Figure) -> None:
        self.figure = figure

    def render_json(self) -> str:
        return self.figure.to_json()

    def render_png(self) -> bytes:
        return self.figure.to_image(format="png")

    def render_svg(self) -> bytes:
        return self.figure.to_image(format="svg")


class LinesChart:
    def plot(
        self,
        df: DataFrame,
        x_field: str,
        y_field: str,
        category_field: str,
        x_title: Optional[str],
        y_title: Optional[str],
        legend_title: str = None,
        category_names: dict = None
    ) -> Plot:
        fig = px.line(df, x=x_field, y=y_field, color=category_field)

        # Relabel traces
        if category_names is not None:
            for trace in fig.data:
                if trace.name in category_names:
                    trace.name = category_names[trace.name]

        fig.update_xaxes(title_text=x_title)
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
            )
        )

        return Plot(fig)


class CompactHistogramChart:
    def plot(self, df: DataFrame, x_field: str, count_field: str) -> Plot:
        fig = px.histogram(df, x=x_field, y=count_field, histfunc="sum", nbins=30)
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                title_text=None,
            ),
            yaxis=dict(
                visible=False,
            ),
        )

        return Plot(fig)


class BoxPlot:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str],
        y_title: Optional[str]
    ) -> Plot:
        fig = px.box(df, x=type_field, y=value_field, points="all", color=type_field, color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_traces(boxpoints="outliers", jitter=0.3, hoveron="boxes", marker=dict(opacity=0.3, size=4))
        fig.update_layout(
            title=None,
            showlegend=False,
            margin=dict(l=10, r=0, t=20, b=10),
            xaxis=dict(
                fixedrange=True,
                categoryorder="total descending",
            ),
            yaxis=dict(
                fixedrange=True,
                title=dict(
                    standoff=30,
                ),
            )
        )

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return Plot(fig)
