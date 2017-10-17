#!/usr/bin/env python
"""
Guillotine Style 2D Bin Algorithm

Solomon Bothwell
ssbothwell@gmail.com
"""
import operator
import typing
from typing import List
from functools import reduce
from collections import namedtuple
from . import item


class FreeRectangle(typing.NamedTuple('FreeRectangle', [('width', int), ('height', int), ('x', int), ('y', int)])):
    __slots__ = ()
    @property
    def area(self):
        return self.width*self.height


class Guillotine:
    def __init__(self, x: int = 8,
                 y: int = 4,
                 rotation: bool = True,
                 rectangle_merge: bool=False,
                 split_heuristic: str='default') -> None:
        self.x = x
        self.y = y
        self.rMerge = rectangle_merge
        self.split_heuristic = split_heuristic


        if x == 0 or y == 0:
            self.freerects = [] # type: List[FreeRectangle]
        else:
            self.freerects = [FreeRectangle(self.x, self.y, 0, 0)] # type: List[FreeRectangle]
        self.items = [] # type: List[item.Item]
        self.rotation = rotation


    def __repr__(self) -> str:
        return "Guillotine(%r)" % (self.items)


    def _fitted_rects(self, item: item.Item,
                      rotation: bool = False) -> List[FreeRectangle]:
        """
        Returns a list of FreeRectangles that the item fits
        """
        width = item.width if not rotation else item.height
        height = item.height if not rotation else item.width
        return [rect for rect
                in self.freerects
                if rect.width >= width
                and rect.height >= height]


    @staticmethod
    def _split_along_axis(freeRect: FreeRectangle,
                          item: item.Item, split: bool) -> List[FreeRectangle]:
        top_x = freeRect.x
        top_y = freeRect.y + item.height
        top_h = freeRect.height - item.height

        right_x = freeRect.x + item.width
        right_y = freeRect.y
        right_w = freeRect.width - item.width

        # horizontal split
        if split:
            top_w = freeRect.width
            right_h = item.height
        # vertical split
        else:
            top_w = item.width
            right_h = freeRect.height

        result = []

        if right_w > 0 and right_h > 0:
            right_rect = FreeRectangle(right_w, right_h, right_x, right_y)
            result.append(right_rect)

        if top_w > 0 and top_h > 0:
            top_rect = FreeRectangle(top_w, top_h, top_x, top_y)
            result.append(top_rect)

        return result


    def _split_free_rect(self, item: item.Item,
                         freeRect: FreeRectangle) -> List[FreeRectangle]:
        """
        Determines the split axis based upon the split heuristic then calls
        _split_along_axis  with the appropriate axis to return a List[FreeRectangle].
        """

        # Leftover lengths
        w = freeRect.width - item.width
        h = freeRect.height - item.height

        if self.split_heuristic == 'SplitShorterLeftoverAxis': split = (w <= h)
        elif self.split_heuristic == 'SplitLongerLeftoverAxis': split = (w > h)
        elif self.split_heuristic == 'SplitMinimizeArea': split = (item.width * h > w * item.height)
        elif self.split_heuristic == 'SplitMaximizeArea': split = (item.width * h <= w * item.height)
        elif self.split_heuristic == 'SplitShorterAxis': split = (freeRect.width <= freeRect.height)
        elif self.split_heuristic == 'SplitLongerAxis': split = (freeRect.width > freeRect.height)
        else: split = True


        return self._split_along_axis(freeRect, item, split)


    @staticmethod
    def _rectangle_reduce(fitted_rects: List[FreeRectangle],
                          op = operator.lt,
                          field: str = 'width') -> FreeRectangle:
        """
        Reduces a list of FreeRectangles and returns the result
        """
        if fitted_rects:
            if field == 'width':
                compare = lambda a, b: a if op(a.width, b.width) else b
            if field == 'height':
                compare = lambda a, b: a if op(a.height, b.height) else b
            if field == 'area':
                compare = lambda a, b: a if op(a.area, b.area) else b
            return reduce(compare, fitted_rects)
        return None


    @staticmethod
    def _compare_two_freerects(A: FreeRectangle, B: FreeRectangle) -> FreeRectangle:
        """
        Returns the smaller of two FreeRectangles
        """
        if not A and not B:
            return None
        if A and B:
            return min(A, B)
        if A and not B:
            return A
        else:
            return B


    def first_fit(self, item: item.Item) -> bool:
        """
        Select first indexed FreeRectangle (that fits item)
        """
        fitted_rects = self._fitted_rects(item)
        if not fitted_rects and self.rotation:
            fitted_rects = self._fitted_rects(item, rotation=True)
            if fitted_rects:
                item.rotate()
        for freerect in fitted_rects:
            item.CornerPoint = (freerect.x, freerect.y)
            self.items.append(item)
            self.freerects.remove(freerect)

            splits = self._split_free_rect(item, freerect)
            for rect in splits:
                self.freerects.append(rect)
            return True
        return False


    def _generic_algo(self, item, heuristic: str = 'best_width_fit', op = operator.lt, split_heuristic: str='default') -> bool:
        """
        Select FreeRectangle based on heuristic choices
        """
        fitted_rects = self._fitted_rects(item)
        smallest_rect = self._rectangle_reduce(self._fitted_rects(item), op, heuristic)

        if self.rotation:
            fitted_rects_rot = self._fitted_rects(item, rotation=True)
            smallest_rotated = self._rectangle_reduce(fitted_rects_rot, op, heuristic)
            best = self._compare_two_freerects(smallest_rect, smallest_rotated)
            if best == smallest_rotated:
                item.rotate()
        else:
            best = smallest_rect
        if best:
            item.CornerPoint = (best.x, best.y)
            self.items.append(item)
            self.freerects.remove(best)

            splits = self._split_free_rect(item, best)
            for rect in splits:
                self.freerects.append(rect)
            return True
        return False


    def rectangle_merge(self) -> None:
        """
        Rectangle Merge optimization
        Finds pairs of free rectangles and merges them if they are mergable.
        """
        for freerect in self.freerects:
            matching_widths = list(filter(lambda r: (r.width == freerect.width and
                                                     r.x == freerect.x) and
                                                     r != freerect, self.freerects))
            matching_heights = list(filter(lambda r: (r.height == freerect.height and
                                                      r.y == freerect.y) and
                                                      r != freerect, self.freerects))

            if matching_widths:
                widths_adjacent = list(filter(lambda r: r.y == freerect.y + freerect.height, self.freerects)) # type: List[FreeRectangle]

                if widths_adjacent:
                    match_rect = widths_adjacent[0]
                    merged_rect = FreeRectangle(freerect.width,
                                                freerect.height+match_rect.height,
                                                freerect.x,
                                                freerect.y)
                    self.freerects.remove(freerect)
                    self.freerects.remove(match_rect)
                    self.freerects.append(merged_rect)

            if matching_heights:
                heights_adjacent = list(filter(lambda r: r.x == freerect.x + freerect.width, self.freerects))
                if heights_adjacent:
                    match_rect = heights_adjacent[0]
                    merged_rect = FreeRectangle(freerect.width+match_rect.width,
                                                freerect.height,
                                                freerect.x,
                                                freerect.y)
                    self.freerects.remove(freerect)
                    self.freerects.remove(match_rect)
                    self.freerects.append(merged_rect)


    def insert(self, item: item.Item, heuristic: str = 'best_area_fit', split_heuristic='default') -> bool:
        """
        Public method for selecting heuristic and inserting item
        """
        if heuristic == 'first_fit':
            res = self.first_fit(item)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        elif heuristic == 'best_width_fit':
            res = self._generic_algo(item, 'width', operator.lt, split_heuristic)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        elif heuristic == 'best_height_fit':
            res = self._generic_algo(item, 'height', operator.lt, split_heuristic)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        elif heuristic == 'best_area_fit':
            res = self._generic_algo(item, 'area', operator.lt, split_heuristic)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        elif heuristic == 'worst_width_fit':
            res = self._generic_algo(item, 'width', operator.gt, split_heuristic)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        elif heuristic == 'worst_height_fit':
            res = self._generic_algo(item, 'height', operator.gt, split_heuristic)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        elif heuristic == 'worst_area_fit':
            res = self._generic_algo(item, 'area', operator.gt, split_heuristic)
            if res:
                if self.rMerge:
                    self.rectangle_merge()
                return True
        return False


    def bin_stats(self) -> dict:
        """
        Returns a dictionary with compiled stats on the bin tree
        """

        stats = {
            'width': self.x,
            'height': self.y,
            'area': self.x * self.y,
            'efficiency': 1-(sum([F.width*F.height for F in self.freerects])/(self.x*self.y)),
            'items': self.items,
            }

        return stats
