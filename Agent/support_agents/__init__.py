"""
Multi-Agent Support System - Support Agents Package
=================================================

This package contains all the intelligent agents that work together
to analyze and route customer support tickets.

Agents:
- PriorityAgent: Analyzes ticket urgency and business impact
- ClassificationAgent: Categorizes tickets and estimates complexity
- RoutingAgent: Makes final routing decisions based on other agents' analysis
"""

from .priority_agent import PriorityAgent
from .classification_agent import ClassificationAgent
from .routing_agent import RoutingAgent
from .ticket_router import TicketRouter
__all__ = [
    'PriorityAgent',
    'ClassificationAgent', 
    'RoutingAgent',
    'TicketRouter'
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'Brunda Somashekhar'
__description__ = 'Multi-agent system for intelligent customer support ticket routing'
