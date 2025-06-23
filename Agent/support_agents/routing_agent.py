"""
Routing Agent - Makes final routing decisions based on other agents' analysis
Enhanced with summary statistics tracking and corrected evaluation metrics
"""

from collections import defaultdict, Counter
import json
import statistics

class RoutingAgent:
    """
    Agent responsible for making final routing decisions based on
    priority analysis and classification results.
    Enhanced with statistics tracking capabilities and corrected metrics.
    """

    def __init__(self):
        # Define available teams and their capabilities
        self.teams = {
            'Level1_Support': {
                'categories': ['General', 'Account', 'bug_report'],
                'max_complexity': 'low',
                'max_priority': 'Medium',
                'capacity': 10
            },
            'Level2_Technical': {
                'categories': ['Technical', 'Feature Request', 'bug_report'],
                'max_complexity': 'medium',
                'max_priority': 'High',
                'capacity': 5
            },
            'Level3_Engineering': {
                'categories': ['Technical', 'bug_report'],
                'max_complexity': 'high',
                'max_priority': 'Critical',
                'capacity': 3
            },
            'Billing_Team': {
                'categories': ['Billing'],
                'max_complexity': 'medium',
                'max_priority': 'High',
                'capacity': 4
            },
            'Security_Team': {
                'categories': ['Technical', 'bug_report'],
                'keywords': ['security', 'breach', 'vulnerability'],
                'max_complexity': 'high',
                'max_priority': 'Critical',
                'capacity': 2
            }
        }

        # Priority levels (for comparison)
        self.priority_levels = {
            'low': 1,
            'Low': 1,
            'medium': 2,
            'Medium': 2,
            'high': 3,
            'High': 3,
            'critical': 4,
            'Critical': 4
        }

        # Complexity levels (for comparison)
        self.complexity_levels = {
            'low': 1,
            'simple': 1,
            'medium': 2,
            'moderate': 2,
            'high': 3,
            'complex': 3
        }

        # Statistics tracking
        self.routing_stats = {
            'total_tickets': 0,
            'team_assignments': defaultdict(int),
            'category_distribution': defaultdict(int),
            'priority_distribution': defaultdict(int),
            'complexity_distribution': defaultdict(int),
            'sla_distribution': defaultdict(int),
            'security_tickets': 0,
            'fallback_assignments': 0,
            'routing_decisions': []
        }

    def route_ticket(self, ticket, priority_analysis, classification_analysis):
        """
        Make routing decision based on priority and classification analysis.

        Args:
            ticket (dict): Original ticket
            priority_analysis (dict): Results from PriorityAgent
            classification_analysis (dict): Results from ClassificationAgent

        Returns:
            dict: Routing decision with team assignment and reasoning
        """
        # Safely extract values with fallbacks
        category = classification_analysis.get('category', 'General')
        complexity = classification_analysis.get('complexity', 'medium')

        # Handle both 'priority' and 'priority_level' keys
        priority_level = priority_analysis.get('priority_level') or priority_analysis.get('priority', 'medium')

        # Normalize priority level to title case
        priority_level = priority_level.title()

        print(f"Debug - Category: {category}, Complexity: {complexity}, Priority: {priority_level}")

        # Track statistics
        self.routing_stats['total_tickets'] += 1
        self.routing_stats['category_distribution'][category] += 1
        self.routing_stats['priority_distribution'][priority_level] += 1
        self.routing_stats['complexity_distribution'][complexity] += 1

        # Check for security-related tickets first
        content = f"{ticket.get('title', '')} {ticket.get('description', '')}".lower()
        is_security = any(keyword in content for keyword in self.teams['Security_Team']['keywords'])

        if is_security:
            self.routing_stats['security_tickets'] += 1
            routing_decision = self._create_routing_decision(
                'Security_Team',
                'Security-related ticket detected',
                priority_analysis,
                classification_analysis,
                priority_level,
                complexity
            )
        else:
            # Find suitable teams based on category, complexity, and priority
            suitable_teams = []

            for team_name, team_info in self.teams.items():
                if team_name == 'Security_Team':  # Already handled above
                    continue

                # Check category match
                if category not in team_info['categories']:
                    continue

                # Check complexity capability
                team_max_complexity = self.complexity_levels.get(team_info['max_complexity'], 2)
                ticket_complexity = self.complexity_levels.get(complexity, 2)
                if ticket_complexity > team_max_complexity:
                    continue

                # Check priority capability
                team_max_priority = self.priority_levels.get(team_info['max_priority'], 2)
                ticket_priority = self.priority_levels.get(priority_level, 2)
                if ticket_priority > team_max_priority:
                    continue

                suitable_teams.append(team_name)

            # Select best team (prefer specialized teams for complex/high-priority tickets)
            if suitable_teams:
                # For high complexity or critical priority, prefer higher-level teams
                if complexity in ['high', 'complex'] or priority_level in ['Critical', 'critical']:
                    selected_team = max(suitable_teams, key=lambda t: self.complexity_levels.get(self.teams[t]['max_complexity'], 2))
                else:
                    # For simpler tickets, prefer lower-level teams to distribute load
                    selected_team = min(suitable_teams, key=lambda t: self.complexity_levels.get(self.teams[t]['max_complexity'], 2))

                reasoning = f"Matched {category} category with {complexity} complexity and {priority_level} priority"
            else:
                # Fallback to Level2_Technical for unmatched tickets
                selected_team = 'Level2_Technical'
                reasoning = f"No perfect match found for {category}/{complexity}/{priority_level}, escalating to Level2_Technical"
                self.routing_stats['fallback_assignments'] += 1

            routing_decision = self._create_routing_decision(
                selected_team,
                reasoning,
                priority_analysis,
                classification_analysis,
                priority_level,
                complexity
            )

        # Update team assignment stats
        self.routing_stats['team_assignments'][routing_decision['assigned_team']] += 1
        self.routing_stats['sla_distribution'][routing_decision['estimated_sla_hours']] += 1

        # Store routing decision for detailed analysis
        self.routing_stats['routing_decisions'].append({
            'ticket_id': ticket.get('id', 'unknown'),
            'category': category,
            'priority': priority_level,
            'complexity': complexity,
            'assigned_team': routing_decision['assigned_team'],
            'sla_hours': routing_decision['estimated_sla_hours'],
            'is_security': is_security
        })

        return routing_decision

    def _create_routing_decision(self, team, reasoning, priority_analysis, classification_analysis, priority_level, complexity):
        """Create a structured routing decision."""
        sla_hours = self._calculate_sla(priority_level, complexity)

        return {
            'assigned_team': team,
            'recommended_queue': f"{team}_Queue",
            'reasoning': reasoning,
            'priority_info': priority_analysis,
            'classification_info': classification_analysis,
            'estimated_sla_hours': sla_hours,
            'expected_response_time_hours': sla_hours,
            'routing_confidence': 0.85,
            'agent': 'RoutingAgent'
        }

    def _calculate_sla(self, priority_level, complexity):
        """Calculate SLA based on priority and complexity."""
        base_sla = {
            'critical': 4,
            'Critical': 4,
            'high': 24,
            'High': 24,
            'medium': 72,
            'Medium': 72,
            'low': 168,
            'Low': 168
        }

        complexity_multiplier = {
            'low': 0.5,
            'simple': 0.5,
            'medium': 1.0,
            'moderate': 1.0,
            'high': 1.5,
            'complex': 1.5
        }

        base_time = base_sla.get(priority_level, 72)  # Default to 72 hours
        multiplier = complexity_multiplier.get(complexity, 1.0)  # Default to 1.0

        return int(base_time * multiplier)

    def get_summary_statistics(self):
        """
        Generate comprehensive summary statistics for all processed tickets.

        Returns:
            dict: Detailed statistics about routing performance
        """
        if self.routing_stats['total_tickets'] == 0:
            return {"message": "No tickets have been processed yet."}

        total = self.routing_stats['total_tickets']

        # Calculate average SLA (FIXED: proper calculation)
        if self.routing_stats['routing_decisions']:
            sla_values = [decision['sla_hours'] for decision in self.routing_stats['routing_decisions']]
            avg_sla = statistics.mean(sla_values)
        else:
            avg_sla = 0

        # Calculate team utilization as percentage of total tickets (FIXED: more meaningful metric)
        team_utilization = {}
        team_load_distribution = {}

        for team_name in self.teams.keys():
            assignments = self.routing_stats['team_assignments'].get(team_name, 0)
            # Utilization as percentage of total workload
            utilization_pct = (assignments / total) * 100 if total > 0 else 0
            team_utilization[team_name] = round(utilization_pct, 2)

            # Load relative to team capacity
            capacity = self.teams[team_name]['capacity']
            load_ratio = assignments / capacity if capacity > 0 else 0
            team_load_distribution[team_name] = round(load_ratio, 2)

        # Calculate distribution percentages (FIXED: handle empty distributions)
        def safe_percentage_calc(distribution_dict, total_count):
            return {k: round((v/total_count)*100, 2) for k, v in distribution_dict.items()} if total_count > 0 else {}

        category_percentages = safe_percentage_calc(self.routing_stats['category_distribution'], total)
        priority_percentages = safe_percentage_calc(self.routing_stats['priority_distribution'], total)
        complexity_percentages = safe_percentage_calc(self.routing_stats['complexity_distribution'], total)
        team_percentages = safe_percentage_calc(self.routing_stats['team_assignments'], total)

        # FIXED: More accurate performance metrics
        routing_accuracy = self._calculate_routing_accuracy()
        security_detection_rate = (self.routing_stats['security_tickets'] / total) * 100 if total > 0 else 0
        load_balance_score = self._calculate_load_balance_score(team_load_distribution)

        # Additional metrics for better evaluation
        sla_efficiency = self._calculate_sla_efficiency()
        team_specialization_score = self._calculate_team_specialization_score()

        return {
            'overview': {
                'total_tickets_processed': total,
                'security_tickets': self.routing_stats['security_tickets'],
                'fallback_assignments': self.routing_stats['fallback_assignments'],
                'average_sla_hours': round(avg_sla, 2)
            },
            'team_assignments': {
                'counts': dict(self.routing_stats['team_assignments']),
                'percentages': team_percentages,
                'workload_distribution': team_utilization,
                'capacity_utilization': team_load_distribution
            },
            'distributions': {
                'categories': {
                    'counts': dict(self.routing_stats['category_distribution']),
                    'percentages': category_percentages
                },
                'priorities': {
                    'counts': dict(self.routing_stats['priority_distribution']),
                    'percentages': priority_percentages
                },
                'complexity': {
                    'counts': dict(self.routing_stats['complexity_distribution']),
                    'percentages': complexity_percentages
                }
            },
            'sla_analysis': {
                'distribution': dict(self.routing_stats['sla_distribution']),
                'average_hours': round(avg_sla, 2),
                'median_hours': self._calculate_median_sla(),
                'efficiency_score': sla_efficiency
            },
            'performance_metrics': {
                'routing_accuracy': routing_accuracy,
                'security_detection_rate': round(security_detection_rate, 2),
                'load_balance_score': load_balance_score,
                'team_specialization_score': team_specialization_score,
                'fallback_rate': round((self.routing_stats['fallback_assignments'] / total) * 100, 2) if total > 0 else 0
            }
        }

    def _calculate_routing_accuracy(self):
        """Calculate routing accuracy based on appropriate team selection."""
        if not self.routing_stats['routing_decisions']:
            return 0.0

        accurate_routes = 0
        total_routes = len(self.routing_stats['routing_decisions'])

        for decision in self.routing_stats['routing_decisions']:
            team = decision['assigned_team']
            category = decision['category']
            priority = decision['priority']
            complexity = decision['complexity']

            # Check if the team can handle this ticket type
            team_info = self.teams.get(team, {})

            # Category match
            category_match = category in team_info.get('categories', [])

            # Priority capability
            team_max_priority = self.priority_levels.get(team_info.get('max_priority', 'Medium'), 2)
            ticket_priority = self.priority_levels.get(priority, 2)
            priority_capable = ticket_priority <= team_max_priority

            # Complexity capability
            team_max_complexity = self.complexity_levels.get(team_info.get('max_complexity', 'medium'), 2)
            ticket_complexity = self.complexity_levels.get(complexity, 2)
            complexity_capable = ticket_complexity <= team_max_complexity

            # Security special case
            is_security_appropriate = (team == 'Security_Team' and decision['is_security']) or \
                                    (team != 'Security_Team' and not decision['is_security'])

            if category_match and priority_capable and complexity_capable and is_security_appropriate:
                accurate_routes += 1

        return round((accurate_routes / total_routes) * 100, 2) if total_routes > 0 else 0.0

    def _calculate_load_balance_score(self, team_load_distribution):
        """Calculate how well balanced the load is across teams (0-100, higher is better)."""
        if not team_load_distribution or len(team_load_distribution) < 2:
            return 100.0  # Perfect balance if only one team or no teams

        load_values = [load for load in team_load_distribution.values() if load > 0]

        if not load_values:
            return 100.0

        # Calculate coefficient of variation (lower is better for balance)
        mean_load = statistics.mean(load_values)
        if mean_load == 0:
            return 100.0

        std_dev = statistics.stdev(load_values) if len(load_values) > 1 else 0
        cv = std_dev / mean_load

        # Convert to 0-100 score (lower CV = higher score)
        # CV of 0 = 100, CV of 1 = 0 (approximately)
        score = max(0, 100 - (cv * 100))
        return round(score, 2)

    def _calculate_median_sla(self):
        """Calculate median SLA hours."""
        if not self.routing_stats['routing_decisions']:
            return 0

        sla_values = [decision['sla_hours'] for decision in self.routing_stats['routing_decisions']]
        return statistics.median(sla_values)

    def _calculate_sla_efficiency(self):
        """Calculate SLA efficiency score based on appropriate SLA assignment."""
        if not self.routing_stats['routing_decisions']:
            return 0.0

        efficient_assignments = 0
        total_assignments = len(self.routing_stats['routing_decisions'])

        for decision in self.routing_stats['routing_decisions']:
            priority = decision['priority']
            complexity = decision['complexity']
            actual_sla = decision['sla_hours']
            expected_sla = self._calculate_sla(priority, complexity)

            # Consider efficient if actual SLA matches expected SLA
            if actual_sla == expected_sla:
                efficient_assignments += 1

        return round((efficient_assignments / total_assignments) * 100, 2) if total_assignments > 0 else 0.0

    def _calculate_team_specialization_score(self):
        """Calculate how well teams are being used for their specialized purposes."""
        if not self.routing_stats['routing_decisions']:
            return 0.0

        specialized_assignments = 0
        total_assignments = len(self.routing_stats['routing_decisions'])

        for decision in self.routing_stats['routing_decisions']:
            team = decision['assigned_team']
            category = decision['category']

            # Check if team is being used for its primary specialization
            if team == 'Security_Team' and decision['is_security']:
                specialized_assignments += 1
            elif team == 'Billing_Team' and category == 'Billing':
                specialized_assignments += 1
            elif team == 'Level3_Engineering' and decision['complexity'] in ['high', 'complex']:
                specialized_assignments += 1
            elif team == 'Level1_Support' and decision['complexity'] in ['low', 'simple']:
                specialized_assignments += 1
            elif team == 'Level2_Technical':
                # Level2 is appropriately used for medium complexity or as fallback
                specialized_assignments += 1

        return round((specialized_assignments / total_assignments) * 100, 2) if total_assignments > 0 else 0.0

    def print_summary_statistics(self):
        """Print formatted summary statistics to console."""
        stats = self.get_summary_statistics()

        if "message" in stats:
            print(stats["message"])
            return

        print("\n" + "="*80)
        print("📊 TICKET ROUTING SUMMARY STATISTICS")
        print("="*80)

        # Overview
        print(f"\n🎯 OVERVIEW:")
        print(f"   Total Tickets Processed: {stats['overview']['total_tickets_processed']}")
        print(f"   Security Tickets: {stats['overview']['security_tickets']}")
        print(f"   Fallback Assignments: {stats['overview']['fallback_assignments']}")
        print(f"   Average SLA Hours: {stats['overview']['average_sla_hours']}")

        # Team Assignments
        print(f"\n👥 TEAM ASSIGNMENTS:")
        for team, count in stats['team_assignments']['counts'].items():
            percentage = stats['team_assignments']['percentages'].get(team, 0)
            workload = stats['team_assignments']['workload_distribution'].get(team, 0)
            capacity_util = stats['team_assignments']['capacity_utilization'].get(team, 0)
            print(f"   {team}: {count} tickets ({percentage}%) - Workload: {workload}%, Capacity: {capacity_util:.1f}x")

        # Category Distribution
        print(f"\n📋 CATEGORY DISTRIBUTION:")
        for category, count in stats['distributions']['categories']['counts'].items():
            percentage = stats['distributions']['categories']['percentages'].get(category, 0)
            print(f"   {category}: {count} tickets ({percentage}%)")

        # Priority Distribution
        print(f"\n⚡ PRIORITY DISTRIBUTION:")
        for priority, count in stats['distributions']['priorities']['counts'].items():
            percentage = stats['distributions']['priorities']['percentages'].get(priority, 0)
            print(f"   {priority}: {count} tickets ({percentage}%)")

        # Complexity Distribution
        print(f"\n🔧 COMPLEXITY DISTRIBUTION:")
        for complexity, count in stats['distributions']['complexity']['counts'].items():
            percentage = stats['distributions']['complexity']['percentages'].get(complexity, 0)
            print(f"   {complexity}: {count} tickets ({percentage}%)")

        # Performance Metrics
        print(f"\n📈 PERFORMANCE METRICS:")
        metrics = stats['performance_metrics']
        print(f"   Routing Accuracy: {metrics['routing_accuracy']}%")
        print(f"   Security Detection Rate: {metrics['security_detection_rate']}%")
        print(f"   Load Balance Score: {metrics['load_balance_score']}/100")
        print(f"   Team Specialization Score: {metrics['team_specialization_score']}%")
        print(f"   Fallback Rate: {metrics['fallback_rate']}%")

        # SLA Analysis
        print(f"\n⏱️  SLA ANALYSIS:")
        sla_analysis = stats['sla_analysis']
        print(f"   Average SLA: {sla_analysis['average_hours']} hours")
        print(f"   Median SLA: {sla_analysis['median_hours']} hours")
        print(f"   SLA Efficiency: {sla_analysis['efficiency_score']}%")
        print(f"   SLA Distribution:")
        for hours, count in sorted(sla_analysis['distribution'].items()):
            print(f"      {hours} hours: {count} tickets")

    def reset_statistics(self):
        """Reset all statistics counters."""
        self.routing_stats = {
            'total_tickets': 0,
            'team_assignments': defaultdict(int),
            'category_distribution': defaultdict(int),
            'priority_distribution': defaultdict(int),
            'complexity_distribution': defaultdict(int),
            'sla_distribution': defaultdict(int),
            'security_tickets': 0,
            'fallback_assignments': 0,
            'routing_decisions': []
        }

    def export_statistics_to_json(self, filename="routing_statistics.json"):
        """Export statistics to a JSON file."""
        stats = self.get_summary_statistics()
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Statistics exported to {filename}")