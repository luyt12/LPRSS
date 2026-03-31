# LatePost Daily Email

Automated daily email digest of LatePost (晚点 LatePost) articles.

## How It Works

1. Scrapes latest articles from LatePost website
2. Converts content to Markdown format
3. Sends a formatted HTML email daily

## Schedule

Runs automatically every day at 03:00 UTC via GitHub Actions.

## Setup

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `SMTP_PASS` | SMTP password / app password |
| `EMAIL_TO` | Recipient email address |
| `EMAIL_FROM` | Sender email address |
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP server port |
| `SMTP_USER` | SMTP login username |

### Manual Trigger

Go to **Actions** tab → **Daily LatePost Email** → **Run workflow**.

## Tech Stack

- Python 3.11
- GitHub Actions (scheduled)
- BeautifulSoup4 for article scraping
- SMTP over TLS (port 465)
