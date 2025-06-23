"""
Classification Agent - Technical Categorization and Complexity Analysis
======================================================================

This agent analyzes customer support tickets to determine:
- Technical category (API, Security, UI, Feature, General)
- Complexity score (1-10 scale)
- Estimated resolution time
- Required expertise and skills
"""

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ClassificationAnalysis:
    """Data structure for classification analysis results."""
    category: str
    complexity_score: int
    estimated_resolution_time: int
    required_expertise: List[str]
    reasoning: str

class ClassificationAgent:
    """
    Agent responsible for technical classification of support tickets.
    Uses keyword analysis and pattern matching to categorize issues
    and estimate technical complexity.
    """
    
    def __init__(self):
        """Initialize classification rules and categories."""
        self.category_rules = {
            'API': {
                'keywords': ['api', 'rate limit', 'integration', 'endpoint', 'webhook', 'authentication', 'oauth'],
                'complexity': 6,
                'expertise': ['backend', 'api'],
                'resolution_time': 4
            },
            'Security': {
                'keywords': ['security', 'vulnerability', 'paths', 'risk', 'breach', 'unauthorized', 'exploit'],
                'complexity': 8,
                'expertise': ['security', 'backend'],
                'resolution_time': 8
            },
            'UI': {
                'keywords': ['ui', 'dashboard', 'mobile', 'interface', 'design', 'layout', 'responsive'],
                'complexity': 4,
                'expertise': ['frontend', 'design'],
                'resolution_time': 2
            },
            'Feature': {
                'keywords': ['feature', 'export', 'functionality', 'enhancement', 'improvement', 'request'],
                'complexity': 5,
                'expertise': ['product', 'engineering'],
                'resolution_time': 12
            },
            'General': {
                'keywords': ['login', 'password', 'account', 'basic', 'help', 'question'],
                'complexity': 3,
                'expertise': ['support'],
                'resolution_time': 1
            }
        }
    
    def analyze(self, ticket: Dict[str, Any]) -> ClassificationAnalysis:
        """
        Classify ticket and analyze technical complexity.
        
        Args:
            ticket: Dictionary containing ticket information
            
        Returns:
            ClassificationAnalysis object with category and complexity
        """
        subject = ticket.get('subject', '').lower()
        message = ticket.get('message', '').lower()
        combined_text = f"{subject} {message}"
        
        # Find matching category
        category_scores = {}
        for category, rules in self.category_rules.items():
            score = 0
            for keyword in rules['keywords']:
                if keyword in combined_text:
                    score += 1
            category_scores[category] = score
        
        # Determine best matching category
        if max(category_scores.values()) == 0:
            # No keywords matched, default to General
            best_category = 'General'
        else:
            best_category = max(category_scores, key=category_scores.get)
        
        # Get category details
        category_info = self.category_rules[best_category]
        
        # Adjust complexity based on ticket specifics
        base_complexity = category_info['complexity']
        complexity_adjustments = 0
        
        # Check for complexity indicators
        complex_indicators = ['multiple', 'several', 'various', 'complex', 'advanced', 'custom']
        for indicator in complex_indicators:
            if indicator in combined_text:
                complexity_adjustments += 1
                break
        
        # Check for simplicity indicators
        simple_indicators = ['simple', 'basic', 'quick', 'minor', 'small']
        for indicator in simple_indicators:
            if indicator in combined_text:
                complexity_adjustments -= 1
                break
        
        # Customer tier can affect complexity handling
        customer_tier = ticket.get('customer_tier', 'free')
        if customer_tier == 'enterprise' and best_category != 'General':
            complexity_adjustments += 1  # Enterprise customers often have more complex setups
        
        # Calculate final complexity
        final_complexity = max(1, min(10, base_complexity + complexity_adjustments))
        
        # Adjust resolution time based on complexity
        base_resolution = category_info['resolution_time']
        if final_complexity > base_complexity:
            adjusted_resolution = int(base_resolution * 1.5)
        elif final_complexity < base_complexity:
            adjusted_resolution = max(1, int(base_resolution * 0.7))
        else:
            adjusted_resolution = base_resolution
        
        # Generate reasoning
        matched_keywords = [kw for kw in category_info['keywords'] if kw in combined_text]
        reasoning = f"Categorized as {best_category}"
        if matched_keywords:
            reasoning += f" (keywords: {', '.join(matched_keywords[:3])})"
        reasoning += f". Complexity {final_complexity}/10 based on technical requirements."
        
        return ClassificationAnalysis(
            category=best_category,
            complexity_score=final_complexity,
            estimated_resolution_time=adjusted_resolution,
            required_expertise=category_info['expertise'].copy(),
            reasoning=reasoning
        )
    
    def get_supported_categories(self) -> Dict[str, Dict[str, Any]]:
        """Return information about supported categories."""
        return {
            category: {
                'description': self._get_category_description(category),
                'typical_complexity': rules['complexity'],
                'required_skills': rules['expertise'],
                'avg_resolution_hours': rules['resolution_time']
            }
            for category, rules in self.category_rules.items()
        }
    
    def _get_category_description(self, category: str) -> str:
        """Get human-readable description for a category."""
        descriptions = {
            'API': 'API integration issues, rate limiting, authentication problems',
            'Security': 'Security vulnerabilities, access control, data protection',
            'UI': 'User interface issues, design problems, mobile responsiveness',
            'Feature': 'Feature requests, enhancements, new functionality',
            'General': 'Basic support questions, account issues, general help'
        }
        return descriptions.get(category, 'General support category')
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Return information about this agent's capabilities."""
        return {
            'name': 'Classification Agent',
            'purpose': 'Categorize tickets and assess technical complexity',
            'outputs': ['category', 'complexity_score', 'estimated_resolution_time', 'required_expertise'],
            'supported_categories': list(self.category_rules.keys()),
            'complexity_factors': [
                'Keyword analysis and pattern matching',
                'Technical complexity indicators',
                'Customer tier considerations',
                'Issue scope assessment'
            ]
        }
