from typing import Dict, List

#: Step-by-step DKIM setup guides per provider.
PROVIDER_DKIM_GUIDES: Dict[str, List[str]] = {
    "Google Workspace": [
        "Log in to the Google Workspace Admin console (admin.google.com).",
        "Go to Apps → Google Workspace → Gmail → Authenticate email.",
        "Select your domain and click 'Generate new record'.",
        "Set the DKIM key length to 2048 bits.",
        "Copy the generated TXT record value (selector: 'google').",
        "In your DNS provider, create a TXT record at 'google._domainkey.<yourdomain>'.",
        "Paste the generated value and save.",
        "Return to the Admin console and click 'Start authentication'.",
        "Send a test email and confirm dkim=pass in the headers.",
    ],
    "Microsoft 365": [
        "Log in to the Microsoft 365 Defender portal (security.microsoft.com).",
        "Go to Email & collaboration → Policies & rules → Threat policies → DKIM.",
        "Select your domain and toggle 'Sign messages for this domain with DKIM signatures' to ON.",
        "Copy the two CNAME records shown (selector1._domainkey and selector2._domainkey).",
        "In your DNS provider, create both CNAME records exactly as specified.",
        "Return to the Defender portal and click 'Enable' to activate DKIM signing.",
        "Allow up to 24 hours for DNS propagation, then send a test email.",
    ],
    "SendGrid": [
        "Log in to SendGrid and go to Settings → Sender Authentication.",
        "Click 'Authenticate Your Domain' and follow the setup wizard.",
        "Enter your domain name.",
        "SendGrid will show you two CNAME records (s1._domainkey and s2._domainkey).",
        "In your DNS provider, create both CNAME records exactly as shown.",
        "Return to SendGrid and click 'Verify'.",
        "Once verified, all outbound email will be DKIM signed automatically.",
    ],
    "Mailchimp": [
        "Log in to Mailchimp and go to Account & Billing → Domains.",
        "Click 'Authenticate' next to your domain.",
        "Mailchimp will display 3 CNAME records (k1, k2, k3 selectors).",
        "In your DNS provider, create all 3 CNAME records exactly as shown.",
        "Click 'Authenticate Domain' in Mailchimp.",
        "Allow up to 48 hours for DNS propagation before testing.",
    ],
    "Mailgun": [
        "Log in to Mailgun and go to Sending → Domains.",
        "Select your domain and open the DNS Records tab.",
        "Copy the DKIM TXT record(s) listed (selectors: pic, krs, mg, or mailo).",
        "In your DNS provider, create the TXT records at the specified hostnames.",
        "Click 'Verify DNS Settings' in Mailgun.",
        "Once verified, Mailgun will sign all outbound email automatically.",
    ],
    "Amazon SES": [
        "Log in to the AWS Console and open Amazon SES.",
        "Go to Configuration → Verified Identities and select your domain.",
        "Click 'View DKIM settings' and copy the 3 CNAME records shown.",
        "In your DNS provider, create all 3 CNAME records (SES uses unique random selectors).",
        "Return to SES and wait for the verification status to show 'Verified'.",
        "Enable 'Easy DKIM' with 2048-bit keys for maximum compatibility.",
    ],
    "Zendesk": [
        "Log in to Zendesk Admin Center.",
        "Go to Channels → Email → Domain's DKIM.",
        "Copy the two CNAME records shown (zendesk1._domainkey and zendesk2._domainkey).",
        "In your DNS provider, create both CNAME records exactly as specified.",
        "Return to Zendesk and click 'Verify'.",
    ],
}

#: SPF include directives per provider.
PROVIDER_SPF_INCLUDES: Dict[str, str] = {
    "Google Workspace": "_spf.google.com",
    "Microsoft 365": "spf.protection.outlook.com",
    "SendGrid": "sendgrid.net",
    "Mailchimp": "servers.mcsv.net",
    "Mailgun": "mailgun.org",
    "Amazon SES": "amazonses.com",
    "Zendesk": "mail.zendesk.com",
}
