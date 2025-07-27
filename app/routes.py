from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date, timedelta
import logging
from app.models import db, Keyword, Ranking, RankingChange
from app.tasks import check_single_keyword, weekly_rank_check, send_report_email
from app.config import Config

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('main.dashboard'))


@bp.route('/dashboard')
def dashboard():
    """Main dashboard showing current rankings"""
    try:
        # Get all active keywords with their latest rankings
        keywords = db.session.query(Keyword).filter_by(is_active=True).all()
        
        dashboard_data = []
        for keyword in keywords:
            latest_ranking = Ranking.query.filter_by(
                keyword_id=keyword.id
            ).order_by(Ranking.check_date.desc()).first()
            
            latest_change = RankingChange.query.filter_by(
                keyword_id=keyword.id
            ).order_by(RankingChange.change_date.desc()).first()
            
            keyword_data = {
                'id': keyword.id,
                'keyword': keyword.keyword,
                'domain': keyword.domain,
                'position': latest_ranking.position if latest_ranking else None,
                'url': latest_ranking.url if latest_ranking else None,
                'found_in_top_100': latest_ranking.found_in_top_100 if latest_ranking else False,
                'last_checked': latest_ranking.check_date if latest_ranking else None,
                'change_direction': latest_change.change_direction if latest_change else 'none',
                'change_magnitude': latest_change.change_magnitude if latest_change else 'none',
                'position_change': latest_change.position_change if latest_change else 0,
                'previous_position': latest_change.previous_position if latest_change else None
            }
            dashboard_data.append(keyword_data)
        
        # Calculate summary statistics
        stats = calculate_dashboard_stats(dashboard_data)
        
        return render_template('dashboard.html', 
                             keywords=dashboard_data, 
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {e}", 'error')
        return render_template('dashboard.html', keywords=[], stats={})


@bp.route('/api/rankings')
def api_rankings():
    """JSON API endpoint for current rankings"""
    try:
        keywords = Keyword.query.filter_by(is_active=True).all()
        results = []
        
        for keyword in keywords:
            latest_ranking = keyword.latest_ranking
            if latest_ranking:
                results.append({
                    'keyword_id': keyword.id,
                    'keyword': keyword.keyword,
                    'domain': keyword.domain,
                    'position': latest_ranking.position,
                    'url': latest_ranking.url,
                    'title': latest_ranking.title,
                    'found_in_top_100': latest_ranking.found_in_top_100,
                    'check_date': latest_ranking.check_date.isoformat(),
                    'serp_features': latest_ranking.serp_features
                })
        
        return jsonify({
            'success': True,
            'data': results,
            'total': len(results),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in API rankings endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/keyword/<int:keyword_id>/history')
def api_keyword_history(keyword_id):
    """Get ranking history for a specific keyword"""
    try:
        days = request.args.get('days', 30, type=int)
        
        keyword = Keyword.query.get_or_404(keyword_id)
        
        # Get historical rankings
        start_date = date.today() - timedelta(days=days)
        rankings = Ranking.query.filter(
            Ranking.keyword_id == keyword_id,
            Ranking.check_date >= start_date
        ).order_by(Ranking.check_date.asc()).all()
        
        history_data = []
        for ranking in rankings:
            history_data.append({
                'date': ranking.check_date.isoformat(),
                'position': ranking.position,
                'found_in_top_100': ranking.found_in_top_100,
                'url': ranking.url
            })
        
        return jsonify({
            'success': True,
            'keyword': keyword.keyword,
            'domain': keyword.domain,
            'history': history_data,
            'days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting keyword history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/trigger-check', methods=['POST'])
def trigger_manual_check():
    """Trigger manual rank check"""
    try:
        check_type = request.form.get('type', 'all')
        
        if check_type == 'single':
            keyword_id = request.form.get('keyword_id', type=int)
            if not keyword_id:
                flash('Keyword ID is required for single check', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Trigger single keyword check
            task = check_single_keyword.delay(keyword_id)
            flash(f'Single keyword check started (Task ID: {task.id})', 'success')
            
        else:
            # Trigger full check
            task = weekly_rank_check.delay()
            flash(f'Full rank check started (Task ID: {task.id})', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        logger.error(f"Error triggering manual check: {e}")
        flash(f'Error starting check: {e}', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/send-report', methods=['POST'])
def trigger_report():
    """Trigger manual report sending"""
    try:
        recipient = request.form.get('recipient') or Config.RECIPIENT_EMAIL
        
        if not recipient:
            flash('Recipient email is required', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Get current ranking data
        keywords = Keyword.query.filter_by(is_active=True).all()
        report_data = []
        
        for keyword in keywords:
            latest_ranking = keyword.latest_ranking
            latest_change = RankingChange.query.filter_by(
                keyword_id=keyword.id
            ).order_by(RankingChange.change_date.desc()).first()
            
            if latest_ranking:
                keyword_data = {
                    'keyword': keyword.keyword,
                    'position': latest_ranking.position,
                    'url': latest_ranking.url,
                    'found_in_top_100': latest_ranking.found_in_top_100,
                    'change_direction': latest_change.change_direction if latest_change else 'none',
                    'change_magnitude': latest_change.change_magnitude if latest_change else 'none',
                    'position_change': latest_change.position_change if latest_change else 0
                }
                report_data.append(keyword_data)
        
        # Send report
        task = send_report_email.delay(report_data, recipient)
        flash(f'Report sending started (Task ID: {task.id})', 'success')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        flash(f'Error sending report: {e}', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/keywords')
def keywords_list():
    """List all keywords with management options"""
    try:
        keywords = Keyword.query.all()
        return render_template('keywords.html', keywords=keywords)
        
    except Exception as e:
        logger.error(f"Error loading keywords: {e}")
        flash(f'Error loading keywords: {e}', 'error')
        return render_template('keywords.html', keywords=[])


@bp.route('/keywords/add', methods=['POST'])
def add_keyword():
    """Add a new keyword"""
    try:
        keyword_text = request.form.get('keyword', '').strip()
        domain = request.form.get('domain', Config.TARGET_DOMAIN).strip()
        
        if not keyword_text:
            flash('Keyword is required', 'error')
            return redirect(url_for('main.keywords_list'))
        
        # Check if keyword already exists for this domain
        existing = Keyword.query.filter_by(keyword=keyword_text, domain=domain).first()
        if existing:
            flash('Keyword already exists for this domain', 'warning')
            return redirect(url_for('main.keywords_list'))
        
        # Add new keyword
        new_keyword = Keyword(
            keyword=keyword_text,
            domain=domain,
            is_active=True
        )
        
        db.session.add(new_keyword)
        db.session.commit()
        
        flash(f'Keyword "{keyword_text}" added successfully', 'success')
        return redirect(url_for('main.keywords_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding keyword: {e}")
        flash(f'Error adding keyword: {e}', 'error')
        return redirect(url_for('main.keywords_list'))


@bp.route('/keywords/<int:keyword_id>/toggle', methods=['POST'])
def toggle_keyword(keyword_id):
    """Toggle keyword active status"""
    try:
        keyword = Keyword.query.get_or_404(keyword_id)
        keyword.is_active = not keyword.is_active
        db.session.commit()
        
        status = 'activated' if keyword.is_active else 'deactivated'
        flash(f'Keyword "{keyword.keyword}" {status}', 'success')
        
        return redirect(url_for('main.keywords_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling keyword: {e}")
        flash(f'Error updating keyword: {e}', 'error')
        return redirect(url_for('main.keywords_list'))


@bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Get basic stats
        keyword_count = Keyword.query.count()
        ranking_count = Ranking.query.count()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'keywords': keyword_count,
            'rankings': ranking_count
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


def calculate_dashboard_stats(keywords_data):
    """Calculate summary statistics for dashboard"""
    total = len(keywords_data)
    if total == 0:
        return {
            'total_keywords': 0,
            'ranked_keywords': 0,
            'ranking_percentage': 0,
            'average_position': 0,
            'top_10_count': 0,
            'top_3_count': 0,
            'improvements': 0,
            'declines': 0,
            'new_rankings': 0
        }
    
    ranked = sum(1 for k in keywords_data if k['found_in_top_100'])
    positions = [k['position'] for k in keywords_data if k['position'] is not None]
    avg_position = sum(positions) / len(positions) if positions else 0
    
    top_10 = sum(1 for k in keywords_data if k['position'] and k['position'] <= 10)
    top_3 = sum(1 for k in keywords_data if k['position'] and k['position'] <= 3)
    
    improvements = sum(1 for k in keywords_data if k['change_direction'] == 'up')
    declines = sum(1 for k in keywords_data if k['change_direction'] == 'down')
    new_rankings = sum(1 for k in keywords_data if k['change_direction'] == 'new')
    
    return {
        'total_keywords': total,
        'ranked_keywords': ranked,
        'ranking_percentage': round((ranked / total * 100), 1),
        'average_position': round(avg_position, 1),
        'top_10_count': top_10,
        'top_3_count': top_3,
        'improvements': improvements,
        'declines': declines,
        'new_rankings': new_rankings
    }