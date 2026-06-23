import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from jinja2 import Template
from schemas import ListingSchema

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
  .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 24px; }
  h1 { color: #1a73e8; font-size: 22px; }
  .listing { display: flex; border: 1px solid #e0e0e0; border-radius: 8px; margin: 12px 0; overflow: hidden; }
  .listing img { width: 120px; height: 120px; object-fit: cover; }
  .listing-info { padding: 12px; flex: 1; }
  .listing-title { font-weight: bold; font-size: 15px; color: #333; text-decoration: none; }
  .listing-title:hover { color: #1a73e8; }
  .listing-price { color: #e53935; font-size: 18px; font-weight: bold; margin: 6px 0; }
  .platform { display: inline-block; background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
  .footer { text-align: center; color: #999; font-size: 12px; margin-top: 24px; }
</style>
</head>
<body>
<div class="container">
  <h1>🔔 Nuovi annunci per "{{ query }}"</h1>
  <p>Abbiamo trovato <strong>{{ listings|length }}</strong> nuovi annunci{% if max_price %} sotto {{ max_price }}€{% endif %}:</p>
  {% for listing in listings %}
  <div class="listing">
    {% if listing.image_url %}<img src="{{ listing.image_url }}" alt="">{% endif %}
    <div class="listing-info">
      <a class="listing-title" href="{{ listing.url }}">{{ listing.title }}</a>
      {% if listing.price %}<div class="listing-price">{{ listing.price }}€</div>{% endif %}
      <span class="platform">{{ listing.platform }}</span>
      {% if listing.location %}<span style="color:#666; font-size:13px;"> · {{ listing.location }}</span>{% endif %}
    </div>
  </div>
  {% endfor %}
</div>
<div class="footer">UsatoFinder — Ricerca automatica usato</div>
</body>
</html>
""")


async def send_notification(email: str, query: str, listings: list[ListingSchema], max_price: float | None = None):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    email_from = os.getenv("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_password:
        logger.error("SMTP credentials not configured")
        return

    html_body = EMAIL_TEMPLATE.render(query=query, listings=listings, max_price=max_price)

    msg = MIMEMultipart("alternative")
    msg["From"] = email_from
    msg["To"] = email
    msg["Subject"] = f"UsatoFinder: {len(listings)} nuovi annunci per \"{query}\""
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
        )
        logger.info("Email sent to %s for query '%s' (%d listings)", email, query, len(listings))
    except Exception as e:
        logger.error("Failed to send email: %s", e)
