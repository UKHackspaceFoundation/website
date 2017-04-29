from django.db import models
from django.conf import settings
from django.contrib.auth.models import (AbstractUser,BaseUserManager)
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import gocardless_pro
import logging
import uuid
from .gocardless_mandate import GocardlessMandate
from datetime import datetime, timedelta

# get instance of a logger
logger = logging.getLogger(__name__)


# utility functions:
def get_gocardless_client():
    return gocardless_pro.Client(
        access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
        environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
    )


class SupporterMembershipManager(models.Manager):
    # get all membership records for user
    def get_membership_history(self, user):
        return super(SupporterMembershipManager, self).get_queryset().filter(user=user)

    # get latest membership for user
    def get_membership(self, user):
        return self.get_membership_history(user).latest('created_at')

    # get latest membership status for user
    def get_membership_status(self, user):
        try:
            return self.get_membership(user).status
        except SupporterMembership.DoesNotExist as e:
            return 'None'


class SupporterMembership(models.Model):

    APPROVAL_STATUS_CHOICES = (
        ("Pending", "Pending"),  # approval is pending
        ("Approved", "Approved"),  # application has been approved
        ("Rejected", "Rejected"),  # application has been rejected
    )

    # application status
    status = models.CharField(max_length=8, choices=APPROVAL_STATUS_CHOICES, default='Pending')
    # how many times have we successfully sent an approval request email:
    approval_request_count = models.IntegerField(default=0)
    # subscription fee (chosen by user)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=10.00)
    # application statement - aka: why i should be a member statement
    statement = models.TextField(blank=True)
    # when was the application membership created
    created_at = models.DateTimeField(default=timezone.now)
    # when was the first payment received
    started_at = models.DateField(null=True)
    # when did the membership expire
    expired_at = models.DateField(null=True)
    # what user is this associated with:
    user = models.ForeignKey('User', models.CASCADE)
    # gocardless redirect flow id
    redirect_flow_id = models.CharField(max_length=33, blank=True)
    # session token (for redirect flow)
    session_token = models.CharField(max_length=33, default='')

    objects = SupporterMembershipManager()

    class Meta:
        ordering = ["created_at"]
        db_table = 'supportermembership'
        app_label = 'main'

    def __str__(self):
        return self.user.name() + ' - ' + self.created_at.strftime('%Y-%m-%d')

    def is_active(self):
        if self.expired_at is not None:
            return self.status == 'Approved' and self.expired_at > timezone.now().date()
        else:
            return False

    # is there an active mandate?
    def has_active_mandate(self):
        try:
            return self.mandate().status != ''
        except GocardlessMandate.DoesNotExist as e:
            return False

    # get mandate status or throw DoesNotExist
    def mandate_status(self):
        return self.mandate().status

    # get latest mandate record for this supporter membership
    def mandate(self):
        return GocardlessMandate.objects.get_mandate_for_supporter_membership(self)

    # create a new gocardless redirect flow and return redirect_url
    def get_redirect_flow_url(self, request):
        # get gocardless client object
        client = get_gocardless_client()

        # generate a new session_token
        self.session_token = uuid.uuid4().hex

        # create a redirect_flow, pre-fill the users name and email
        redirect_flow = client.redirect_flows.create(
            params={
                "description" : "Hackspace Foundation Individual Membership",
                "session_token" : self.session_token,
                "success_redirect_url" : request.build_absolute_uri( reverse('join_supporter_step3') ),
                "prefilled_customer": {
                    "given_name": self.user.first_name,
                    "family_name": self.user.last_name,
                    "email": self.user.email
                }
            }
        )

        self.redirect_flow_id = redirect_flow.id
        self.save()

        return redirect_flow.redirect_url

    # attempt to complete a redirect flow and return new mandate object
    # will throw Gocardless and/or other exceptions
    def complete_redirect_flow(self, request):
        # get gocardless client object
        client = get_gocardless_client()

        # try to complete the redirect flow
        logger.info("Completing redirect flow")
        redirect_flow = client.redirect_flows.complete(
            request.GET.get('redirect_flow_id', ''),
            params = {
                'session_token': self.session_token
            }
        )

        # fetch the detailed mandate info
        logger.info("Fetch detailed mandate info")
        mandate_detail = client.mandates.get( redirect_flow.links.mandate )

        # create new mandate object
        logger.info("Create new mandate object")
        mandate = GocardlessMandate(
            id = redirect_flow.links.mandate,
            supporter_membership = self,
            reference = mandate_detail.reference,
            status = mandate_detail.status,
            customer_id = mandate_detail.links.customer,
            creditor_id = mandate_detail.links.creditor,
            customer_bank_account_id = mandate_detail.links.customer_bank_account
        )
        mandate.save()

        logger.info("Mandate object created: {}".format(mandate.id))
        return mandate

    # send approval request email
    def send_approval_request(self, request):
        # get template
        htmly = get_template('join_supporter/supporter_application_email.html')

        # build context
        d = Context({
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'note': self.statement,
            'fee': self.fee,
            'approve_url': request.build_absolute_uri(reverse('supporter-approval', kwargs={'session_token':self.session_token, 'action':'approve'} )),
            'reject_url': request.build_absolute_uri(reverse('supporter-approval', kwargs={'session_token':self.session_token, 'action':'reject'} ))
        })

        # prep headers
        subject = "Supporter Member Application from " + self.user.first_name +" " + self.user.last_name
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        to = getattr(settings, "BOARD_EMAIL", None)

        # render template
        message = htmly.render(d)
        try:
            # send email
            msg = EmailMessage(subject, message, to=[to], from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()

            # track how many times we've sent a request
            self.approval_request_count += 1;
            self.save()

        except Exception as e:
            # TODO: oh dear - how should we handle this gracefully?!?
            logger.error("Error in send_approval_request - failed to send email: "+str(e), extra={'SupporterMembership':self})


    # email user to notify of decision
    def send_application_decision(self):
        htmly = get_template('join_supporter/supporter_decision_email.html')

        d = Context({
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'fee': self.fee,
            'status': self.status
        })

        subject = "Hackspace Foundation Membership Application"
        from_email = getattr(settings, "BOARD_EMAIL", None)
        to = self.user.email
        message = htmly.render(d)
        try:
            msg = EmailMessage(subject, message, to=[to], from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()

            return True
        except Exception as e:
            logger.error("Error in send_application_decision - unable to send email: "+str(e), extra={'membership application':self})
            return False


    # approve the membership application (and create initial payment)
    def approve(self):

        # check user has not already been approved/rejected (e.g. by someone else!)
        if self.status != 'Pending':
            return False

        # update membership status
        self.status = 'Approved'
        self.save()

        self.send_application_decision()

        self.request_payment()

        return True


    # reject the membership application (and cancel mandate)
    def reject(self):

        # check user has not already been approved/rejected (e.g. by someone else!)
        if self.status != 'Pending':
            return False

        # update membership status
        self.status = 'Rejected'
        self.save()

        self.send_application_decision()

        if self.has_active_mandate():
            return self.mandate().cancel()

        return True


    # request new payment for this membership (e.g. start of a new year)
    def request_payment(self):
        if self.has_active_mandate():
            return self.mandate().create_payment(self.fee)


    def handle_payment_received(self, payment):
        if payment.payout_date is not None:
            # update started_at when first payment received
            self.started_at = payment.payout_date

            # update expired_at when new payment received
            print(payment.payout_date)
            print(timedelta(days=365))
            self.expired_at = payment.payout_date + timedelta(days=365)

            self.save()
        else:
            logger.error("handle_payment_received - payout_date is null")

        # TODO: send notification email of payment received and membership active


    def handle_mandate_updated(self, mandate):
        # TODO: something useful
        pass


    # TODO: get associated mandates
