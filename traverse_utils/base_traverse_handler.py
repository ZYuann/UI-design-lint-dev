from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple, TypeVar, Dict, Any, Type

from sketch_utils import SketchFile, Page, Artboard, AnyLayer, Group
from traverse_utils.layer_transform import LayerTransformed


class BaseTraverseHandler(ABC):
    """
    A base class for traverse handler.
    """

    def init_sketch(self, sketch_file: SketchFile):
        """
        initialization in sketch.
        """
        pass

    def init_artboard(self, sketch_file: SketchFile, page: Page, artboard: Artboard) -> None:
        """
        initialization in artboard.
        do anything like create image or generate list .etc as you want
        """
        pass

    @abstractmethod
    def handle_layer(self, layer: LayerTransformed, layer_stack: Tuple[AnyLayer, ...]) -> None:
        """
        handle a visible layer.
        @param layer: the transformed layer with polygon
        @param layer_stack: the layer stack to reach this layer
        """
        pass

    @abstractmethod
    def if_group_need_handle(self, group: Group) -> bool:
        """
        if a group need extra handle.
        @param group: the group to be checked
        """
        pass

    @abstractmethod
    def handle_group(self, layer: LayerTransformed, layer_stack: Tuple[AnyLayer, ...]) -> None:
        """
        handle a group match :py:func:`BaseTraverseHandler.if_group_need_handle` result.
        @param layer: the transformed group layer with polygon
        @param layer_stack: the layer stack to reach this layer
        """
        pass

    def finish_artboard(self) -> None:
        """
        finish traverse for artboard
        do anything like save image or save list file .etc as you want
        """
        pass

    def finish_sketch(self) -> None:
        """
        finish traverse for sketch
        do anything like save image or save list file .etc as you want
        """
        pass


T = TypeVar('T', bound=BaseTraverseHandler)


class CreateBaseTraverseHandlerOption:
    class_loader: Type[T]
    option: Dict[str, Any]

    def __init__(self, class_loader: Type[T], option: Dict[str, Any]):
        self.class_loader = class_loader
        self.option = option

    def create_instance(self) -> T:
        return self.class_loader(**self.option)


__all__ = [
    'CreateBaseTraverseHandlerOption', 'BaseTraverseHandler'
]
