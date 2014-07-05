# -*- coding: utf-8 -*-

from django.conf import settings
from django.core import mail
from django.template.loader import get_template
from django.template import Context
from django.core.mail import EmailMultiAlternatives
import re

#single point of change
SENDER_EMAIL_ADDRESS = settings.EMAIL_HOST_USER

# sends mail only to specified email-addresses if dev mode
def send_mail(subject, message, from_email, to_emails):
    okmails = []
    if settings.DEBUG is False:
        okmails = to_emails
    else:
        # in debug mode send to dummy address
        okmails = [settings.DEBUG_EMAIL_ADDRESS]
        print "Mail intended for " + ", ".join(to_emails) + " rerouted to " + settings.DEBUG_EMAIL_ADDRESS
    
    if len(okmails) > 0:
        for amail in okmails:
            res = mail.send_mail(subject, message, from_email, [amail], fail_silently=False)
            print 'Sending mail from ' + from_email + ' to ' + amail 
            print ' res= ', res
        
    # todo remove again later, for now send a copy every time
    message_verbose =  message + '\n\nCopy of original sent to: ' + ', '.join(to_emails)
    res = mail.send_mail(subject, message_verbose, from_email, [settings.DEBUG_EMAIL_ADDRESS], fail_silently=False)

    return None


def send_mail_multi(email_multi_message):
    to_emails = email_multi_message.to
    okmails = []
    if settings.DEBUG is False:
        okmails = email_multi_message.to
    else:
        okmails = [settings.DEBUG_EMAIL_ADDRESS]
        print "Multi-Mail intended for " + ", ".join(to_emails) + " rerouted to " + settings.DEBUG_EMAIL_ADDRESS
        
    if len(okmails) > 0:
        email_multi_message.to = []
        email_multi_message.bcc = okmails
        res = email_multi_message.send()
        print "res = ", res
        print "Mail sent to " + ", ".join(okmails) + (", on whitelist" if settings.DEBUG else "")
        
    # todo remove again later, for now send a copy every time
    message_verbose =  email_multi_message.body + '\n\nCopy of original sent to: ' + ', '.join(to_emails)
    res = mail.send_mail(email_multi_message.subject, message_verbose, email_multi_message.from_email, [settings.DEBUG_EMAIL_ADDRESS], fail_silently=False)

    return None


def send_new_loco_in_taetigkeitsbereich_to_bg(area, loco):
    send_mail('Neues Mitglied im Taetigkeitsbereich ' + area.name,
              'Soeben hat sich ' + loco.first_name + " " + loco.last_name + ' in den Taetigkeitsbereich ' + area.name + ' eingetragen', SENDER_EMAIL_ADDRESS, [area.coordinator.email])


def send_contact_form(subject, message, loco, copy_to_loco):
    send_mail('Anfrage per ' + settings.SITE_MY_URL + ': ' + subject, message, loco.email, [SENDER_EMAIL_ADDRESS])
    if copy_to_loco:
        send_mail('Anfrage per ' + settings.SITE_MY_URL + ': ' + subject, message, loco.email, [loco.email])


def send_welcome_mail(email, password, server):
    plaintext = get_template('mails/welcome_mail.txt')
    htmly = get_template('mails/welcome_mail.html')

    # reset password so we can send it to him
    d = Context({
        'subject': 'Willkommen bei ' + settings.SITE_NAME,
        'username': email,
        'password': password,
        'serverurl': "http://" + server
    })

    text_content = plaintext.render(d)
    html_content = htmly.render(d)

    msg = EmailMultiAlternatives('Willkommen bei ' + settings.SITE_NAME, text_content, SENDER_EMAIL_ADDRESS, [email])
    msg.attach_alternative(html_content, "text/html")
    send_mail_multi(msg)


def send_been_added_to_abo(email, password, name, anteilsscheine, hash, server):
    plaintext = get_template('mails/welcome_added_mail.txt')
    htmly = get_template('mails/welcome_added_mail.html')

    # reset password so we can send it to him
    d = Context({
        'subject': 'Willkommen bei ' + settings.SITE_NAME,
        'username': email,
        'name': name,
        'password': password,
        'hash': hash,
        'anteilsscheine': anteilsscheine,
        'serverurl': "http://" + server
    })

    text_content = plaintext.render(d)
    html_content = htmly.render(d)

    msg = EmailMultiAlternatives('Willkommen bei ' + settings.SITE_NAME, text_content, SENDER_EMAIL_ADDRESS, [email])
    msg.attach_alternative(html_content, "text/html")
    send_mail_multi(msg)


def send_filtered_mail(subject, message, text_message, emails, server):
    plaintext = get_template('mails/filtered_mail.txt')
    htmly = get_template('mails/filtered_mail.html')

    htmld = Context({
        'subject': subject,
        'content': message,
        'serverurl': "http://" + server
    })
    textd = Context({
        'subject': subject,
        'content': text_message,
        'serverurl': "http://" + server
    })

    text_content = plaintext.render(textd)
    html_content = htmly.render(htmld)

    msg = EmailMultiAlternatives(subject, text_content, SENDER_EMAIL_ADDRESS, emails)
    msg.attach_alternative(html_content, "text/html")
    send_mail_multi(msg)


def send_politoloco_mail(subject, message, text_message, emails, server):
    plaintext = get_template('mails/politoloco.txt')
    htmly = get_template('mails/politoloco.html')

    htmld = Context({
        'subject': subject,
        'content': message,
        'serverurl': "http://" + server
    })
    textd = Context({
        'subject': subject,
        'content': text_message,
        'serverurl': "http://" + server
    })

    text_content = plaintext.render(textd)
    html_content = htmly.render(htmld)

    msg = EmailMultiAlternatives(subject, text_content, SENDER_EMAIL_ADDRESS, emails)
    msg.attach_alternative(html_content, "text/html")
    send_mail_multi(msg)


def send_mail_password_reset(email, password, server):
    plaintext = get_template('mails/password_reset_mail.txt')
    htmly = get_template('mails/password_reset_mail.html')
    subject = 'Dein neues ' + settings.SITE_NAME + ' Passwort'

    htmld = Context({
        'subject': subject,
        'email': email,
        'password': password,
        'serverurl': "http://" + server
    })
    textd = Context({
        'subject': subject,
        'email': email,
        'password': password,
        'serverurl': "http://" + server
    })

    text_content = plaintext.render(textd)
    html_content = htmly.render(htmld)

    msg = EmailMultiAlternatives(subject, text_content, SENDER_EMAIL_ADDRESS, [email])
    msg.attach_alternative(html_content, "text/html")
    send_mail_multi(msg)


def send_job_reminder(emails, job, participants, server):
    plaintext = get_template('mails/job_reminder_mail.txt')
    htmly = get_template('mails/job_reminder_mail.html')

    d = Context({
        'job': job,
        'participants': participants,
        'serverurl': "http://" + server
    })

    text_content = plaintext.render(d)
    html_content = htmly.render(d)

    msg = EmailMultiAlternatives(settings.SITE_NAME + " - Job-Erinnerung", text_content, SENDER_EMAIL_ADDRESS, emails)
    msg.attach_alternative(html_content, "text/html")
    send_mail_multi(msg)
