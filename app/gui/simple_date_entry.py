"""
app/gui/simple_date_entry.py - Simple date input widget (no calendar popup)

Provides a date field as a plain Entry in DD/MM/YYYY format to avoid locale/encoding
issues with calendar popups (e.g. month names showing as "??????"). Compatible
with existing code that uses .entry.get() or .get().
"""

from datetime import date
import ttkbootstrap as ttk
from ttkbootstrap.constants import LEFT, X, YES


class SimpleDateEntry(ttk.Frame):
    """A date input that is just an Entry with DD/MM/YYYY format.
    No calendar popup — user types the date. Exposes .entry and .get() for compatibility.
    """

    def __init__(self, master=None, default_date=None, width=12, bootstyle="", **kwargs):
        super().__init__(master, **kwargs)
        self._default = default_date or date.today()
        self.entry = ttk.Entry(self, width=width, bootstyle=bootstyle or None)
        self.entry.pack(side=LEFT, fill=X, expand=YES)
        self._set_default()

    def _set_default(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self._default.strftime("%d/%m/%Y"))

    def get(self):
        return self.entry.get().strip()

    def set_date(self, d):
        if hasattr(d, "strftime"):
            self._default = d if isinstance(d, date) else d.date()
        self._set_default()
