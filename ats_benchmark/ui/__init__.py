"""UI package for ATS Benchmark."""
from .entry_page import render_entry_page
from .dataset_page import render_dataset_page
from .analysis_page import render_analysis_page
from .paper_figures import render_paper_figures

__all__ = [
    "render_entry_page",
    "render_dataset_page",
    "render_analysis_page",
    "render_paper_figures",
]
