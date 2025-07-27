from celery import Celery
from datetime import datetime, date, timedelta
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery with configuration
celery = Celery('seo_tracker')

# Configure Celery
celery.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        # Scheduled tasks can be configured later via web interface or manual triggers
    }
)


@celery.task(bind=True)
def weekly_rank_check(self):
    """
    Scheduled weekly task to check all keyword rankings
    """
    from app import create_app
    flask_app = create_app()
    
    with flask_app.app_context():
        try:
            logger.info("Starting weekly rank check")
            
            # Import models and config within app context
            from app.models import db, Keyword, Ranking, RankingChange
            from app.utils.serpapi_client import get_keyword_ranking
            from app.config import Config
            
            # Get all active keywords
            keywords = Keyword.query.filter_by(is_active=True).all()
            
            if not keywords:
                logger.warning("No active keywords found")
                return "No active keywords to check"
            
            # Get API key and target domain
            api_key = Config.SERPAPI_KEY
            if not api_key:
                logger.error("SERPAPI_KEY not configured")
                return "SERPAPI_KEY not configured"
            
            results = []
            
            # Process each keyword
            for keyword in keywords:
                try:
                    # Check ranking for this keyword
                    ranking_data = get_keyword_ranking(
                        keyword.keyword, 
                        keyword.domain, 
                        api_key
                    )
                    
                    # Save ranking data
                    ranking_result = save_ranking_data(keyword.id, ranking_data)
                    results.append(ranking_result)
                    
                    logger.info(f"Checked keyword: {keyword.keyword} - Position: {ranking_data.get('position', 'Not found')}")
                    
                except Exception as e:
                    logger.error(f"Error checking keyword {keyword.keyword}: {e}")
                    results.append({
                        'keyword_id': keyword.id,
                        'keyword': keyword.keyword,
                        'error': str(e)
                    })
            
            # Generate and send report
            send_weekly_report_task.delay(results)
            
            logger.info(f"Weekly rank check completed. Checked {len(results)} keywords")
            return f"Checked {len(results)} keywords successfully"
            
        except Exception as e:
            logger.error(f"Error in weekly_rank_check: {e}")
            raise self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(bind=True)
def check_single_keyword(self, keyword_id):
    """
    Check ranking for a single keyword
    
    Args:
        keyword_id: ID of the keyword to check
    """
    from app import create_app
    flask_app = create_app()
    
    with flask_app.app_context():
        try:
            from app.models import Keyword
            from app.utils.serpapi_client import get_keyword_ranking
            from app.config import Config
            
            keyword = Keyword.query.get(keyword_id)
            if not keyword:
                return f"Keyword with ID {keyword_id} not found"
            
            api_key = Config.SERPAPI_KEY
            if not api_key:
                return "SERPAPI_KEY not configured"
            
            # Check ranking
            ranking_data = get_keyword_ranking(
                keyword.keyword,
                keyword.domain,
                api_key
            )
            
            # Save ranking data
            result = save_ranking_data(keyword_id, ranking_data)
            
            logger.info(f"Single keyword check completed for: {keyword.keyword}")
            return result
            
        except Exception as e:
            logger.error(f"Error in check_single_keyword: {e}")
            raise self.retry(exc=e, countdown=30, max_retries=2)


@celery.task
def send_weekly_report_task(ranking_results):
    """
    Send weekly email report
    
    Args:
        ranking_results: List of ranking result dictionaries
    """
    from app import create_app
    flask_app = create_app()
    
    with flask_app.app_context():
        try:
            from app.config import Config
            from app.utils.email_sender import smtp_gmail_setup
            
            recipient_email = Config.RECIPIENT_EMAIL
            if not recipient_email:
                logger.error("RECIPIENT_EMAIL not configured")
                return "RECIPIENT_EMAIL not configured"
            
            # Prepare ranking data with change information
            report_data = prepare_report_data(ranking_results)
            
            # Send email
            email_sender = smtp_gmail_setup()
            success = email_sender.send_weekly_report(report_data, recipient_email)
            
            if success:
                logger.info(f"Weekly report sent successfully to {recipient_email}")
                return "Weekly report sent successfully"
            else:
                logger.error("Failed to send weekly report")
                return "Failed to send weekly report"
                
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
            return f"Error sending report: {e}"


@celery.task
def send_report_email(report_data, recipient_email):
    """
    Send a custom email report
    
    Args:
        report_data: Ranking data for the report
        recipient_email: Email address to send to
    """
    from app import create_app
    flask_app = create_app()
    
    with flask_app.app_context():
        try:
            from app.utils.email_sender import smtp_gmail_setup
            
            email_sender = smtp_gmail_setup()
            success = email_sender.send_weekly_report(report_data, recipient_email)
            
            if success:
                logger.info(f"Custom report sent successfully to {recipient_email}")
                return "Report sent successfully"
            else:
                logger.error("Failed to send custom report")
                return "Failed to send report"
                
        except Exception as e:
            logger.error(f"Error sending custom report: {e}")
            return f"Error sending report: {e}"


@celery.task
def cleanup_old_data():
    """
    Clean up old ranking data to manage database size
    Keeps data for the last 365 days
    """
    from app import create_app
    flask_app = create_app()
    
    with flask_app.app_context():
        try:
            from app.models import db, Ranking, RankingChange
            
            cutoff_date = date.today() - timedelta(days=365)
            
            # Delete old rankings
            old_rankings = Ranking.query.filter(Ranking.check_date < cutoff_date).all()
            for ranking in old_rankings:
                db.session.delete(ranking)
            
            # Delete old ranking changes
            old_changes = RankingChange.query.filter(RankingChange.change_date < cutoff_date).all()
            for change in old_changes:
                db.session.delete(change)
            
            db.session.commit()
            
            deleted_count = len(old_rankings) + len(old_changes)
            logger.info(f"Cleaned up {deleted_count} old records")
            return f"Cleaned up {deleted_count} old records"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in cleanup_old_data: {e}")
            return f"Error cleaning up data: {e}"


def save_ranking_data(keyword_id, ranking_data):
    """
    Save ranking data to database and calculate changes
    
    Args:
        keyword_id: ID of the keyword
        ranking_data: Ranking data from SerpAPI
    
    Returns:
        Dictionary with save result
    """
    try:
        from app.models import db, Ranking, RankingChange
        
        # Get the latest ranking for comparison
        latest_ranking = Ranking.query.filter_by(
            keyword_id=keyword_id
        ).order_by(Ranking.check_date.desc()).first()
        
        # Create new ranking record
        new_ranking = Ranking(
            keyword_id=keyword_id,
            position=ranking_data.get('position'),
            url=ranking_data.get('url'),
            title=ranking_data.get('title'),
            found_in_top_100=ranking_data.get('found_in_top_100', False),
            serp_features=ranking_data.get('serp_features', {}),
            check_date=date.today()
        )
        
        db.session.add(new_ranking)
        
        # Calculate and save ranking change
        if latest_ranking:
            change_direction, change_magnitude, position_change = RankingChange.calculate_change_metrics(
                latest_ranking.position,
                new_ranking.position
            )
            
            ranking_change = RankingChange(
                keyword_id=keyword_id,
                previous_position=latest_ranking.position,
                current_position=new_ranking.position,
                position_change=position_change,
                change_direction=change_direction,
                change_magnitude=change_magnitude,
                change_date=date.today()
            )
            
            db.session.add(ranking_change)
        
        db.session.commit()
        
        result = {
            'keyword_id': keyword_id,
            'keyword': ranking_data.get('keyword'),
            'position': new_ranking.position,
            'found_in_top_100': new_ranking.found_in_top_100,
            'url': new_ranking.url,
            'previous_position': latest_ranking.position if latest_ranking else None,
            'change_direction': change_direction if latest_ranking else 'new',
            'change_magnitude': change_magnitude if latest_ranking else 'major',
            'position_change': position_change if latest_ranking else None
        }
        
        return result
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving ranking data for keyword {keyword_id}: {e}")
        raise e


def prepare_report_data(ranking_results):
    """
    Prepare ranking data for email report
    
    Args:
        ranking_results: List of ranking result dictionaries
    
    Returns:
        List of prepared data for report
    """
    report_data = []
    
    for result in ranking_results:
        if 'error' not in result:
            report_data.append(result)
    
    return report_data


# Manual task execution functions for development/testing
def run_manual_check():
    """Run manual keyword check for testing"""
    return weekly_rank_check.delay()


def run_manual_cleanup():
    """Run manual cleanup for testing"""
    return cleanup_old_data.delay()