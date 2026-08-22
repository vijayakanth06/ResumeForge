"""UI package for ATS Benchmark."""
from .entry_page import render_entry_page
from .dataset_page import render_dataset_page
from .analysis_page import render_analysis_page

__all__ = [
    "render_entry_page",
    "render_dataset_page",
    "render_analysis_page",
]
