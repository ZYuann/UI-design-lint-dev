import threading
import time
from dataclasses import dataclass
from queue import Queue
from typing import Optional, List, Dict, Tuple

from shapely.geometry import Point, Polygon

from console_utils import ConsoleColor
from sketch_utils import AnyLayer, Artboard, Color, Group, Page, SymbolInstance, SymbolMaster, SketchFile, Uuid, \
    from_file
from .base_traverse_handler import CreateBaseTraverseHandlerOption, BaseTraverseHandler
from .layer_transform import BoundArea, recursive_remove_layer, \
    Transform, Scale, Rotation, transform_layer, get_polygon_exterior


@dataclass
class ClippingMask:
    """
    A class that can be used to check whether a layer has a clipping mask.
    """
    hasClippingMask: bool
    mask: Optional[BoundArea] = None


class PreProcess:
    sketch_list: List[str]
    create_handler_option: CreateBaseTraverseHandlerOption

    def __init__(self, sketch_list: List[str], create_handler_option: CreateBaseTraverseHandlerOption, thread_num=5):
        """
        @param sketch_list: sketch file path list
        @param create_handler_option: the option for create handler
        """
        self.create_handler_option = create_handler_option
        self.thread_num = thread_num
        # load sketches from files
        self.sketch_list = []
        for sketch_file_path in sketch_list:
            try:
                self.sketch_list.append(sketch_file_path)
            except Exception as e:
                ConsoleColor.RED.cprint(f"error happened when reading sketch {sketch_file_path}")
                ConsoleColor.RED.cprint(str(e))
        self.count = 0

    def process(self) -> None:
        """
        traverse sketch list and generate image for each sketch artboard
        """
        # for each sketch
        # for sketch_file_path in self.sketch_list:
        #     try:
        #         sketch = from_file(sketch_file_path)
        #         if sketch is not None:
        #             print(ConsoleColor.GREEN + f"processing sketch {sketch.filepath}")
        #             PreProcessEachSketch(
        #                 sketch, self.create_handler_option.create_instance()).process()
        #     except Exception as e:
        #         print(ConsoleColor.RED + f"error happened when processing sketch of index {sketch_file_path}")
        #         print(ConsoleColor.RED + str(e))

        sketch_queue = Queue()
        for sketch_file_path in self.sketch_list:
            sketch_queue.put(sketch_file_path)
        for i in range(self.thread_num):
            worker = PreProcessThreadWorker(
                sketch_queue, self.create_handler_option)
            worker.daemon = True
            worker.start()
        sketch_queue.join()


class PreProcessThreadWorker(threading.Thread):
    def __init__(self, sketch_queue: Queue, create_handler_option: CreateBaseTraverseHandlerOption):
        super(PreProcessThreadWorker, self).__init__()
        self.sketch_queue = sketch_queue
        self.initial_size = self.sketch_queue.qsize()
        self.create_handler_option = create_handler_option

    def run(self) -> None:
        while True:
            if self.sketch_queue.empty():
                break
            sketch_file_path = self.sketch_queue.get_nowait()
            start_time = time.time_ns()
            try:
                sketch = from_file(sketch_file_path)
                if sketch is not None:
                    ConsoleColor.GREEN.cprint(f"processing sketch {sketch.filepath}")
                    PreProcessEachSketch(
                        sketch, self.create_handler_option.create_instance()).process()
            except Exception as e:
                ConsoleColor.RED.cprint(f"error happened when processing sketch of index {sketch_file_path}")
                ConsoleColor.RED.cprint(str(e))
            end_time = time.time_ns()
            ConsoleColor.MAGENTA.cprint(
                f'finish processing sketch {sketch_file_path} in {(end_time - start_time) / (10 ** 6):.3f} ms')
            self.sketch_queue.task_done()


class PreProcessEachSketch:
    def __init__(self, sketch_file: SketchFile, traverse_handler: BaseTraverseHandler):
        self.sketch_file = sketch_file
        self.traverse_handler = traverse_handler
        self.symbol_master_dict: Dict[Uuid, SymbolMaster] = {}
        self.layer_stack: List[AnyLayer] = []

    def analyze_symbol_master(self) -> None:
        """
        get all symbol master in sketch
        """
        # load foreign symbol master
        for foreign_symbol in self.sketch_file.contents.document.foreignSymbols:
            self.symbol_master_dict[foreign_symbol.symbolMaster.symbolID] = foreign_symbol.symbolMaster
        # load local symbol master
        for page in self.sketch_file.contents.document.pages:
            ConsoleColor.BLUE.cprint(f"[sketch] {self.sketch_file.filepath} finding symbol master in page {page.name}")
            # for each sketch page layer (artboard/symbol master)
            for layer in page.layers:
                if isinstance(layer, SymbolMaster):
                    self.symbol_master_dict[layer.symbolID] = layer

    def process(self) -> None:
        """
        traverse sketch and generate image for each sketch artboard
        """
        self.analyze_symbol_master()
        self.traverse_handler.init_sketch(self.sketch_file)
        # for each sketch page
        for page in self.sketch_file.contents.document.pages:
            ConsoleColor.GREEN.cprint(f"[sketch] {self.sketch_file.filepath} processing page {page.name}")
            # remove all invisible layers
            reduced_page = recursive_remove_layer(page)
            # for each sketch page layer (artboard/symbol master)
            for layer in reduced_page.layers:
                # if the layer is an artboard
                if isinstance(layer, Artboard):
                    ConsoleColor.YELLOW.cprint(f"[sketch] {self.sketch_file.filepath} processing artboard {layer.name}")
                    # print(layer.frame.width)
                    self.layer_stack = []
                    self.traverse_handler.init_artboard(
                        self.sketch_file, page, layer)
                    # traverse the artboard and draw
                    self.traverse(layer, Point(0, 0))
                    self.traverse_handler.finish_artboard()
                    # break # only one artboard
            # break # only one page
        self.traverse_handler.finish_sketch()

    def traverse(self, layer: AnyLayer, parent_xy: Point, transforms: Tuple[Transform, ...] = (),
                 bound_areas: Tuple[BoundArea, ...] = (), opacity: float = 1, tint: Color = None, isKeep: bool = False) -> ClippingMask:
        """
        traverse sketch list and generate image for each sketch artboard
        @param layer: the layer need to be traversed
        @param parent_xy: the parent x and y since all layer"s xy are relative
        @param transforms: the Flip/Rotate inherit from parent
        @param bound_areas: the mask inherit from parent
        @param opacity: the opacity passed from parent
        @param tint: the tint passed from parent
        @return: if layer has ClippingMask, return the calculated mask area
        """
        # if the layer is a page or artboard or symbol master
        if isinstance(layer, Page) or isinstance(layer, Artboard) or isinstance(layer, SymbolMaster):
            # their x axis and y axis are relative to whole page, ignore them
            # traverse the group and draw
            sub_bound_areas = bound_areas + (
                Polygon([[0, 0], [layer.frame.width, 0],
                         [layer.frame.width, layer.frame.height], [0, layer.frame.height]]),)
            self.layer_stack.append(layer)
            for i in layer.layers:
                self.traverse(i, parent_xy, transforms,
                              sub_bound_areas, opacity, tint, isKeep)
            self.layer_stack.pop()
        else:
            # count left top corner point
            xx = parent_xy.x + layer.frame.x
            yy = parent_xy.y + layer.frame.y
            xy = Point(xx, yy)
            # count center point for transformation
            center = Point(xx + layer.frame.width / 2,
                           yy + layer.frame.height / 2)
            # extend inherited transforms
            sub_transforms = transforms
            # since the Rotation is executed before the Flip,
            # and the final transform sequence will be executed reversely,
            # we need to reverse the order of the transforms
            if layer.isFlippedHorizontal or layer.isFlippedVertical:
                # since the Flip can be executed before with one time scale,
                # we put horizontal and vertical flip into single object
                sub_transforms = sub_transforms + \
                                 (Scale.to_flip(layer.isFlippedHorizontal,
                                                layer.isFlippedVertical, center),)
            if layer.rotation != 0:
                # record the rotation angle and the center point
                # the sketch json"s angle is in count-clockwise, but shapely"s angle is in clockwise
                sub_transforms = sub_transforms + \
                                 (Rotation(-layer.rotation, center),)
            sub_opacity = opacity
            if layer.style is not None and layer.style.contextSettings is not None:
                sub_opacity *= layer.style.contextSettings.opacity
            # traverse the group and draw
            if isinstance(layer, Group):
                sub_bound_areas = bound_areas
                group_tint = tint
                if group_tint is None and layer.style is not None and layer.style.fills is not None and len(
                        layer.style.fills) > 0:
                    group_tint = layer.style.fills[len(
                        layer.style.fills) - 1].color
                self.layer_stack.append(layer)
                if self.traverse_handler.if_group_need_handle(layer):
                    isKeep = True
                    transformed_layer = transform_layer(layer, Point(
                        xx, yy), sub_transforms, bound_areas, sub_opacity, group_tint, True)
                    self.traverse_handler.handle_group(
                        transformed_layer, tuple(self.layer_stack))
                for i in layer.layers:
                    clipping_mask = self.traverse(
                        i, xy, sub_transforms, sub_bound_areas, sub_opacity, group_tint, isKeep)
                    # if the layer has a clipping mask, add it to the bound_areas
                    if clipping_mask.hasClippingMask:
                        sub_bound_areas = sub_bound_areas + \
                                          (clipping_mask.mask,)
                    # if the layer break the mask, recover all masks created in this group
                    if i.shouldBreakMaskChain:
                        sub_bound_areas = bound_areas
                self.layer_stack.pop()
            elif isinstance(layer, SymbolInstance) and layer.symbolID in self.symbol_master_dict.keys():
                # scale the symbol master
                sub_transforms = sub_transforms + \
                                 (Scale(layer.scale, layer.scale, Point(xx, yy)),)
                # load real symbol from symbol link
                self.traverse(
                    self.symbol_master_dict[layer.symbolID], xy, sub_transforms, bound_areas,
                    sub_opacity, tint, isKeep)
            else:
                # get bounding box
                transformed_layer = transform_layer(layer, Point(xx, yy), sub_transforms, bound_areas, sub_opacity,
                                                    tint, layer.hasClippingMask or isKeep)
                self.traverse_handler.handle_layer(
                    transformed_layer, tuple(self.layer_stack) + (layer,))
                # return the clipping mask if the layer has ClippingMask and the polygon is not empty
                if layer.hasClippingMask and len(get_polygon_exterior(transformed_layer.bound_area)) > 2:
                    return ClippingMask(True, transformed_layer.bound_area)
        # default return
        return ClippingMask(False)


__all__ = [
    'ClippingMask', 'PreProcess', 'PreProcessEachSketch', 'PreProcessThreadWorker'
]
