import smtplib
from email.mime.text import MIMEText
import os

def enviar_correo_html(destino: str, asunto: str, cuerpo_html: str,
                       remitente_email: str, remitente_nombre: str,
                       bcc_list: list = None):

    if not remitente_email:
        remitente_email = "tecnico@ceibcn.com"
    if not remitente_nombre:
        remitente_nombre = "CRM"

    msg = MIMEText(cuerpo_html, "html", "utf-8")
    msg["Subject"] = asunto
    msg["From"] = f"{remitente_nombre} <{remitente_email}>"
    msg["To"] = destino

    # Destinataris reals per a l’enviament SMTP
    recipients = [destino]

    # Afegir BCC al conjunt d’enviament (però no a la capçalera)
    if bcc_list:
        recipients.extend(bcc_list)

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    print("DEBUG SMTP:", smtp_host, smtp_port, smtp_user)
    print("FROM:", msg["From"])
    print("TO:", destino)
    print("BCC:", bcc_list)

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.set_debuglevel(1)
    server.starttls()
    server.login(smtp_user, smtp_pass)

    # IMPORTANT: enviar el llistat complet de destinataris (To + BCC)
    server.send_message(msg, from_addr=remitente_email, to_addrs=recipients)
    server.quit()
def wrap_email_html(body_html: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
</head>
<body style="margin:0;padding:0;background:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:20px;">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;padding:24px;font-family:Arial,sans-serif;font-size:14px;color:#333;">
          <tr>
            <td>
              {body_html}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
