from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.edit import CreateView
from .models import Space, SupporterMembership, GocardlessMandate, GocardlessPayment
from .forms import CustomUserCreationForm, SupporterMembershipForm, NewSpaceForm
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
import markdown
from urllib.parse import urljoin
from main.models import User
from dealer.git import git
from django.conf import settings
from django.views.generic.edit import UpdateView, FormView
from django.urls import reverse_lazy, reverse
from django import forms
import gocardless_pro
import uuid
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.template import Context
import logging


# get instance of a logger
logger = logging.getLogger(__name__)


def index(request):
    activeSpaces = Space.objects.active_spaces()
    inactiveSpaces = Space.objects.inactive_spaces()
    return render(request, 'main/index.html', {
        'activeSpaces': activeSpaces,
        'inactiveSpaces': inactiveSpaces,
        'MAPBOX_ACCESS_TOKEN': getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
    })


# profile page for registered users
@login_required
def profile(request):
    associated_users = User.objects.filter(space=request.user.space, space_status='Approved')
    payments = None

    # TODO: provide payment summary to template

    return render(request, 'main/profile.html', {
        'MAPBOX_ACCESS_TOKEN': getattr(settings, "MAPBOX_ACCESS_TOKEN", None),
        'associated_users': associated_users,
        'payments': payments
    })


class UserUpdate(LoginRequiredMixin, UpdateView):
    model = User
    success_url = '/profile'
    form_class = CustomUserCreationForm

    # make request object available to form
    def get_form_kwargs(self):
        kw = super(UserUpdate, self).get_form_kwargs()
        kw['request'] = self.request
        return kw

    # ensure the logged in user object is passed to the view/form
    def get_object(self, queryset=None):
        return self.request.user


class SpaceUpdate(LoginRequiredMixin, UpdateView):
    model = Space
    fields = ['name', 'status', 'main_website_url', 'email','have_premises', 'address_first_line', 'town', 'region', 'postcode', 'country', 'lat', 'lng', 'logo_image_url']
    success_url = '/profile'

    def get_object(self, queryset=None):
        return self.request.user.space

    def get_context_data(self, **kwargs):
        context = super(SpaceUpdate, self).get_context_data(**kwargs)
        context['MAPBOX_ACCESS_TOKEN'] = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
        return context

    def dispatch(self, request, *args, **kwargs):
        # make sure users have space_status='Approved'
        if self.request.user.space_status != 'Approved':
            # otherwise redirect to profile
            return redirect(reverse_lazy('profile'))
        return super(SpaceUpdate, self).dispatch(request, *args, **kwargs)


# return space info as json - used for rendering map on homepage
def spaces(request):
    return JsonResponse( Space.objects.as_json() )


@login_required
def gitinfo(request):
    context = {
        'tag': git.tag
    }
    return render(request, 'main/gitinfo.html', context)


# return space info as geojson
def geojson(request):
    geo = Space.objects.as_geojson()
    return JsonResponse(geo)


@staff_member_required(login_url='/login')
def space_detail(request):
    return render(request, 'main/space_detail.html', {'spaces': Space.objects.all()})


def valueOrBlank(obj, attr, d):
    if attr in obj:
        return obj[attr]
    else:
        return d


@staff_member_required(login_url='/login')
def import_spaces(request):
    json_data = open('static/data.json')
    data = json.load(json_data)

    for s in data:

        # see if record already exists
        q = Space.objects.filter(name=s['name'])
        if len(q) == 0:
            srecord = Space(
                name=valueOrBlank(s, 'name', ''),
                town=valueOrBlank(s, 'town', ''),
                country=valueOrBlank(s, 'country', ''),
                region=valueOrBlank(s, 'region', ''),
                have_premises=valueOrBlank(s, 'havePremises', 'No') == 'Yes',
                address_first_line=valueOrBlank(s, 'addressFirstLine', ''),
                postcode=valueOrBlank(s, 'postcode', ''),
                lat=valueOrBlank(s, 'lat', 0.0),
                lng=valueOrBlank(s, 'lng', 0.0),
                main_website_url=valueOrBlank(s, 'mainWebsiteUrl', ''),
                logo_image_url=valueOrBlank(s, 'logoImageUrl', ''),
                status=valueOrBlank(s, 'status', ''),
                email=valueOrBlank(s, 'contactEmail', ''),
            )
            srecord.save()
        # else
            # existing record, do nothing for now
    return redirect(reverse_lazy('space_detail'))


@login_required
def join(request):
    return render(request, 'join/join.html')


class JoinSupporterStep1(LoginRequiredMixin, CreateView):
    form_class = SupporterMembershipForm
    success_url = reverse_lazy('join_supporter_step2')
    template_name = 'join_supporter/step1.html'

    def dispatch(self, request, *args, **kwargs):
        # if user already has an active membership then return to profile page
        if request.user.supporter_status() != 'None':
            messages.error(request, 'You already have an active membership', extra_tags='alert-danger')
            logger.error("Error in JoinSupporterStep1 - user has an existing membership", extra={'user':request.user})
            return redirect(reverse('profile'))

        return super(JoinSupporterStep1, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # hook up the new application to the current user
        form.instance.user = self.request.user
        return super().form_valid(form)


@login_required
def join_supporter_step2(request):
    try:
        # get membership application
        ma = request.user.supporter_membership()

        try:
            # see if the application already has a mandate
            mandate = ma.mandate()

            # if it's active...
            if mandate.is_active():
                # redirect to step 3:
                return redirect(reverse('join_supporter_step3'))

        except GocardlessMandate.DoesNotExist as e:
            # if not, continue...
            pass

        # redirect user to create a new mandate
        return redirect( ma.get_redirect_flow_url(request) )

    except SupporterMembership.DoesNotExist as e:
        # odd, user does not have an active membership application - send them to step1
        logger.error("Error in join_supporter_step2 - user does not have a membership application", extra={'user':request.user})
        return redirect(reverse('join_supporter_step1'))


@login_required
def join_supporter_step3(request):

    try:
        # get membership application
        ma = request.user.supporter_membership()
        mandate = None

        try:
            # see if the application already has a mandate
            mandate = ma.mandate()

        except GocardlessMandate.DoesNotExist as e:
            # if not, complete the flow and create a new mandate record
            mandate = ma.complete_redirect_flow(request)

        # now do the email approval stuff
        ma.send_approval_request(request)

        # finally, render the completion page
        return render(request, 'join_supporter/supporter_step3.html')


    except SupporterMembership.DoesNotExist as e:
        # odd, user does not have an active membership application - send them to step1
        logger.error("Error in join_supporter_step3 - user does not have a membership application", extra={'user':request.user})
        return redirect(reverse('join_supporter_step1'))



def supporter_approval(request, session_token, action):

    if action != 'approve' and action != 'reject':
        # this shouldn't happen - just redirect to home
        logger.error("Error in supporter_approval - unexpected action: "+action, extra={'user':request.user})
        return redirect(reverse_lazy('index'))

    try:
        # lookup user info based on key
        user = User.objects.get(gocardless_session_token=session_token)

        # check user has not already been approved/rejected (e.g. by someone else!)
        if user.member_status != 'Pending':
            messages.error(request, "Error - "+ user.first_name+" appears to have already been " + user.member_status, extra_tags='alert-danger')
            return render(request, 'base.html')


        # update user object
        user.member_status = 'Approved' if action=='approve' else 'Rejected'

        user.save()

        # email user to notify of decision
        htmly = get_template('join_supporter/supporter_decision_email.html')

        d = Context({
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'fee': user.member_fee,
            'action': action
        })

        subject = "Hackspace Foundation Membership Application"
        from_email = getattr(settings, "BOARD_EMAIL", None)
        to = user.email
        message = htmly.render(d)
        try:
            msg = EmailMessage(subject, message, to=[to], from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()
        except Exception as e:
            # TODO: oh dear - how should we handle this gracefully?!?
            logger.error("Error in supporter_approval - unable to send email: "+str(e), extra={'user':request.user})


        # get gocardless client object
        client = gocardless_pro.Client(
            access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
            environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
        )

        # if approved, request gocardless payment
        if action == 'approve':


            # generate idempotency key
            key = uuid.uuid4().hex

            try:
                # create payment
                payment = client.payments.create(
                    params={
                        "amount" : int(user.member_fee * 100), # convert to pence
                        "currency" : "GBP",
                        "links" : {
                            "mandate": user.gocardless_mandate_id
                        },
                        "metadata": {
                            "type":"SupporterSubscription"
                            # TODO: decide if we want to add metadata to the payment
                        }
                    }, headers={
                        'Idempotency-Key' : key
                })

                # Store payment object
                payment.idempotency_key = key
                obj = GocardlessPayment.objects.get_or_create_from_payload(payment)

                # add user relationship to object
                obj.user = user
                obj.save()


            except Exception as e:
                logger.error("Error in supporter_approval - exception creating payment: "+repr(e), extra={'user':user})



        # if rejected, then cancel mandate
        else:

            try:
                # cancel mandate
                mandate = client.mandates.cancel(user.gocardless_mandate_id)


                # reset gocardless info on user object
                user.gocardless_mandate_id = '';
                user.gocardless_customer_id = '';
                user.gocardless_redirect_flow_id = '';

                user.save()


            except Exception as e:
                logger.error("Error in supporter_approval - exception cancelling mandate: "+repr(e), extra={'user':request.user})


        # make a context object for the template to render
        context = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email':user.email,
            'action': ('approving' if action=='approve' else 'rejecting')
        }
        return render(request, 'join_supporter/supporter_approval.html', context)

    except User.DoesNotExist as e:
        # aargh - that's not right - redirect to home
        logger.error("Error in supporter_approval - user does not exist: "+str(e), extra={'user':request.user})
        return redirect(reverse_lazy('index'))



class Login(View):
    def get(self, request):
        return render(request, 'main/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)

            # mark user as active (must have completed signup if they are able to login)
            if not user.active:
                user.active = True
                user.save()

            # FIXME: Redirect to page in 'next' query param ?
            return redirect(reverse_lazy('profile'))
        else:
            messages.error(request, "Invalid username or password", extra_tags='alert-danger')
            logger.error("Error in Login - invalid username or password: "+username)
            return render(request, 'main/login.html')


def logout_view(request):
    logout(request)
    return redirect(reverse_lazy('index'))


def new_space(request):
    form_class = NewSpaceForm

    try:
        if request.method == 'POST':
            form = form_class(request.POST)

            if form.is_valid():

                template = get_template('main/new_space_email.txt')
                context = Context({ 'form': form.cleaned_data })
                content = template.render(context)

                email = EmailMessage(
                    "New space form submission",
                    content,
                    getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    [getattr(settings, "BOARD_EMAIL", None)],
                    headers = {'Reply-To': request.POST.get('email', '') }
                )
                email.send()

                messages.info(request, "Thanks - we'll get that space added to the map ")
                return redirect(reverse('new_space'))
    except Exception as e:
        messages.error(request, "Error dealing with submission, please try again", extra_tags='alert-danger')
        logger.error("Error in new_space - exception: "+str(e))

    return render(request, 'main/new_space.html', {
        'form': form_class,
        'MAPBOX_ACCESS_TOKEN': getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
    })


class SignupView(CreateView):
    form_class = CustomUserCreationForm
    model = User
    template_name = 'signup/signup.html'

    # make request object available to form
    def get_form_kwargs(self):
        kw = super(SignupView, self).get_form_kwargs()
        kw['request'] = self.request
        return kw

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.set_password(User.objects.make_random_password())
        obj.save()

        try:
            # PasswordResetForm only requires the "email" field, so will validate.
            reset_form = PasswordResetForm(self.request.POST)
            reset_form.is_valid()  # Must trigger validation
            # Copied from django/contrib/auth/views.py : password_reset
            opts = {
                'use_https': self.request.is_secure(),
                'email_template_name': 'user_space_verification/verification.html',
                'subject_template_name': 'user_space_verification/verification_subject.txt',
                'request': self.request,
            }
            # This form sends the email on save()
            reset_form.save(**opts)

            return redirect(reverse_lazy('signup-done'))
        except Exception as e:
            # boo - most likely error is ConnectionRefused, but could be others
            # best to delete partially formed user object so we don't leave useless entries in the database
            obj.delete()
            messages.error(self.request, "Error emailing verification link: " + str(e), extra_tags='alert-danger')
            logger.error("Error in SignupView - unable to send password reset email: "+str(e))

            return redirect(reverse_lazy('signup'))


def space_approval(request, key, action):

    if action != 'approve' and action != 'reject':
        # this shouldn't happen - just redirect to home
        return redirect(reverse_lazy('index'))

    try:
        # lookup user info based on key
        user = User.objects.get(space_request_key=key)

        # update user object
        user.space_status = 'Approved' if action=='approve' else 'Rejected'

        user.save()

        # make a context object for the template to render
        context = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'hackspace': user.space.name,
            'action': ('approving' if action=='approve' else 'rejecting')
        }
        return render(request, 'user_space_verification/space_approval.html', context)

    except User.DoesNotExist as e:
        # aargh - that's not right - redirect to home
        return redirect(reverse_lazy('index'))


def resources(request, path):
    settings = {
        'repo': 'resources',
        'title': 'Resources',
        'subtitle': 'Curated resources to aid starting and running a Hackspace'
    }
    return github_browser(request, settings, path)


def foundation(request, path):
    settings = {
        'repo': 'foundation',
        'title': 'About the Foundation',
        'subtitle': 'Goals, structure and operation of the Hackspace Foundation'
    }
    return github_browser(request, settings, path)


def github_browser(request, settings, path):
    origpath = path

    slugs = path.split('/')
    repo = settings['repo']

    # need to redirect folder requests to a README.md file
    if '.' not in slugs[-1]:
        if path != '' and not path.endswith('/'):
            path += '/'
        path += 'README.md'
        return redirect('/%s/%s' % (repo, path))

    rawurl = urljoin('https://raw.githubusercontent.com/UKHackspaceFoundation/%s/master/' % repo, path)
    url = urljoin('https://github.com/UKHackspaceFoundation/%s/blob/master/' % repo, path)

    # if this isn't a markdown file?
    if not path.endswith('.md'):
        # redirect to raw url  (e.g. for .pdf, etc)
        return redirect(rawurl)

    r = requests.get(rawurl)

    # build breadcrumbs
    breadcrumbs = []
    slugurl = ''
    for slug in slugs:
        if slug != '':
            slugurl = '%s/%s' % (slugurl, slug)
            breadcrumb = {'slug': slug, 'url': slugurl}
            breadcrumbs.append(breadcrumb)

    # TODO: deal with not found
    context = {
        'repo': settings['repo'],
        'origpath': origpath,
        'breadcrumbs': breadcrumbs,
        'path': path.split('/'),
        'rawurl': rawurl,
        'url': url,
        'imageBase': rawurl.rsplit('/', 1)[0] + '/',
        'md': markdown.markdown(r.text, safe_mode='escape'),
        'title': settings['title'],
        'subtitle': settings['subtitle']
    }
    return render(request, 'main/github_browser.html', context)
