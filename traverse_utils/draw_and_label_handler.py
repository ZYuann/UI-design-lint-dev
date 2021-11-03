# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import AnyStr, List, Tuple

import numpy as np
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry.base import BaseMultipartGeometry, BaseGeometry

from sketch_utils import SketchFile, Page, Artboard, AnyLayer, Group
from .base_traverse_handler import BaseTraverseHandler
from .layer_transform import LayerTransformed, get_polygon_exterior

LabelPoint = Tuple[float, float, float, float]


@dataclass
class ImageObject:
    """
    A class that store image.
    """
    image: Image.Image
    path: str

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.image.save(self.path)


@dataclass
class DrawAndLabelHandlerOption:
    """
    An option class for :py:class:`DrawAndLabelHandler`.
    """
    color_list: List[List[int]]
    cache_folder_name: str = '.cache'
    images_folder_name: str = 'images'
    labels_folder_name: str = 'labels'
    generate_default_image: bool = True
    generate_flatten_list: bool = True
    generate_label_list: bool = True
    generate_labeled_image: bool = False


class DrawAndLabelHandler(BaseTraverseHandler):
    image_object: ImageObject
    sketch_tool_subprocess: subprocess.Popen

    cache_dir: str = None
    sketch_tool_subprocess_result: List[str] = None
    label_list: List[LabelPoint] = []
    flatten_list: List[LayerTransformed] = []
    count: int = 0
    scale: float = 1

    def __init__(self, options: DrawAndLabelHandlerOption):
        self.color_list = options.color_list
        self.options = options

    def init_sketch(self, sketch_file: SketchFile):
        if self.options.generate_default_image:
            self.cache_dir = os.path.join(
                self.options.cache_folder_name, sketch_file.contents.document.do_objectID)
            os.makedirs(self.cache_dir, exist_ok=True)
            self.sketch_tool_subprocess = subprocess.Popen(
                ["/Applications/Sketch.app/Contents/MacOS/sketchtool",
                 "export",
                 "artboards",
                 sketch_file.filepath,
                 f"--output={self.cache_dir}",
                 "--use-id-for-name",
                 "--overwriting"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

    def init_artboard(self, sketch_file: SketchFile, page: Page, artboard: Artboard) -> None:
        self.count = 0
        # create a new image
        image = Image.new(
            "RGBA", (int(artboard.frame.width * self.scale), int(artboard.frame.height * self.scale)), "white")
        self.image_object = ImageObject(image, f"{artboard.do_objectID}")
        if self.options.generate_label_list:
            self.label_list = []
        if self.options.generate_flatten_list:
            self.flatten_list = []

    def handle_layer(self, layer: LayerTransformed, layer_stack: Tuple[AnyLayer, ...]) -> None:
        sub_image = self.image_object.image
        # create an ImageDraw object
        image_draw = ImageDraw.Draw(sub_image, sub_image.mode)
        # opacity is not 1 means need to do alpha composite
        if layer.opacity != 1:
            # create new image
            sub_image = Image.new(
                sub_image.mode, sub_image.size)
            # create a ImageDraw object
            image_draw = ImageDraw.Draw(sub_image, sub_image.mode)
        # if intersection result is a multipart geometry (for only mask operation is a very rare situation)
        if isinstance(layer.bound_area, BaseMultipartGeometry):
            # draw each geometry instance
            for geom in layer.bound_area.geoms:
                self.draw_polygon(geom, image_draw, layer.opacity)
        # if intersection result is single geometry
        elif isinstance(layer.bound_area, BaseGeometry):
            # draw the geometry instance
            self.draw_polygon(layer.bound_area, image_draw, layer.opacity)
        # opacity is not 1 means need to do alpha composite
        if layer.opacity != 1:
            self.image_object.image = Image.alpha_composite(
                self.image_object.image, sub_image)
        # if need to generate flatten list, append computed geometry to flatten_list
        if self.options.generate_flatten_list:
            self.flatten_list.append(layer)

    def if_group_need_handle(self, group: Group) -> bool:
        # only process group contains '#merge#' keyword
        return "#merge#" in group.name

    def handle_group(self, layer: LayerTransformed, layer_stack: Tuple[AnyLayer, ...]) -> None:
        # the group matched 'if_group_need_handle' result
        if self.options.generate_label_list:
            # get exterior coord of the layer polygon
            exterior = get_polygon_exterior(layer.bound_area)
            if len(exterior) > 2:
                # generate left top corner and right bottom corner points' axes of bounding box
                min_x = min([point[0] for point in exterior])
                max_x = max([point[0] for point in exterior])
                min_y = min([point[1] for point in exterior])
                max_y = max([point[1] for point in exterior])
                self.label_list.append((min_x, min_y, max_x, max_y))

    def finish_artboard(self) -> None:
        if self.options.generate_label_list and self.label_list is not None and len(self.label_list) > 0:
            self.split_and_label()
        if self.options.generate_flatten_list:
            pass
            # TODO: split flatten list in z axis
            # print(
            #     "\n".join(map(lambda x: f"{x.origin.name}:{x.bound_area}", self.flatten_list)))

    def finish_sketch(self) -> None:
        if self.options.generate_default_image and self.cache_dir is not None:
            shutil.rmtree(self.cache_dir, ignore_errors=True)

    def split_and_label(self, aspect_ratio: float = 1):
        """
        split current image and label list and save to file
        @param aspect_ratio: the aspect ratio of split image
        """
        # check if result folder exists
        if not os.path.exists(self.options.images_folder_name):
            os.makedirs(self.options.images_folder_name, exist_ok=True)
        if not os.path.exists(self.options.labels_folder_name):
            os.makedirs(self.options.labels_folder_name, exist_ok=True)
        sketch_tool_image = self.image_object.image
        if self.options.generate_default_image:
            if not self.check_sketch_tool_success(self.image_object.path):
                return
            sketch_tool_image = Image.open(os.path.join(self.cache_dir, self.image_object.path + '.png'))
            sketch_tool_image = sketch_tool_image.resize(
                self.image_object.image.size)
        height = self.image_object.image.height
        width = self.image_object.image.width
        # calculate split images' width and height
        single_image_width = width
        single_image_height = int(width / aspect_ratio)
        # calculate image need to process
        total = height / single_image_height
        box_range: List[Tuple[float, float]] = [
            (0, float(y)) for y in np.arange(0, total, step=0.5)]
        if total < 1:
            # re-calculate split images' width and height
            single_image_width = int(height * aspect_ratio)
            single_image_height = height
            # calculate image need to process
            total = width / single_image_width
            box_range = [(float(x), 0) for x in np.arange(0, total, step=0.5)]
        # using step in 0.5 to avoid splitting labeled object
        for (x, y) in box_range:
            # calculate crop box in order: (left, top, right, bottom)
            img_box = (math.floor(single_image_width * x),
                       math.floor(single_image_height * y),
                       math.floor(min(single_image_width * (x + 1), width)),
                       math.floor(min(single_image_height * (y + 1), height)))
            # calculate image and label file basename
            file_basename = f'{self.image_object.path}-{aspect_ratio}-{x}-{y}'
            labels = list(map(
                # convert (left, top, right, bottom) to (x_center, y_center, width, height) format
                # remember to multiply scale to match real pixel
                lambda points: " ".join(
                    ["0"] + list(map(lambda float_value: "{:.6f}".format(float_value),
                                     [((points[0] + points[2]) / 2 * self.scale - math.floor(
                                         single_image_width * x)) / single_image_width,
                                      ((points[1] + points[3]) / 2 * self.scale - math.floor(
                                          single_image_height * y)) / single_image_height,
                                      ((points[2] - points[0]) * self.scale) / single_image_width,
                                      ((points[3] - points[1]) * self.scale) / single_image_height]))
                ) + "\n",
                # filter label in crop box
                filter(
                    lambda target_label:
                    img_box[0] <= target_label[0] * self.scale and img_box[1] <= target_label[1] * self.scale and
                    img_box[2] >= target_label[2] * \
                    self.scale and img_box[3] >= target_label[3] * \
                    self.scale,
                    self.label_list
                )))
            if len(labels) > 0:
                if not os.path.exists(os.path.join(self.options.images_folder_name, file_basename)):
                    os.makedirs(os.path.join(self.options.images_folder_name, file_basename), exist_ok=True)
                # crop and save cropped image
                filled_image = Image.new(self.image_object.image.mode, (single_image_width, single_image_height),
                                         "white")
                filled_image.paste(
                    self.image_object.image.crop(img_box), (0, 0))
                filled_image.save(os.path.join(
                    self.options.images_folder_name, file_basename, 'filled.png'))
                if self.options.generate_default_image:
                    default_image = Image.new(sketch_tool_image.mode, (single_image_width, single_image_height),
                                              "white")
                    default_image.paste(
                        sketch_tool_image.crop(img_box), (0, 0))
                    default_image.save(os.path.join(
                        self.options.images_folder_name, file_basename, 'default.png'))
                # save label txt file
                with open(os.path.join(self.options.labels_folder_name, file_basename + '.txt'), 'w+') as label_file:
                    label_file.writelines(labels)
                # generate labeled image
                if self.options.generate_labeled_image:
                    generate_label(os.path.join(self.options.images_folder_name, file_basename, 'filled.png'),
                                   os.path.join(self.options.labels_folder_name, file_basename + '.txt'))
                    if self.options.generate_default_image:
                        generate_label(os.path.join(self.options.images_folder_name, file_basename, 'default.png'),
                                       os.path.join(self.options.labels_folder_name, file_basename + '.txt'))

    def draw_polygon(self, polygon: BaseGeometry, image_draw: ImageDraw.ImageDraw, opacity: float):
        # count for coloring
        self.count += 1
        # scale the polygon to match the image size
        scaled = affinity.scale(polygon, xfact=self.scale,
                                yfact=self.scale, origin=(0, 0))
        # if coord > 2, the polygon is not empty
        coords = get_polygon_exterior(scaled)
        if len(coords) > 2:
            # draw the polygon
            image_draw.polygon(coords,
                               # set the fill color
                               # TODO: add support for gradient fill
                               fill=(self.color_list[0][self.count],
                                     self.color_list[1][self.count],
                                     self.color_list[2][self.count],
                                     int(opacity * 255)))

    def check_sketch_tool_success(self, artboard_id: str) -> bool:
        if self.sketch_tool_subprocess is None:
            return False
        elif self.sketch_tool_subprocess.poll() is None:
            self.sketch_tool_subprocess.wait()
        if self.sketch_tool_subprocess_result is None:
            byte_stdout: AnyStr = self.sketch_tool_subprocess.stdout.read()
            self.sketch_tool_subprocess_result = list(
                map(
                    lambda x: x.lstrip("Exported ").rstrip(".png"),
                    filter(
                        lambda x: len(x) > 0,
                        byte_stdout.decode().split('\n')
                    )
                )
            )
        return artboard_id in self.sketch_tool_subprocess_result


def generate_label(image_path: str, label_path: str, width: int = 3) -> None:
    """
    generate labeled image with given image path and label path
    @param image_path: the path of image need to be labeled
    @param label_path: the path of label list
    @param width: the label frame border width
    """
    with open(label_path, 'r') as label_fp:
        # read label list from file
        label_list: List[LabelPoint] = [
            (float(x.split(" ")[1]), float(x.split(" ")[2]),
             float(x.split(" ")[3]), float(x.split(" ")[4]))
            for x in label_fp.readlines()]
        image = Image.open(image_path)
        h, w = image.size
        image_draw = ImageDraw.Draw(image)
        for label in label_list:
            # draw label
            image_draw.rectangle(
                [(label[0] - label[2] / 2) * w, (label[1] - label[3] / 2) * h, (label[0] + label[2] / 2) * w,
                 (label[1] + label[3] / 2) * h],
                fill=None, outline="red", width=width)
        # save labeled image
        image.save(os.path.splitext(image_path)[
                       0] + '-labeled' + os.path.splitext(image_path)[1])


__all__ = [
    'LabelPoint', 'ImageObject', 'DrawAndLabelHandlerOption', 'DrawAndLabelHandler', 'generate_label'
]

if __name__ == '__main__':
    pass
