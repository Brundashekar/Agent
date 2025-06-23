"""
Test Cases for Multi-Agent Support System
========================================

This module contains realistic test cases that demonstrate
various routing scenarios and edge cases.
"""

from typing import List, Dict, Any

def get_test_tickets() -> List[Dict[str, Any]]:
    """
    Return a comprehensive set of test tickets covering various scenarios.
    
    Returns:
        List of ticket dictionaries for testing the routing system
    """
    return [
        {
            "ticket_id": "SUP-001",
            "customer_tier": "free",
            "subject": "This product is completely broken!!!",
            "message": "Nothing works! I can't even log in. This is the worst software I've ever used. I'm switching to a competitor!",
            "previous_tickets": 0,
            "monthly_revenue": 0,
            "account_age_days": 2,
            "expected_outcome": {
                "queue": "L1_GENERAL",
                "priority": "MEDIUM",
                "reasoning": "Free tier customer with emotional language, but basic login issue"
            }
        },
        {
            "ticket_id": "SUP-002", 
            "customer_tier": "enterprise",
            "subject": "Minor UI issue with dashboard",
            "message": "Hi team, just noticed the dashboard numbers are slightly misaligned on mobile view. Not urgent, but wanted to report it.",
            "previous_tickets": 15,
            "monthly_revenue": 25000,
            "account_age_days": 730,
            "expected_outcome": {
                "queue": "L2_TECHNICAL",
                "priority": "HIGH",
                "reasoning": "Enterprise customer with high revenue deserves prioritized attention"
            }
        },
        {
            "ticket_id": "SUP-003",
            "customer_tier": "premium", 
            "subject": "Feature Request: Bulk export",
            "message": "We need bulk export functionality for our quarterly reports. Currently exporting one by one is very time consuming.",
            "previous_tickets": 5,
            "monthly_revenue": 5000,
            "account_age_days": 400,
            "expected_outcome": {
                "queue": "L3_ENGINEERING",
                "priority": "MEDIUM",
                "reasoning": "Feature request requires engineering team"
            }
        },
        {
            "ticket_id": "SUP-004",
            "customer_tier": "premium",
            "subject": "API rate limits unclear", 
            "message": "Getting rate limited but documentation says we should have 1000 requests/hour. We're only making ~200/hour. Please clarify.",
            "previous_tickets": 8,
            "monthly_revenue": 3000,
            "account_age_days": 180,
            "expected_outcome": {
                "queue": "L2_API_TEAM",
                "priority": "MEDIUM",
                "reasoning": "API-specific issue requiring specialized knowledge"
            }
        },
        {
            "ticket_id": "SUP-005",
            "customer_tier": "enterprise",
            "subject": "Urgent: Security vulnerability?",
            "message": "Our security team flagged that your API responses include internal server paths in error messages. This could be a security risk.",
            "previous_tickets": 20,
            "monthly_revenue": 50000,
            "account_age_days": 900,
            "expected_outcome": {
                "queue": "SECURITY_TEAM",
                "priority": "CRITICAL",
                "reasoning": "Security issue from high-value customer requires immediate attention"
            }
        },
        {
            "ticket_id": "SUP-006",
            "customer_tier": "free",
            "subject": "Simple question about account",
            "message": "Hi, I just wanted to know how to change my password. Thanks!",
            "previous_tickets": 0,
            "monthly_revenue": 0,
            "account_age_days": 45,
            "expected_outcome": {
                "queue": "L1_GENERAL", 
                "priority": "LOW",
                "reasoning": "Basic account question with low complexity"
            }
        },
        {
            "ticket_id": "SUP-007",
            "customer_tier": "premium",
            "subject": "Mobile app interface problems",
            "message": "The mobile interface is not responsive on tablets. Buttons are too small and text is cut off.",
            "previous_tickets": 3,
            "monthly_revenue": 2000,
            "account_age_days": 120,
            "expected_outcome": {
                "queue": "L2_TECHNICAL",
                "priority": "MEDIUM", 
                "reasoning": "UI issue requiring frontend expertise"
            }
        },
        {
            "ticket_id": "SUP-008",
            "customer_tier": "enterprise",
            "subject": "Critical: Integration completely down",
            "message": "Our webhook integration stopped working 2 hours ago. This is blocking our production deployment. We need immediate assistance!",
            "previous_tickets": 12,
            "monthly_revenue": 35000,
            "account_age_days": 600,
            "expected_outcome": {
                "queue": "ESCALATION",
                "priority": "CRITICAL",
                "reasoning": "Production-blocking issue for high-value enterprise customer"
            }
        }
    ]

def get_edge_case_tickets() -> List[Dict[str, Any]]:
    """
    Return edge case tickets for testing system robustness.
    
    Returns:
        List of edge case ticket dictionaries
    """
    return [
        {
            "ticket_id": "EDGE-001",
            "customer_tier": "enterprise",
            "subject": "",  # Empty subject
            "message": "help",  # Minimal message
            "previous_tickets": 0,
            "monthly_revenue": 100000,
            "account_age_days": 1
        },
        {
            "ticket_id": "EDGE-002", 
            "customer_tier": "free",
            "subject": "URGENT URGENT URGENT SECURITY VULNERABILITY API BROKEN!!!",
            "message": "Everything is broken! API, UI, security, features - nothing works! This is terrible!",
            "previous_tickets": 50,  # Excessive ticket history
            "monthly_revenue": 0,
            "account_age_days": 5000  # Very old account
        },
        {
            "ticket_id": "EDGE-003",
            "customer_tier": "premium",
            "subject": "Complex multi-category issue",
            "message": "Our API integration has a security vulnerability in the UI dashboard that's blocking a critical feature we need. This affects our mobile app too.",
            "previous_tickets": 25,
            "monthly_revenue": 15000,
            "account_age_days": 365
        }
    ]

def get_performance_test_tickets(count: int = 100) -> List[Dict[str, Any]]:
    """
    Generate a large set of tickets for performance testing.
    
    Args:
        count: Number of test tickets to generate
        
    Returns:
        List of generated test tickets
    """
    import random
    
    tiers = ["free", "premium", "enterprise"]
    categories = ["login", "api", "ui", "feature", "security", "general"]
    
    tickets = []
    for i in range(count):
        tier = random.choice(tiers)
        category = random.choice(categories)
        
        # Generate realistic data based on tier
        if tier == "enterprise":
            revenue = random.randint(10000, 100000)
        elif tier == "premium":
            revenue = random.randint(1000, 15000)
        else:
            revenue = 0
            
        tickets.append({
            "ticket_id": f"PERF-{i+1:03d}",
            "customer_tier": tier,
            "subject": f"Test {category} issue #{i+1}",
            "message": f"This is a test {category} issue for performance testing.",
            "previous_tickets": random.randint(0, 30),
            "monthly_revenue": revenue,
            "account_age_days": random.randint(1, 2000)
        })
    
    return tickets
