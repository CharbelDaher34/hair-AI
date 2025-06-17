# Email OTP Verification Setup Guide

This guide explains how to set up email OTP verification for the job application form.

## Overview

The system now requires candidates to verify their email address before submitting job applications. This is implemented using:

- **Backend**: FastAPI with aiosmtplib for sending emails
- **Frontend**: React with OTP input component
- **Security**: 6-digit OTP codes with 10-minute expiration

## Features

- ✅ Email verification required for job applications
- ✅ 6-digit OTP codes sent via email
- ✅ 10-minute expiration time with countdown timer
- ✅ Rate limiting (max 5 verification attempts)
- ✅ Resend functionality
- ✅ Beautiful email templates
- ✅ Real-time UI feedback
- ✅ Automatic cleanup of expired OTPs

## Email Configuration

### 1. Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Copy the 16-character password

3. **Update Docker Compose**:
   ```yaml
   environment:
     - SMTP_HOST=smtp.gmail.com
     - SMTP_PORT=587
     - SMTP_USERNAME=your-email@gmail.com
     - SMTP_PASSWORD=your-16-char-app-password
     - FROM_EMAIL=your-email@gmail.com
   ```

### 2. Other Email Providers

#### Outlook/Hotmail
```yaml
environment:
  - SMTP_HOST=smtp-mail.outlook.com
  - SMTP_PORT=587
  - SMTP_USERNAME=your-email@outlook.com
  - SMTP_PASSWORD=your-password
  - FROM_EMAIL=your-email@outlook.com
```

#### Custom SMTP
```yaml
environment:
  - SMTP_HOST=your-smtp-server.com
  - SMTP_PORT=587  # or 465 for SSL
  - SMTP_USERNAME=your-username
  - SMTP_PASSWORD=your-password
  - FROM_EMAIL=noreply@yourcompany.com
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` | Yes |
| `SMTP_PORT` | SMTP server port | `587` | Yes |
| `SMTP_USERNAME` | SMTP username/email | - | Yes |
| `SMTP_PASSWORD` | SMTP password/app password | - | Yes |
| `FROM_EMAIL` | Sender email address | `SMTP_USERNAME` | No |
| `OTP_EXPIRE_MINUTES` | OTP expiration time in minutes | `10` | No |
| `OTP_LENGTH` | Length of OTP code | `6` | No |

## API Endpoints

### Send OTP
```http
POST /api/v1/candidates/send-otp
Content-Type: application/json

{
  "email": "candidate@example.com",
  "full_name": "John Doe"
}
```

### Verify OTP
```http
POST /api/v1/candidates/verify-otp
Content-Type: application/json

{
  "email": "candidate@example.com",
  "otp_code": "123456"
}
```

### Check OTP Status
```http
GET /api/v1/candidates/otp-status/candidate@example.com
```

## Frontend Integration

The job application form now includes:

1. **Email Input with Verification Button**
2. **OTP Input Component** (6-digit code entry)
3. **Timer Display** (shows remaining time)
4. **Resend Functionality**
5. **Verification Status Indicators**

### Key Components Used

- `InputOTP` - 6-digit code input
- `InputOTPGroup` - Groups OTP slots
- `InputOTPSlot` - Individual digit slots

## Security Features

### Rate Limiting
- Maximum 5 verification attempts per email
- Account lockout after failed attempts
- Automatic cleanup of expired codes

### Validation
- Email format validation
- OTP code length validation
- Expiration time enforcement
- Duplicate submission prevention

### Error Handling
- Network error recovery
- User-friendly error messages
- Graceful degradation

## Troubleshooting

### Common Issues

1. **"Failed to send OTP"**
   - Check SMTP credentials
   - Verify network connectivity
   - Check email provider settings

2. **"OTP expired"**
   - Default expiration is 10 minutes
   - Request a new code
   - Check system time synchronization

3. **"Too many attempts"**
   - Wait for cleanup cycle (5 minutes)
   - Or restart the backend service

### Testing

1. **Test Email Sending**:
   ```bash
   curl -X POST http://localhost:8017/api/v1/candidates/send-otp \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","full_name":"Test User"}'
   ```

2. **Test OTP Verification**:
   ```bash
   curl -X POST http://localhost:8017/api/v1/candidates/verify-otp \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","otp_code":"123456"}'
   ```

### Logs

Monitor backend logs for email-related messages:
```bash
docker logs backend | grep -E "\[OTP\]|\[Email\]"
```

## Production Considerations

### Email Deliverability
- Use a dedicated email service (SendGrid, AWS SES, etc.)
- Set up SPF, DKIM, and DMARC records
- Monitor bounce rates and spam complaints

### Scalability
- Consider using Redis for OTP storage
- Implement proper rate limiting
- Add email queue for high volume

### Security
- Use environment variables for credentials
- Enable TLS/SSL for SMTP
- Implement additional fraud detection

## Development Notes

### File Structure
```
backend/app/
├── services/
│   ├── email_service.py      # Email sending logic
│   └── otp_service.py        # OTP generation/verification
├── api/v1/endpoints/
│   └── candidate.py          # OTP endpoints
└── core/
    └── config.py             # Email configuration

frontend/src/
├── pages/
│   └── JobApplicationForm.tsx # Updated with OTP verification
└── services/
    └── api.js                # OTP API methods
```

### Dependencies Added
- **Backend**: `aiosmtplib`, `email-validator`
- **Frontend**: Uses existing `input-otp` component

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify email configuration
3. Test with a simple email first
4. Check network connectivity and firewall settings 