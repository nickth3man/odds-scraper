"""Shared mock Playwright helpers — importable from any test module.

These are NOT pytest fixtures. Use them directly when constructing test data.
"""

from __future__ import annotations

import re


class FakeElement:
    """Unified mock for a Playwright ElementHandle.

    Supports targeted child lookup for the CSS/XPath selector subset used by parser tests.
    """

    def __init__(self, text='', attrs=None, parent=None, children=None):
        self._text = text
        self._attrs = attrs or {}
        self._parent = parent
        self._children = children or []

    def inner_text(self) -> str:
        return self._text

    def get_attribute(self, name: str):
        return self._attrs.get(name)

    def query_selector(self, selector: str):
        """Simulate Playwright query_selector returning None on no match."""
        selector_lower = selector.lower()

        # XPath: simulate ancestor traversal by returning the parent element
        if 'xpath' in selector_lower:
            if 'ancestor' in selector_lower:
                return self._parent
            if '..' in selector:
                return self._parent
            raise RuntimeError('no parent element')

        for child in self._walk_children():
            if child._matches_selector(selector):
                return child
        return None

    def _find_child_by_testid(self, testid: str):
        for child in self._children:
            if child._attrs.get('data-testid') == testid:
                return child
            result = child._find_child_by_testid(testid)
            if result:
                return result
        return None

    def query_selector_all(self, selector: str):
        """Simulate Playwright query_selector_all with basic selector filtering."""
        return [child for child in self._walk_children() if child._matches_selector(selector)]

    def _walk_children(self):
        for child in self._children:
            yield child
            yield from child._walk_children()

    def _matches_selector(self, selector: str) -> bool:
        selector_options = [part.strip() for part in selector.split(',')]
        return any(self._matches_simple_selector(option) for option in selector_options if option)

    def _matches_simple_selector(self, selector: str) -> bool:
        if not selector:
            return False

        selector = selector.split()[-1]
        tag = self._attrs.get('tag')
        if selector in {'a', 'button'}:
            return tag == selector or selector in (self._attrs.get('class') or '')

        data_testid = self._attrs.get('data-testid') or ''
        exact_testid = re.search(r"data-testid=['\"]([^'\"]+)['\"]", selector)
        if exact_testid and data_testid != exact_testid.group(1):
            return False
        partial_testid = re.search(r"data-testid\*=['\"]([^'\"]+)['\"]", selector)
        if partial_testid and partial_testid.group(1) not in data_testid:
            return False

        class_name = self._attrs.get('class') or ''
        partial_classes = re.findall(r"class\*=['\"]([^'\"]+)['\"]", selector)
        if partial_classes and not any(fragment in class_name for fragment in partial_classes):
            return False

        aria_label = self._attrs.get('aria-label') or ''
        partial_aria = re.search(r"aria-label\*=['\"]([^'\"]+)['\"]", selector)
        if partial_aria and partial_aria.group(1) not in aria_label:
            return False

        return bool(exact_testid or partial_testid or partial_classes or partial_aria)


class FakePage:
    """Mock Playwright Page that returns a fixed list of elements."""

    def __init__(self, elements=None, html_content=''):
        self._elements = elements or []
        self._html = html_content

    def content(self) -> str:
        return self._html

    def title(self) -> str:
        return 'DraftKings Test'

    def query_selector_all(self, selector: str):
        return [element for element in self._elements if element._matches_selector(selector)]
