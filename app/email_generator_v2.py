import random
import names
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Domain names for the USA
us_domains = ["gmail.com", "yahoo.com", "outlook.com", "iCloud.com", "verizon.net"]

def generate_code():
    import random
    abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    num = '1234567890'
    code_maker_list=[abc, num]
    code=''
    while len(code) < 3:
        resp = random.choice(abc[:])
        if not resp in code:
            code+=resp
    code+='-'

    for n in range(3):
        for m in range(4):
            code_maker=random.choice(code_maker_list)
            code+=random.choice(code_maker)

        if len(code) < 18:
            code+='-'

    return code

def generate_random_fullname_and_email():
    # Generate a random American name
    fullname= names.get_full_name()
    name = fullname.replace(" ", "").lower()

    emails = []
    for domain in us_domains:
        emails.append(f"{name}@{domain}")
    
    return fullname, emails

# Function to send HTML email
def send_html_email(from_address, password, to_address, to_address_fullname, website_url, user_message):
    message = MIMEMultipart('alternative')
    message['From'] = from_address
    message['To'] = to_address
    message['Subject'] = 'Exclusive Invitation Inside!'

    # HTML content of the email
    html_content = f"""
    <html>
    <head>
        <style>
            /* Define your CSS styles here */
            .email-container {{
                background: linear-gradient(to top left, #343a40 80%, #fff 10%, #c0c0c0 100%);
                text-align: center;
                padding: 50px;
                font-family: Arial, sans-serif;
                color: #fff;
            }}
            .header {{
                color: green;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .message {{
                color: #fff;
                font-size: 18px;
                margin-bottom: 30px;
            }}
            .cta-button {{
                display: inline-block;
                padding: 15px 30px;
                background-color: #ffcc00;
                color: #fff;
                text-decoration: none;
                border-radius: 5px;
                font-size: 18px;
                margin-right: 20px;
                transition: background-color 0.3s ease;
            }}
            .cta-button:hover {{
                background-color: #ffdb4d;
            }}
        </style>
    </head>
    <body style="padding:15px; background: #c0c0c0;">
        <div class="email-container">
            <div class="header">Hello there!</div>
            <div class="message">
                <p>Discover the latest and greatest at our website!</p>
                <p>Explore a world of exciting offers and exclusive content waiting just for you @ {website_url}.</p>
                <hr>
                <pre>
                    {to_address_fullname}, {user_message}
                </pre>
                <hr>

            </div>
            <a href="{website_url}" class="cta-button">Explore Now</a>
            <a href="{website_url}/special-offers" class="cta-button">View Special Offers</a>
        </div>
    </body>
    </html>
    """

    # Attach HTML content to the email
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_address, password)  # Replace with your email password

        response=server.sendmail(from_address, to_address, message.as_string())
        server.quit()
        print(response)

        return True  # Email sent successfully
    except smtplib.SMTPServerDisconnected:
        return False  # Failed to connect to the server

def bomb_details(counter):
    # Generate random USA emails base on count
    mails = []
    details={}
    for _ in range(counter):
        fullname, emails = generate_random_fullname_and_email()
        trials = 0
        while emails[0] in mails:
            fullname, emails = generate_random_fullname_and_email()
            trials += 1
            if trials >= 10:
                break

        mails.extend(emails)
        details[fullname]=emails
    return details

def send_generated_mass_mail(from_address, password, website_url, counter, user_message):
    details = bomb_details(counter)
    # Send HTML email to each generated email address
    for fullname in details:
        emails = details[fullname]
        for email in emails:
            to_address=email
            to_address_fullname = fullname
            sent = send_html_email(from_address, password, to_address, to_address_fullname, website_url, user_message)  # Replace with your actual website URL
            print(f"Email sent to {to_address_fullname} on {email}: {sent}")
    return details

def main():
    from_address = 'keanureevesofficialcares@gmail.com'
    password = 'hmhrnbkzglqjdmbj'
    website_url = "https://keanureevesofficialcares.pythonanywhere.com/"
    user_message = "You have the lawful right to claim the Giveaway winning prize without any further delay using {generate_code()}... Explore now to get your claiming profile immediately."
    try:
        send_generated_mass_mail(from_address, password, website_url, counter, user_message)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()