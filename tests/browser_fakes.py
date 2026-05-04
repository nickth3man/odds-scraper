"""Shared mock Playwright helpers — importable from any test module.

These are NOT pytest fixtures. Use them directly when constructing test data.
"""

from __future__ import annotations

import re


class FakeElement:
    """Unified mock for a Playwright ElementHandle.

    Supports child lookup by data-testid (CSS selector) and parent traversal (XPath).
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

        # CSS selector: look up a child by data-testid attribute
        match = re.search(r"data-testid='([^']+)'", selector)
        if match:
            found = self._find_child_by_testid(match.group(1))
            if found:
                return found

        return self._children[0] if self._children else None

    def _find_child_by_testid(self, testid: str):
        for child in self._children:
            if child._attrs.get('data-testid') == testid:
                return child
            result = child._find_child_by_testid(testid)
            if result:
                return result
        return None

    def query_selector_all(self, selector: str):
        """Simulate Playwright query_selector_all returning children list."""
        return self._children


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
        return self._elements
