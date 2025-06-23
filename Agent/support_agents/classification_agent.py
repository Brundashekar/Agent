"""
Classification Agent - Categorizes tickets and estimates complexity
================================================================

This agent classifies support tickets into categories and estimates
the complexity and effort required to resolve them.
"""

from enum import Enum
from typing import Dict, Any, List


class TicketCategory(Enum):
    """Categories for support tickets"""
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL_INQUIRY = "general_inquiry"


class Complexity(Enum):
    """Complexity levels for support tickets"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class ClassificationAgent:
    """
    Agent responsible for categorizing tickets and estimating complexity.
    """

    def __init__(self):
        self.name = "ClassificationAgent"
        self.description = "Categorizes tickets and estimates complexity"

        # Category keywords mapping
        self.category_keywords = {
            TicketCategory.TECHNICAL: [
                'api', 'integration', 'code', 'error', 'bug', 'crash', 'timeout',
                'performance', 'database', 'server', 'configuration', 'setup'
            ],
            TicketCategory.BILLING: [
                'invoice', 'payment', 'charge', 'billing', 'subscription', 'refund',
                'price', 'cost', 'upgrade', 'downgrade', 'plan'
            ],
            TicketCategory.ACCOUNT: [
                'login', 'password', 'access', 'permission', 'user', 'account',
                'profile', 'settings', 'authentication', 'authorization'
            ],
            TicketCategory.FEATURE_REQUEST: [
                'feature', 'enhancement', 'improvement', 'suggestion', 'add',
                'new functionality', 'request', 'would like', 'can you add'
            ],
            TicketCategory.BUG_REPORT: [
                'bug', 'issue', 'problem', 'not working', 'broken', 'incorrect',
                'unexpected', 'malfunction', 'glitch'
            ],
            TicketCategory.GENERAL_INQUIRY: [
                'question', 'help', 'how to', 'documentation', 'guide',
                'tutorial', 'information', 'clarification'
            ]
        }

        # Complexity indicators
        self.complexity_indicators = {
            'simple': [
                'password reset', 'basic question', 'documentation',
                'how to', 'simple configuration'
            ],
            'moderate': [
                'integration', 'setup', 'configuration', 'troubleshooting',
                'account issue'
            ],
            'complex': [
                'custom implementation', 'advanced configuration', 'data migration',
                'complex bug', 'system integration'
            ],
            'expert': [
                'architecture', 'performance optimization', 'security',
                'custom development', 'enterprise setup'
            ]
        }

    def classify_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a support ticket into category and complexity.

        Args:
            ticket: Dictionary containing ticket information

        Returns:
            Dictionary with classification results
        """
        content = ticket.get('description', '').lower()
        subject = ticket.get('subject', '').lower()

        # Combine subject and content for analysis
        full_text = f"{subject} {content}"

        # Determine category
        category = self._determine_category(full_text)

        # Determine complexity
        complexity = self._determine_complexity(full_text, category)

        # Estimate effort (in hours)
        effort_hours = self._estimate_effort(complexity)

        return {
            'category': category.value,
            'complexity': complexity.value,
            'estimated_effort_hours': effort_hours,
            'reasoning': self._get_classification_reasoning(category, complexity, full_text),
            'agent': self.name
        }

    def _determine_category(self, text: str) -> TicketCategory:
        """Determine the category of the ticket based on keywords"""
        category_scores = {}

        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            category_scores[category] = score

        # Return category with highest score, default to GENERAL_INQUIRY
        if not category_scores or max(category_scores.values()) == 0:
            return TicketCategory.GENERAL_INQUIRY

        return max(category_scores, key=category_scores.get)

    def _determine_complexity(self, text: str, category: TicketCategory) -> Complexity:
        """Determine the complexity based on text analysis and category"""
        complexity_scores = {}

        for complexity_level, indicators in self.complexity_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text:
                    score += 1
            complexity_scores[complexity_level] = score

        # If no specific indicators found, use category-based defaults
        if not complexity_scores or max(complexity_scores.values()) == 0:
            if category in [TicketCategory.TECHNICAL, TicketCategory.BUG_REPORT]:
                return Complexity.MODERATE
            elif category == TicketCategory.FEATURE_REQUEST:
                return Complexity.COMPLEX
            else:
                return Complexity.SIMPLE

        # Return complexity with highest score
        complexity_name = max(complexity_scores, key=complexity_scores.get)
        return Complexity(complexity_name)

    def _estimate_effort(self, complexity: Complexity) -> float:
        """Estimate effort in hours based on complexity"""
        effort_mapping = {
            Complexity.SIMPLE: 0.5,
            Complexity.MODERATE: 2.0,
            Complexity.COMPLEX: 8.0,
            Complexity.EXPERT: 24.0
        }
        return effort_mapping.get(complexity, 2.0)

    def _get_classification_reasoning(self, category: TicketCategory,
                                      complexity: Complexity, text: str) -> str:
        """Generate reasoning for the classification"""
        reasons = []

        # Category reasoning
        category_keywords_found = []
        for keyword in self.category_keywords.get(category, []):
            if keyword in text:
                category_keywords_found.append(keyword)

        if category_keywords_found:
            reasons.append(f"Category: {category.value} (keywords: {', '.join(category_keywords_found[:3])})")
        else:
            reasons.append(f"Category: {category.value} (default classification)")

        # Complexity reasoning
        complexity_indicators_found = []
        for indicator in self.complexity_indicators.get(complexity.value, []):
            if indicator in text:
                complexity_indicators_found.append(indicator)

        if complexity_indicators_found:
            reasons.append(f"Complexity: {complexity.value} (indicators: {', '.join(complexity_indicators_found[:2])})")
        else:
            reasons.append(f"Complexity: {complexity.value} (category-based)")

        return "; ".join(reasons)