# support_agents/routing_agent.py

from collections import Counter, defaultdict
import statistics
import json
from datetime import datetime


class RoutingAgent:
    """
    Intelligent ticket routing agent with comprehensive statistics
    """

    def __init__(self):
        self.routing_rules = {
            'security': 'Security Team',
            'api': 'L2 API Team',
            'billing': 'L1 General',
            'technical': 'L2 Technical',
            'feature_request': 'L3 Engineering'
        }

        # SLA hours by priority
        self.sla_matrix = {
            'Critical': 2,
            'High': 8,
            'Medium': 24,
            'Low': 72
        }

        # Customer tier priorities
        self.tier_priority_boost = {
            'Enterprise': 2,
            'Professional': 1,
            'Free': 0
        }

    def route_ticket(self, ticket):
        """
        Route a single ticket and return routing decision
        """
        # Analyze ticket content
        category = self._categorize_ticket(ticket)
        priority = self._calculate_priority(ticket)
        queue = self._select_queue(ticket, category, priority)
        sla_hours = self._calculate_sla(priority, ticket.get('customer_tier', 'Free'))

        routing_decision = {
            'recommended_queue': queue,
            'priority_level': priority,
            'sla_hours': sla_hours,
            'category': category,
            'reasoning': self._generate_reasoning(ticket, category, priority, queue)
        }

        return {
            'ticket_id': ticket.get('ticket_id', 'Unknown'),
            'routing_decision': routing_decision,
            'complexity_score': self._assess_complexity(ticket),
            'urgency_score': self._assess_urgency(ticket)
        }

    def _categorize_ticket(self, ticket):
        """Categorize ticket based on content"""
        subject = ticket.get('subject', '').lower()
        description = ticket.get('description', '').lower()
        content = f"{subject} {description}"

        if any(word in content for word in ['security', 'breach', 'hack', 'vulnerability']):
            return 'security'
        elif any(word in content for word in ['api', 'endpoint', 'integration', 'webhook']):
            return 'api'
        elif any(word in content for word in ['billing', 'payment', 'invoice', 'subscription']):
            return 'billing'
        elif any(word in content for word in ['feature', 'enhancement', 'suggestion', 'roadmap']):
            return 'feature_request'
        else:
            return 'technical'

    def _calculate_priority(self, ticket):
        """Calculate priority based on various factors"""
        base_priority = ticket.get('priority', 'Medium')
        customer_tier = ticket.get('customer_tier', 'Free')

        # Priority scoring
        priority_scores = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        score = priority_scores.get(base_priority, 2)

        # Boost for customer tier
        score += self.tier_priority_boost.get(customer_tier, 0)

        # Convert back to priority
        if score >= 5:
            return 'Critical'
        elif score >= 4:
            return 'High'
        elif score >= 3:
            return 'Medium'
        else:
            return 'Low'

    def _select_queue(self, ticket, category, priority):
        """Select appropriate queue based on category and other factors"""
        base_queue = self.routing_rules.get(category, 'L1 General')

        # Special handling for high-value customers
        if ticket.get('customer_tier') == 'Enterprise' and category == 'technical':
            return 'L2 Technical'

        return base_queue

    def _calculate_sla(self, priority, customer_tier):
        """Calculate SLA hours based on priority and customer tier"""
        base_sla = self.sla_matrix.get(priority, 24)

        # Reduce SLA for Enterprise customers
        if customer_tier == 'Enterprise':
            return max(1, base_sla // 2)
        elif customer_tier == 'Professional':
            return max(2, int(base_sla * 0.75))

        return base_sla

    def _assess_complexity(self, ticket):
        """Assess ticket complexity"""
        description = ticket.get('description', '').lower()

        if any(word in description for word in ['integration', 'api', 'custom', 'advanced']):
            return 'High'
        elif any(word in description for word in ['configuration', 'setup', 'installation']):
            return 'Medium'
        else:
            return 'Low'

    def _assess_urgency(self, ticket):
        """Assess ticket urgency"""
        subject = ticket.get('subject', '').lower()
        description = ticket.get('description', '').lower()
        content = f"{subject} {description}"

        if any(word in content for word in ['urgent', 'critical', 'down', 'broken', 'not working']):
            return 'High'
        elif any(word in content for word in ['slow', 'issue', 'problem']):
            return 'Medium'
        else:
            return 'Low'

    def _generate_reasoning(self, ticket, category, priority, queue):
        """Generate human-readable reasoning for routing decision"""
        customer_tier = ticket.get('customer_tier', 'Free')
        return f"{customer_tier} customer with {category} issue, priority {priority} → {queue}"

    def generate_simple_routing_summary(self, test_tickets):
        """Generate a simple routing summary table like your example"""
        routing_summary = []

        print("🎫 Processing tickets...")
        for ticket in test_tickets:
            result = self.route_ticket(ticket)
            routing_summary.append({
                'ticket_id': ticket['ticket_id'],
                'customer_tier': ticket['customer_tier'].lower(),
                'final_queue': result['routing_decision']['recommended_queue'].upper().replace(' ', '_'),
                'priority': result['routing_decision']['priority_level'].upper(),
                'sla_hours': result['routing_decision']['sla_hours']
            })

        print("\n" + "=" * 80)

        # Display the simple summary table
        print("\n📊 ROUTING SUMMARY")
        print("-" * 80)
        print(f"{'Ticket':<10} {'Customer':<12} {'Queue':<18} {'Priority':<10} {'SLA':<8}")
        print("-" * 80)
        for summary in routing_summary:
            print(f"{summary['ticket_id']:<10} {summary['customer_tier']:<12} "
                  f"{summary['final_queue']:<18} {summary['priority']:<10} {summary['sla_hours']}h")

        print("\n🎯 KEY INSIGHTS:")
        print("• Free tier customers → Standard support queues")
        print("• Enterprise customers → Prioritized routing with reduced SLA")
        print("• Security issues → Immediate Security Team assignment")
        print("• API problems → Specialized L2 API Team")
        print("• Feature requests → L3 Engineering for product development")
        print("• Complex technical issues → L2 Technical for expert handling")

        return routing_summary

    def generate_routing_statistics(self, test_tickets):
        """Generate comprehensive routing statistics and summary"""
        routing_summary = []

        print("🎫 Processing tickets...")
        for i, ticket in enumerate(test_tickets, 1):
            result = self.route_ticket(ticket)
            routing_summary.append({
                'ticket_id': ticket['ticket_id'],
                'customer_tier': ticket['customer_tier'],
                'final_queue': result['routing_decision']['recommended_queue'],
                'priority': result['routing_decision']['priority_level'],
                'sla_hours': result['routing_decision']['sla_hours'],
                'complexity': result.get('complexity_score', 'Unknown'),
                'urgency': result.get('urgency_score', 'Unknown'),
                'category': result['routing_decision']['category']
            })
            print(f"   Processed ticket {i}/{len(test_tickets)}: {ticket['ticket_id']}")

        print("\n" + "=" * 80)

        # Calculate statistics
        stats = self._calculate_routing_stats(routing_summary)

        # Display summary table
        self._display_routing_table(routing_summary)

        # Display statistics
        self._display_routing_statistics(stats)

        # Display insights
        self._display_key_insights()

        return routing_summary, stats

    def _calculate_routing_stats(self, routing_summary):
        """Calculate detailed routing statistics"""
        stats = {}

        # Basic counts
        stats['total_tickets'] = len(routing_summary)
        stats['queue_distribution'] = Counter([r['final_queue'] for r in routing_summary])
        stats['priority_distribution'] = Counter([r['priority'] for r in routing_summary])
        stats['customer_tier_distribution'] = Counter([r['customer_tier'] for r in routing_summary])
        stats['category_distribution'] = Counter([r['category'] for r in routing_summary])

        # SLA statistics
        sla_hours = [r['sla_hours'] for r in routing_summary]
        stats['sla_stats'] = {
            'average': round(statistics.mean(sla_hours), 2),
            'median': statistics.median(sla_hours),
            'min': min(sla_hours),
            'max': max(sla_hours)
        }

        # Queue efficiency metrics
        stats['queue_load'] = {}
        for queue, count in stats['queue_distribution'].items():
            stats['queue_load'][queue] = {
                'ticket_count': count,
                'percentage': round((count / stats['total_tickets']) * 100, 1)
            }

        # Customer tier routing patterns
        stats['tier_routing'] = defaultdict(Counter)
        for summary in routing_summary:
            stats['tier_routing'][summary['customer_tier']][summary['final_queue']] += 1

        # Priority-SLA correlation
        stats['priority_sla'] = defaultdict(list)
        for summary in routing_summary:
            stats['priority_sla'][summary['priority']].append(summary['sla_hours'])

        # Calculate average SLA by priority
        for priority, sla_list in stats['priority_sla'].items():
            stats['priority_sla'][priority] = {
                'tickets': len(sla_list),
                'avg_sla': round(statistics.mean(sla_list), 2)
            }

        return stats

    def _display_routing_table(self, routing_summary):
        """Display the routing summary table"""
        print("\n📊 ROUTING SUMMARY")
        print("-" * 90)
        print(f"{'Ticket':<12} {'Customer':<12} {'Queue':<18} {'Priority':<10} {'SLA':<8} {'Category':<12}")
        print("-" * 90)
        for summary in routing_summary:
            print(f"{summary['ticket_id']:<12} {summary['customer_tier']:<12} "
                  f"{summary['final_queue']:<18} {summary['priority']:<10} "
                  f"{summary['sla_hours']}h{'':<5} {summary['category']:<12}")

    def _display_routing_statistics(self, stats):
        """Display comprehensive routing statistics"""
        print("\n📈 ROUTING STATISTICS")
        print("=" * 90)

        # Basic metrics
        print(f"\n🎯 OVERVIEW:")
        print(f"   Total Tickets Processed: {stats['total_tickets']}")
        print(f"   Average SLA Hours: {stats['sla_stats']['average']}")
        print(f"   SLA Range: {stats['sla_stats']['min']}h - {stats['sla_stats']['max']}h")

        # Category distribution
        print(f"\n📂 CATEGORY BREAKDOWN:")
        for category, count in stats['category_distribution'].items():
            percentage = round((count / stats['total_tickets']) * 100, 1)
            print(f"   {category:<15}: {count} tickets ({percentage}%)")

        # Queue distribution
        print(f"\n🏢 QUEUE DISTRIBUTION:")
        for queue, data in stats['queue_load'].items():
            print(f"   {queue:<20}: {data['ticket_count']} tickets ({data['percentage']}%)")

        # Priority breakdown
        print(f"\n⚡ PRIORITY BREAKDOWN:")
        for priority, count in stats['priority_distribution'].items():
            percentage = round((count / stats['total_tickets']) * 100, 1)
            avg_sla = stats['priority_sla'][priority]['avg_sla']
            print(f"   {priority:<12}: {count} tickets ({percentage}%) | Avg SLA: {avg_sla}h")

        # Customer tier analysis
        print(f"\n👥 CUSTOMER TIER ANALYSIS:")
        for tier, count in stats['customer_tier_distribution'].items():
            percentage = round((count / stats['total_tickets']) * 100, 1)
            print(f"   {tier:<12}: {count} tickets ({percentage}%)")

            # Show routing patterns for this tier
            for queue, queue_count in stats['tier_routing'][tier].items():
                queue_percentage = round((queue_count / count) * 100, 1)
                print(f"      → {queue}: {queue_count} tickets ({queue_percentage}%)")

        # Efficiency metrics
        print(f"\n⚙️ EFFICIENCY METRICS:")
        high_priority_count = stats['priority_distribution'].get('High', 0) + stats['priority_distribution'].get(
            'Critical', 0)
        high_priority_percentage = round((high_priority_count / stats['total_tickets']) * 100, 1)
        print(f"   High/Critical Priority: {high_priority_percentage}%")

        specialized_queues = ['L2 API Team', 'Security Team', 'L3 Engineering']
        specialized_count = sum(stats['queue_distribution'].get(queue, 0) for queue in specialized_queues)
        specialized_percentage = round((specialized_count / stats['total_tickets']) * 100, 1)
        print(f"   Specialized Queue Usage: {specialized_percentage}%")

    def _display_key_insights(self):
        """Display key routing insights"""
        print("\n🎯 KEY INSIGHTS:")
        print("• Free tier customers → Standard support queues")
        print("• Enterprise customers → Prioritized routing with reduced SLA")
        print("• Security issues → Immediate Security Team assignment")
        print("• API problems → Specialized L2 API Team")
        print("• Feature requests → L3 Engineering for product development")
        print("• Complex technical issues → L2 Technical for expert handling")

    def save_statistics_to_file(self, stats, routing_summary, filename=None):
        """Save routing statistics to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"routing_analysis_{timestamp}.json"

        output_data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'routing_summary': routing_summary
        }

        try:
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"\n💾 Statistics saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving statistics: {e}")
            return None


# Example usage and test data
def create_test_tickets():
    """Create sample test tickets for demonstration"""
    return [
        {
            'ticket_id': 'SUP-001',
            'customer_tier': 'Free',
            'subject': 'App is very slow',
            'description': 'The application has been running slowly and is critical for our business',
            'priority': 'Critical'
        },
        {
            'ticket_id': 'SUP-002',
            'customer_tier': 'Enterprise',
            'subject': 'System Down',
            'description': 'Critical system failure affecting all users',
            'priority': 'Critical'
        },
        {
            'ticket_id': 'SUP-003',
            'customer_tier': 'Professional',
            'subject': 'UI Bug in Dashboard',
            'description': 'Important UI elements are not displaying correctly',
            'priority': 'High'
        },
        {
            'ticket_id': 'SUP-004',
            'customer_tier': 'Professional',
            'subject': 'API Integration Issue',
            'description': 'API endpoints returning errors consistently',
            'priority': 'High'
        },
        {
            'ticket_id': 'SUP-005',
            'customer_tier': 'Enterprise',
            'subject': 'Security Breach',
            'description': 'Potential security vulnerability detected in authentication system',
            'priority': 'Critical'
        }
    ]


def main():
    """Run the ticket routing demonstration."""
    agent = RoutingAgent()
    test_tickets = create_test_tickets()

    print("🚀 Starting Simple Routing Summary...")
    # Use the simple summary method
    routing_summary = agent.generate_simple_routing_summary(test_tickets)

    print("\n" + "=" * 80)
    print("🚀 Starting Comprehensive Analysis...")
    # Or use the full statistics method
    detailed_summary, stats = agent.generate_routing_statistics(test_tickets)

    # Optionally save to file
    agent.save_statistics_to_file(stats, detailed_summary)


if __name__ == "__main__":
    main()