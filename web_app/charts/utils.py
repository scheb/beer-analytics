from plotly.graph_objs import Figure


class NoDataException(Exception):
    pass


class Chart:
    def __init__(self, figure: Figure, width: int = 600, height: int = 200) -> None:
        self.figure = figure
        self.width = width
        self.height = height

    def render_json(self) -> str:
        return self.figure.to_json()

    def render_png(self) -> bytes:
        return self.figure.to_image(format="png", width=self.width, height=self.height)

    def render_svg(self) -> bytes:
        return self.figure.to_image(format="svg", width=self.width, height=self.height)
