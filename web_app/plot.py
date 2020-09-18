from typing import Optional

import plotly.graph_objects as go
from pandas import DataFrame
from plotly import express as px
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

COLORS_DISTINCT = px.colors.qualitative.Vivid
COLORS_PRISM = px.colors.qualitative.Prism
COLOR_SEQUENTIAL = px.colors.sequential.Sunsetdark


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
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
        legend_title: str = None
    ) -> Plot:
        fig = px.line(df, x=x_field, y=y_field, color=category_field, color_discrete_sequence=COLORS_DISTINCT)
        fig.update_traces(line=dict(width=4))

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        fig.update_layout(legend=dict(title=legend_title))
        fig.update_layout(
            title=None,
            showlegend=len(fig.data) > 1,
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
        # fig.update_traces(marker=dict(cmin=0, cmax=1000, colorsrc=count_field))

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                title_text=None,
                fixedrange=True,
            ),
            yaxis=dict(
                visible=False,
                fixedrange=True,
            ),
        )

        return Plot(fig)


class BoxPlot:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Plot:
        fig = px.box(df, x=type_field, y=value_field, points="all", color=type_field, color_discrete_sequence=COLORS_PRISM)
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


class PreAggregatedBoxPlot:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Plot:
        fig = make_subplots()
        column = 0
        for trace_name in df[type_field].values.tolist():
            trace_df = df[df[type_field].eq(trace_name)]
            trace = go.Box(
                x=[trace_name],
                y=[[1]],
                lowerfence=trace_df[value_field]['lowerfence'],
                q1=trace_df[value_field]['q1'],
                median=trace_df[value_field]['median'],
                mean=trace_df[value_field]['mean'],
                q3=trace_df[value_field]['q3'],
                upperfence=trace_df[value_field]['upperfence'],
                boxpoints=False,
                name=trace_name,
                marker=dict(color=COLORS_PRISM[column % len(COLORS_PRISM)]),
            )
            fig.add_trace(trace)
            column += 1

        fig.update_layout(
            title=None,
            showlegend=False,
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

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return Plot(fig)


class PreAggregatedPairsBoxPlot:
    def plot(
        self,
        df: DataFrame,
        pair_field: str,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Plot:
        pairings = df[pair_field].unique()
        num_pairings = len(pairings)

        fig = make_subplots(
            rows=1,
            cols=num_pairings,
            shared_yaxes=True,
            horizontal_spacing=0.005
        )

        column = 0
        for pairing in pairings:
            column += 1
            df_pair = df[df[pair_field].eq(pairing)]
            for trace_name in df_pair[type_field].values.tolist():
                trace_df = df_pair[df_pair[type_field].eq(trace_name)]
                trace = go.Box(
                    x=[trace_name],
                    y=[[1]],
                    lowerfence=trace_df[value_field]['lowerfence'],
                    q1=trace_df[value_field]['q1'],
                    median=trace_df[value_field]['median'],
                    mean=trace_df[value_field]['mean'],
                    q3=trace_df[value_field]['q3'],
                    upperfence=trace_df[value_field]['upperfence'],
                    boxpoints=False,
                    name=trace_name,
                    marker=dict(color=COLORS_PRISM[column % len(COLORS_PRISM)]),
                )
                fig.add_trace(trace, row=1, col=column)

        fig.update_layout(
            title=None,
            showlegend=False,
            margin=dict(l=30, r=0, t=20, b=10),
        )

        fig.update_xaxes(title_text=x_title, fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        fig.update_yaxes(title_text=y_title, row=1, col=1)

        return Plot(fig)


class BarChart:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Plot:
        fig = px.bar(
            df,
            x=df[type_field],
            y=df[value_field],
            color=df[value_field],
            color_continuous_scale=COLOR_SEQUENTIAL
        )

        fig.update_layout(
            title=None,
            showlegend=False,
            coloraxis=dict(
                showscale=False,
            ),
            margin=dict(l=30, r=0, t=20, b=10),
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

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return Plot(fig)


class PreAggregateHistogramChart:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Plot:
        fig = px.bar(
            df,
            x=df[type_field],
            y=df[value_field],
            color=df[value_field],
            color_continuous_scale=COLOR_SEQUENTIAL
        )
        fig.update_traces(marker=dict(line=dict(width=0)))

        fig.update_layout(
            title=None,
            showlegend=False,
            bargap=0,
            coloraxis=dict(
                showscale=False,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                visible=False,
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