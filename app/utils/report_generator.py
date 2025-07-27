from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


def generate_weekly_report_html(ranking_data: List[Dict]) -> str:
    """
    Generate HTML report for weekly ranking data
    
    Args:
        ranking_data: List of ranking data with changes
        
    Returns:
        HTML string for email report
    """
    
    # Calculate summary statistics
    stats = calculate_report_statistics(ranking_data)
    
    # Sort data for better presentation
    sorted_data = sort_ranking_data_for_report(ranking_data)
    
    # Load and render template
    import os
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'email_templates', 'weekly_report.html')
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    template = Template(template_content)
    
    html_content = template.render(
        report_date=datetime.now().strftime('%B %d, %Y'),
        stats=stats,
        rankings=sorted_data,
        get_change_class=get_change_class,
        get_change_icon=get_change_icon,
        format_position=format_position
    )
    
    return html_content


def calculate_report_statistics(ranking_data: List[Dict]) -> Dict:
    """
    Calculate summary statistics for the report
    
    Args:
        ranking_data: List of ranking data
        
    Returns:
        Dictionary with statistics
    """
    total_keywords = len(ranking_data)
    ranked_keywords = sum(1 for item in ranking_data if item.get('found_in_top_100', False))
    
    # Count changes
    improvements = sum(1 for item in ranking_data if item.get('change_direction') == 'up')
    declines = sum(1 for item in ranking_data if item.get('change_direction') == 'down')
    new_rankings = sum(1 for item in ranking_data if item.get('change_direction') == 'new')
    lost_rankings = sum(1 for item in ranking_data if item.get('change_direction') == 'lost')
    no_change = sum(1 for item in ranking_data if item.get('change_direction') == 'same')
    
    # Calculate average position for ranked keywords
    ranked_positions = [item.get('position') for item in ranking_data 
                       if item.get('position') is not None]
    avg_position = sum(ranked_positions) / len(ranked_positions) if ranked_positions else 0
    
    # Top 10 count
    top_10_count = sum(1 for item in ranking_data 
                      if item.get('position') is not None and item.get('position') <= 10)
    
    # Top 3 count
    top_3_count = sum(1 for item in ranking_data 
                     if item.get('position') is not None and item.get('position') <= 3)
    
    return {
        'total_keywords': total_keywords,
        'ranked_keywords': ranked_keywords,
        'ranking_percentage': round((ranked_keywords / total_keywords * 100), 1) if total_keywords > 0 else 0,
        'improvements': improvements,
        'declines': declines,
        'new_rankings': new_rankings,
        'lost_rankings': lost_rankings,
        'no_change': no_change,
        'average_position': round(avg_position, 1),
        'top_10_count': top_10_count,
        'top_3_count': top_3_count
    }


def sort_ranking_data_for_report(ranking_data: List[Dict]) -> List[Dict]:
    """
    Sort ranking data for optimal report presentation
    
    Args:
        ranking_data: List of ranking data
        
    Returns:
        Sorted list prioritizing significant changes
    """
    def sort_key(item):
        # Priority order: major changes first, then by position
        change_priority = {
            'new': 1,
            'up': 2,
            'down': 3,
            'lost': 4,
            'same': 5
        }
        
        magnitude_priority = {
            'major': 1,
            'moderate': 2,
            'minor': 3,
            'none': 4
        }
        
        direction = item.get('change_direction', 'same')
        magnitude = item.get('change_magnitude', 'none')
        position = item.get('position', 999)  # Put unranked at the end
        
        return (
            change_priority.get(direction, 5),
            magnitude_priority.get(magnitude, 4),
            position
        )
    
    return sorted(ranking_data, key=sort_key)


def get_change_class(change_direction: str) -> str:
    """Get CSS class for change direction"""
    class_map = {
        'up': 'improvement',
        'new': 'new-ranking',
        'down': 'decline',
        'lost': 'lost-ranking',
        'same': 'no-change'
    }
    return class_map.get(change_direction, 'no-change')


def get_change_icon(change_direction: str) -> str:
    """Get icon for change direction"""
    icon_map = {
        'up': '⬆️',
        'new': '🆕',
        'down': '⬇️',
        'lost': '❌',
        'same': '➡️'
    }
    return icon_map.get(change_direction, '➡️')


def format_position(position: Optional[int]) -> str:
    """Format position for display"""
    if position is None:
        return "Not in top 100"
    return f"#{position}"


def generate_trend_analysis(keyword_id: int, days: int = 30) -> Dict:
    """
    Generate trend analysis for a specific keyword
    
    Args:
        keyword_id: ID of the keyword to analyze
        days: Number of days to analyze
        
    Returns:
        Dictionary with trend analysis
    """
    from app.models import Ranking
    from datetime import date, timedelta
    
    # Get historical data
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    rankings = Ranking.query.filter(
        Ranking.keyword_id == keyword_id,
        Ranking.check_date >= start_date,
        Ranking.check_date <= end_date
    ).order_by(Ranking.check_date.asc()).all()
    
    if not rankings:
        return {'trend': 'insufficient_data', 'data_points': 0}
    
    positions = [r.position for r in rankings if r.position is not None]
    
    if len(positions) < 2:
        return {'trend': 'insufficient_data', 'data_points': len(positions)}
    
    # Simple trend calculation
    first_half = positions[:len(positions)//2]
    second_half = positions[len(positions)//2:]
    
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    
    if avg_second < avg_first:  # Lower position number = better
        trend = 'improving'
    elif avg_second > avg_first:
        trend = 'declining'
    else:
        trend = 'stable'
    
    return {
        'trend': trend,
        'data_points': len(positions),
        'first_half_avg': round(avg_first, 1),
        'second_half_avg': round(avg_second, 1),
        'change': round(avg_first - avg_second, 1)
    }