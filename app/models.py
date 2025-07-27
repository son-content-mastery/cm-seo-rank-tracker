from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import json

db = SQLAlchemy()


class Keyword(db.Model):
    __tablename__ = 'keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rankings = db.relationship('Ranking', backref='keyword_rel', lazy=True, cascade='all, delete-orphan')
    changes = db.relationship('RankingChange', backref='keyword_rel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Keyword {self.keyword} for {self.domain}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'domain': self.domain,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def latest_ranking(self):
        return Ranking.query.filter_by(keyword_id=self.id).order_by(Ranking.check_date.desc()).first()


class Ranking(db.Model):
    __tablename__ = 'rankings'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'), nullable=False)
    position = db.Column(db.Integer, nullable=True)  # None if not found in top 100
    url = db.Column(db.Text, nullable=True)
    title = db.Column(db.Text, nullable=True)
    found_in_top_100 = db.Column(db.Boolean, default=False)
    serp_features = db.Column(db.JSON)  # Store additional SERP data
    check_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ranking {self.keyword_id}: pos {self.position} on {self.check_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword_id': self.keyword_id,
            'position': self.position,
            'url': self.url,
            'title': self.title,
            'found_in_top_100': self.found_in_top_100,
            'serp_features': self.serp_features,
            'check_date': self.check_date.isoformat() if self.check_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RankingChange(db.Model):
    __tablename__ = 'ranking_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'), nullable=False)
    previous_position = db.Column(db.Integer, nullable=True)
    current_position = db.Column(db.Integer, nullable=True)
    position_change = db.Column(db.Integer, nullable=True)  # Positive = improvement, Negative = decline
    change_direction = db.Column(db.String(50), nullable=True)  # 'up', 'down', 'new', 'lost', 'same'
    change_magnitude = db.Column(db.String(50), nullable=True)  # 'major', 'moderate', 'minor'
    change_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RankingChange {self.keyword_id}: {self.previous_position} -> {self.current_position}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword_id': self.keyword_id,
            'previous_position': self.previous_position,
            'current_position': self.current_position,
            'position_change': self.position_change,
            'change_direction': self.change_direction,
            'change_magnitude': self.change_magnitude,
            'change_date': self.change_date.isoformat() if self.change_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def calculate_change_metrics(previous_pos, current_pos):
        """Calculate change direction and magnitude"""
        if previous_pos is None and current_pos is not None:
            return 'new', 'major', current_pos * -1  # New entry (improvement)
        elif previous_pos is not None and current_pos is None:
            return 'lost', 'major', previous_pos  # Lost ranking (decline)
        elif previous_pos == current_pos:
            return 'same', 'none', 0
        elif current_pos < previous_pos:  # Improved (lower number = better)
            change = previous_pos - current_pos
            if change >= 10:
                magnitude = 'major'
            elif change >= 5:
                magnitude = 'moderate'
            else:
                magnitude = 'minor'
            return 'up', magnitude, change * -1  # Negative for improvement
        else:  # Declined (higher number = worse)
            change = current_pos - previous_pos
            if change >= 10:
                magnitude = 'major'
            elif change >= 5:
                magnitude = 'moderate'
            else:
                magnitude = 'minor'
            return 'down', magnitude, change