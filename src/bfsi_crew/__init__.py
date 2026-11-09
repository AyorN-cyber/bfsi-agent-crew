"""bfsi-agent-crew: a multi-agent loan application review demo built on CrewAI."""

from .models import Application, ReviewReport
from .pipeline import run_review
from .rag import PolicyIndex

__all__ = ["Application", "PolicyIndex", "ReviewReport", "run_review"]
__version__ = "0.1.0"
