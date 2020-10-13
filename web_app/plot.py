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
    '#fcd99d',
    '#f5a452',
    '#d15483',
    '#bd4d8d',
    '#883b7e',
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
        fig = px.line(df, x=x_field, y=y_field, color=category_field, color_discrete_sequence=COLORS_DISTINCT)
        fig.update_traces(line=dict(width=4), line_shape='spline')

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        fig.update_layout(legend=dict(title=legend_title))
        fig.update_layout(
            plot_bgcolor='#f1efee',
            title=None,
            showlegend=self.force_legend or len(fig.data) > 1,
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

        return fig


class CompactHistogramChart:
    def plot(self, df: DataFrame, x_field: str, count_field: str) -> Figure:
        fig = px.histogram(df, x=x_field, y=count_field, histfunc="sum", nbins=30)

        fig.update_layout(
            plot_bgcolor='#f1efee',
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

        return fig


class BoxPlot:
    def plot(
        self,
        df: DataFrame,
        type_field: str,
        value_field: str,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ) -> Figure:
        fig = px.box(df, x=type_field, y=value_field, points="all", color=type_field, color_discrete_sequence=COLORS_PRISM)
        fig.update_traces(boxpoints="outliers", jitter=0.3, hoveron="boxes", marker=dict(opacity=0.3, size=4))
        fig.update_layout(
            plot_bgcolor='#f1efee',
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
            plot_bgcolor='#f1efee',
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
        pairings = df[pair_field].unique()
        num_pairings = len(pairings)

        fig = make_subplots(
            rows=1,
            cols=num_pairings,
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
            plot_bgcolor='#f1efee',
            title=None,
            showlegend=False,
            margin=dict(l=30, r=0, t=20, b=10),
        )

        # When fixedrange=True is set, shared axis do no longer align, so we manually calculate the overall value range
        # and set it to all the axis so they match.
        y_range = (
            max([0, math.floor((df[value_field]['lowerfence'].min() - 5) / 10) * 10]),
            min([100, math.ceil((df[value_field]['upperfence'].max() + 5) / 10) * 10]),
        )

        fig.update_xaxes(title_text=x_title, fixedrange=True)
        fig.update_yaxes(fixedrange=True, range=y_range, showticklabels=False)
        fig.update_yaxes(title_text=y_title, showticklabels=True, row=1, col=1)

        return fig


class RangeBoxPlot:
    def plot(
        self,
        df: DataFrame,
        value_field: str,
    ) -> Figure:
        fig = make_subplots()
        trace = go.Box(
            x=[[1]],
            lowerfence=[df.loc['lowerfence'][value_field]],
            q1=[df.loc['q1'][value_field]],
            median=[df.loc['median'][value_field]],
            mean=[df.loc['mean'][value_field]],
            q3=[df.loc['q3'][value_field]],
            upperfence=[df.loc['upperfence'][value_field]],
            boxpoints=False,
            marker=dict(color=COLORS_PRISM[0]),
        )
        fig.add_trace(trace)

        fig.update_layout(
            plot_bgcolor='#f1efee',
            title=None,
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                fixedrange=True,
            ),
            yaxis=dict(
                showticklabels=False,
                fixedrange=True,
            )
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
        fig = px.bar(
            df,
            x=df[type_field],
            y=df[value_field],
            color=df[value_field],
            color_continuous_scale=COLOR_SEQUENTIAL
        )

        margin = dict(l=30, r=0, t=20, b=10) if self.add_margin else dict(l=0, r=0, t=0, b=0)
        fig.update_layout(
            plot_bgcolor='#f1efee',
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
                title=dict(
                    standoff=30,
                ),
            )
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
            df,
            x=df[type_field],
            y=df[value_field],
            color=df[value_field],
            color_continuous_scale=COLOR_SEQUENTIAL
        )
        fig.update_traces(marker=dict(line=dict(width=0)))

        fig.update_layout(
            plot_bgcolor='#f1efee',
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
            )
        )

        fig.update_xaxes(title_text=x_title)
        fig.update_yaxes(title_text=y_title)

        return fig
