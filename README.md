# 🐍 SEO Rank Tracker

A comprehensive SEO rank tracking application built with Python Flask, PostgreSQL, and Celery for automated keyword ranking monitoring, email reporting, and data analytics.

## ✨ Features

- **Automated Rank Tracking**: Weekly scheduled checks using SerpAPI
- **Email Reports**: Beautiful HTML email reports with ranking changes
- **Web Dashboard**: Real-time view of current rankings and changes
- **REST API**: JSON endpoints for external integrations
- **Background Processing**: Celery-powered async task processing
- **Docker Ready**: Complete containerized deployment
- **Position Analysis**: Track improvements, declines, and ranking history
- **Rate Limiting**: Built-in API rate limiting compliance

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- SerpAPI account and API key
- Gmail account with app password (for email reports)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/son-content-mastery/cm-seo-rank-tracker.git
cd cm-seo-rank-tracker

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Configure Environment

Update `.env` with your settings:

```bash
# Required: SerpAPI key
SERPAPI_KEY=your_serpapi_key_here

# Required: Gmail credentials
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your_gmail_app_password

# Required: Your domain and email
TARGET_DOMAIN=yourdomain.com
RECIPIENT_EMAIL=your-email@gmail.com

# Generate a secret key
SECRET_KEY=your_secret_key_here
```

### 3. Deploy with Docker

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Access the application
open http://localhost:5000
```

## 📊 Application Structure

```
seo-rank-tracker/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Application container
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── app/
│   ├── __init__.py           # Flask application factory
│   ├── config.py             # Configuration settings
│   ├── models.py             # Database models
│   ├── routes.py             # Web routes and API endpoints
│   ├── tasks.py              # Celery background tasks
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── keywords.html
│   ├── email_templates/      # Email templates
│   │   └── weekly_report.html
│   └── utils/                # Utility modules
│       ├── serpapi_client.py # SerpAPI integration
│       ├── email_sender.py   # Email functionality
│       └── report_generator.py # Report generation
└── migrations/
    └── init.sql              # Database schema
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SERPAPI_KEY` | Your SerpAPI key | Yes | - |
| `GMAIL_USER` | Gmail address for sending reports | Yes | - |
| `GMAIL_PASSWORD` | Gmail app password | Yes | - |
| `TARGET_DOMAIN` | Domain to track rankings for | Yes | yourdomain.com |
| `RECIPIENT_EMAIL` | Email for receiving reports | Yes | - |
| `SECRET_KEY` | Flask secret key | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | No | Auto-configured |
| `REDIS_URL` | Redis connection string | No | Auto-configured |

### Keywords Configuration

Default keywords are configured in `app/config.py`. You can:

1. **Edit the config file** to change default keywords
2. **Use the web interface** to add/remove keywords
3. **Use environment variables** (add `CUSTOM_KEYWORDS=keyword1,keyword2,keyword3`)

## 📈 Usage

### Web Dashboard

Access the dashboard at `http://localhost:5000`:

- **Dashboard**: View current rankings and changes
- **Keywords**: Manage tracked keywords
- **Manual Checks**: Trigger immediate ranking checks
- **Send Reports**: Generate and send email reports

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rankings` | GET | Current rankings (JSON) |
| `/api/keyword/{id}/history` | GET | Keyword ranking history |
| `/health` | GET | Application health check |
| `/trigger-check` | POST | Manual ranking check |
| `/send-report` | POST | Send email report |

### Example API Usage

```bash
# Get current rankings
curl http://localhost:5000/api/rankings

# Get keyword history
curl http://localhost:5000/api/keyword/1/history?days=30

# Health check
curl http://localhost:5000/health
```

## 📧 Email Reports

Weekly email reports include:

- **Summary Statistics**: Total keywords, coverage rate, average position
- **Change Analysis**: Improvements, declines, new rankings
- **Detailed Table**: All keywords with positions and changes
- **Visual Indicators**: Color-coded change indicators

Reports are automatically sent every Monday at 9 AM UTC.

## 🔄 Scheduling

The application uses Celery Beat for scheduling:

- **Weekly Rank Check**: Monday 9:00 AM UTC
- **Data Cleanup**: Sunday 2:00 AM UTC (removes data older than 365 days)

### Manual Operations

```bash
# Run manual check
docker-compose exec web python -c "from app.tasks import run_manual_check; run_manual_check()"

# Run cleanup
docker-compose exec web python -c "from app.tasks import run_manual_cleanup; run_manual_cleanup()"
```

## 📊 Database Schema

### Tables

- **keywords**: Stores tracked keywords
- **rankings**: Daily ranking data
- **ranking_changes**: Position change history

### Key Features

- **Automatic indexing** for optimal query performance
- **Database views** for complex queries
- **Functions** for statistical calculations
- **Constraints** for data integrity

## 🔧 Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up local database
createdb seo_tracker
psql seo_tracker < migrations/init.sql

# Run Flask development server
export FLASK_APP=app
export FLASK_ENV=development
flask run

# Run Celery worker (separate terminal)
celery -A app.tasks worker --loglevel=info

# Run Celery beat (separate terminal)
celery -A app.tasks beat --loglevel=info
```

### Adding Features

1. **Models**: Add new tables in `app/models.py`
2. **Routes**: Add endpoints in `app/routes.py`
3. **Tasks**: Add background jobs in `app/tasks.py`
4. **Templates**: Add HTML templates in `app/templates/`
5. **Utils**: Add utilities in `app/utils/`

## 🚨 Troubleshooting

### Common Issues

**API Key Issues**
```bash
# Check SerpAPI key
curl "https://serpapi.com/account" -H "Authorization: Bearer YOUR_API_KEY"
```

**Email Issues**
```bash
# Test Gmail credentials
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
```

**Database Issues**
```bash
# Check database connection
docker-compose exec db psql -U seo_user -d seo_tracker -c "SELECT COUNT(*) FROM keywords;"
```

**Celery Issues**
```bash
# Check Celery status
docker-compose exec worker celery -A app.tasks status
docker-compose exec scheduler celery -A app.tasks beat --dry-run
```

### Logs

```bash
# Application logs
docker-compose logs web

# Worker logs
docker-compose logs worker

# Scheduler logs
docker-compose logs scheduler

# Database logs
docker-compose logs db
```

## 📈 Performance Optimization

### Rate Limiting

- SerpAPI calls are rate-limited to 1.2 seconds between requests
- Configurable via `SERPAPI_RATE_LIMIT` environment variable
- Batch processing for multiple keywords

### Database Optimization

- Automatic cleanup of old data (365+ days)
- Indexed queries for fast lookups
- Database views for complex reporting

### Monitoring

- Health check endpoint at `/health`
- Comprehensive logging throughout the application
- Task monitoring via Celery

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` files
- **API Keys**: Use environment variables only
- **Database**: Use strong passwords
- **Email**: Use Gmail app passwords, not account passwords
- **Network**: Consider firewall rules for production

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:

1. Check this README
2. Review application logs
3. Check the troubleshooting section
4. Open an issue on GitHub

---

**Created by Son [contentmastery.io](https://contentmastery.io)**