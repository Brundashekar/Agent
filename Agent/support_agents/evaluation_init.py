"""
Evaluation Package - Test Cases and Metrics
==========================================

This package contains test cases and evaluation metrics for the
multi-agent support system.
"""

from .test_cases import get_test_tickets
from .metrics import RoutingMetrics

__all__ = ['get_test_tickets', 'RoutingMetrics']
