import abc
from abc import ABC

from plotly.graph_objs import Figure


class NoDataException(Exception):
    pass


class Chart:
    DEFAULT_WIDTH = 1280
    DEFAULT_HEIGHT = 450

    def __init__(self, figure: Figure, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, title: str = None) -> None:
        self.figure = figure
        self.title = title
        self.width = width
        self.height = height

    def render_json(self) -> str:
        return self.figure.to_json()

    def render_png(self) -> bytes:
        self.configure_image()
        return self.figure.to_image(format="png", width=self.width, height=self.height)

    def render_svg(self) -> bytes:
        self.configure_image()
        return self.figure.to_image(format="svg", width=self.width, height=self.height)

    def configure_image(self):
        margin_top = 30
        title = None
        if self.title is not None:
            margin_top = 50
            title = dict(
                text=self.title,
                x=0.5,
                xanchor='center',
            )
        self.figure.update_layout(
            title=title,
            margin=dict(l=10, r=10, t=margin_top, b=30),
        )


class ChartDefinition(ABC):
    @abc.abstractmethod
    def get_chart_title(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_image_alt(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def plot(self) -> Chart:
        raise NotImplementedError
