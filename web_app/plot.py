import math
from typing import Optional

import plotly.graph_objects as go
from pandas import DataFrame
from plotly import express as px
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

COLORS_PRISM = px.colors.qualitative.Prism
COLORS_DISTINCT = COLORS_PRISM

COLOR_SEQUENTIAL = [
    "#fcd99d",
    "#f5a452",
    "#d15483",
    "#bd4d8d",
    "#883b7e",
]


class LinesChart:
    def __init__(self, force_legend: bool = False) -> None:
        self.force_legend = force_legend

    def plot(
        self,
        df: DataFrame,
        x_field: str,
        y_field: str,
        category_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
        legend_title: str = None,
    ) -> Figure:
        # When the value is percent, format it with 2 decimals
        if "percent" in y_field:
            hover_data = {y_field: ":.2p"}
            tick_format = ".2p"
        else:
            hover_data = None
            tick_format = None

        fig = px.line(
            df,
            x=x_field,
            y=y_field,
            color=category_field,
            color_discrete_sequence=COLORS_DISTINCT,
            hover_data=hover_data,
        )
        try:
            fig.update_traces(line=dict(width=4), line_shape="spline")
        except ValueError:
            # Spline rendering is sometimes causing issues when there's too much data
            fig.update_traces(line=dict(width=4))

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        fig.update_layout(legend=dict(title=legend_title))
        fig.update_layout(
            plot_bgcolor="#f1efee",
            title=None,
            showlegend=self.force_legend or len(fig.data) > 1,
            margin=dict(l=10, r=0, t=20, b=10),
            xaxis=dict(
                fixedrange=True,
            ),
            yaxis=dict(
                tickformat=tick_format,
                fixedrange=True,
                title=dict(
                    standoff=30,
                ),
            ),
        )

        return fig


class PreAggregatedBoxPlot:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Figure:
        # When the value is percent, format it with 2 decimals
        if "percent" in value_field:
            hover_format = ".2p"
            tick_format = ".2p"
        else:
            hover_format = None
            tick_format = None

        fig = make_subplots()
        column = 0
        for trace_name in df[type_field].values.tolist():
            trace_df = df[df[type_field].eq(trace_name)]
            trace = go.Box(
                x=[trace_name],
                y=[[1]],
                lowerfence=trace_df[value_field]["lowerfence"],
                q1=trace_df[value_field]["q1"],
                median=trace_df[value_field]["median"],
                mean=trace_df[value_field]["mean"],
                q3=trace_df[value_field]["q3"],
                upperfence=trace_df[value_field]["upperfence"],
                boxpoints=False,
                name=trace_name,
                marker=dict(color=COLORS_PRISM[column % len(COLORS_PRISM)]),
            )
            fig.add_trace(trace)
            column += 1

        fig.update_layout(
            plot_bgcolor="#f1efee",
            title=None,
            showlegend=False,
            margin=dict(l=10, r=0, t=20, b=10),
            xaxis=dict(
                fixedrange=True,
            ),
            yaxis=dict(
                fixedrange=True,
                tickformat=tick_format,
                hoverformat=hover_format,
                title=dict(
                    standoff=30,
                ),
            ),
        )

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return fig


class PreAggregatedPairsBoxPlot:
    def plot(
        self,
        df: DataFrame,
        pair_field: str,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Figure:
        # When the value is percent, format it with 2 decimals
        if "percent" in value_field:
            hover_format = ".2p"
            tick_format = ".2p"
        else:
            hover_format = None
            tick_format = None

        pairings = df[pair_field].unique()
        num_pairings = len(pairings)

        fig = make_subplots(rows=1, cols=num_pairings, horizontal_spacing=0.005)

        column = 0
        for pairing in pairings:
            column += 1
            df_pair = df[df[pair_field].eq(pairing)]
            for trace_name in df_pair[type_field].values.tolist():
                trace_df = df_pair[df_pair[type_field].eq(trace_name)]
                trace = go.Box(
                    x=[trace_name],
                    y=[[1]],
                    lowerfence=trace_df[value_field]["lowerfence"],
                    q1=trace_df[value_field]["q1"],
                    median=trace_df[value_field]["median"],
                    mean=trace_df[value_field]["mean"],
                    q3=trace_df[value_field]["q3"],
                    upperfence=trace_df[value_field]["upperfence"],
                    boxpoints=False,
                    name=trace_name,
                    marker=dict(color=COLORS_PRISM[column % len(COLORS_PRISM)]),
                )
                fig.add_trace(trace, row=1, col=column)

        fig.update_layout(
            plot_bgcolor="#f1efee",
            title=None,
            showlegend=False,
            margin=dict(l=30, r=0, t=20, b=10),
            yaxis=dict(
                tickformat=tick_format,
            ),
        )

        # When fixedrange=True is set, shared axis do no longer align, so we manually calculate the overall value range
        # and set it to all the axis so they match.
        y_range = (
            max([0, math.floor((df[value_field]["lowerfence"].min() * 100 - 5) / 10) * 10]) / 100,
            min([100, math.ceil((df[value_field]["upperfence"].max() * 100 + 5) / 10) * 10]) / 100,
        )

        fig.update_xaxes(title_text=x_title, fixedrange=True)
        fig.update_yaxes(fixedrange=True, range=y_range, showticklabels=False, hoverformat=hover_format)
        fig.update_yaxes(title_text=y_title, showticklabels=True, row=1, col=1)

        return fig


class RangeBoxPlot:
    def plot(
        self,
        df: DataFrame,
        value_field: str,
    ) -> Figure:
        # When the value is percent, format it with 2 decimals
        if "percent" in value_field:
            hover_format = ".3p"
            tick_format = ".0%"
        else:
            hover_format = None
            tick_format = None

        fig = px.box(df, x=df[value_field], color_discrete_sequence=COLORS_PRISM)
        fig.update_traces(
            boxpoints=False,
            boxmean=True,
        )

        fig.update_xaxes(title_text=None)
        fig.update_layout(
            plot_bgcolor="#f1efee",
            title=None,
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                tickformat=tick_format,
                hoverformat=hover_format,
                fixedrange=True,
            ),
            yaxis=dict(
                showticklabels=False,
                fixedrange=True,
            ),
        )

        return fig


class BarChart:
    def __init__(self, add_margin: bool = True) -> None:
        self.add_margin = add_margin

    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Figure:
        # When the value is percent, format it with 2 decimals
        if "percent" in value_field:
            hover_data = {value_field: ":.2p"}
            tick_format = ".2p"
        else:
            hover_data = None
            tick_format = None

        fig = px.bar(
            df,
            x=df[type_field],
            y=df[value_field],
            color=df[value_field],
            color_continuous_scale=COLOR_SEQUENTIAL,
            hover_data=hover_data,
        )

        margin = dict(l=30, r=0, t=20, b=10) if self.add_margin else dict(l=0, r=0, t=0, b=0)
        fig.update_layout(
            plot_bgcolor="#f1efee",
            title=None,
            showlegend=False,
            coloraxis=dict(
                showscale=False,
            ),
            margin=margin,
            xaxis=dict(
                fixedrange=True,
            ),
            yaxis=dict(
                fixedrange=True,
                tickformat=tick_format,
                title=dict(
                    standoff=30,
                ),
            ),
        )

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return fig


class PreAggregateHistogramChart:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Figure:
        fig = px.bar(
            df, x=df[type_field], y=df[value_field], color=df[value_field], color_continuous_scale=COLOR_SEQUENTIAL
        )
        fig.update_traces(marker=dict(line=dict(width=0)))

        fig.update_layout(
            plot_bgcolor="#f1efee",
            title=None,
            showlegend=False,
            bargap=0,
            coloraxis=dict(
                showscale=False,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                visible=False,
                fixedrange=True,
            ),
            yaxis=dict(
                fixedrange=True,
                title=dict(
                    standoff=30,
                ),
            ),
        )

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return fig
