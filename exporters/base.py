import click
from abc import ABCMeta, abstractmethod


class BaseExporter(metaclass=ABCMeta):
    def __init__(self, ctx, settings):
        self.ctx = ctx
        self.settings = settings

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "_export_data")
            and callable(subclass._export_data)
            or NotImplemented
        )

    @abstractmethod
    def _check_prerequisites(self):
        """Export data from the source vendor"""
        raise NotImplementedError

    @abstractmethod
    def _export_data(self):
        raise NotImplementedError

    def export(self):
        self.ctx.item("Checking pre-requisites")
        try:
            self._check_prerequisites()
        except Exception as e:
            self.ctx.fail(e)

        self.ctx.success("Success")

        self.ctx.item("Exporting data from the source vendor", nl=True)
        try:
          self._export_data()
        except Exception as e:
            self.ctx.fail(e)
