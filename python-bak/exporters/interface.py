import abc

class ExporterInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'export_data') and
                callable(subclass.export_data) or
                NotImplemented)

    @abc.abstractmethod
    def export_data(self):
        """Export data from the current provider"""
        raise NotImplementedError
