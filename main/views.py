from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.edit import CreateView
from .models import Space
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import PasswordResetForm
import requests
import markdown
from urllib.parse import urljoin
from main.models import User
from dealer.git import git
from django.conf import settings
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy, reverse
import gocardless_pro


def index(request):
    activeSpaces = Space.objects.filter(status="Active") | Space.objects.filter(status="Starting")
    inactiveSpaces = Space.objects.filter(status="Defunct") | Space.objects.filter(status="Suspended")
    return render(request, 'main/index.html', {
        'activeSpaces': activeSpaces,
        'inactiveSpaces': inactiveSpaces,
        'MAPBOX_ACCESS_TOKEN': getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
    })


# homepage for registered users
@login_required
def home(request):
    associated_users = User.objects.filter(space=request.user.space)
    return render(request, 'main/home.html', {
        'MAPBOX_ACCESS_TOKEN': getattr(settings, "MAPBOX_ACCESS_TOKEN", None),
        'associated_users': associated_users
    })


class UserUpdate(UpdateView):
    model = User
    success_url = '/home'
    form_class = CustomUserCreationForm

    def get_object(self, queryset=None):
        return self.request.user


class SpaceUpdate(UpdateView):
    model = Space
    fields = ['name', 'status', 'main_website_url', 'email','have_premises', 'address_first_line', 'town', 'region', 'postcode', 'country', 'lat', 'lng', 'logo_image_url']
    success_url = '/home'

    def get_object(self, queryset=None):
        return self.request.user.space

    def get_context_data(self, **kwargs):
        context = super(SpaceUpdate, self).get_context_data(**kwargs)
        context['MAPBOX_ACCESS_TOKEN'] = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
        return context


# return space info as json - used for rendering map on homepage
def spaces(request):
    results = Space.objects.all().values('name', 'lat', 'lng', 'main_website_url', 'logo_image_url', 'status')
    return JsonResponse({'spaces': list(results)})


@login_required
def gitinfo(request):
    context = {
        'tag': git.tag
    }
    return render(request, 'main/gitinfo.html', context)


# return space info as geojson
def geojson(request):
    results = Space.objects.all().values('name', 'lat', 'lng', 'main_website_url', 'logo_image_url', 'status')
    geo = {
        "type": "FeatureCollection",
        "features": []
    }
    for space in results:
        if (space['lng'] != 0 and space['lat'] != 0):
            geo['features'].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(space['lng']), float(space['lat'])]
                },
                "properties": {
                    "name": space['name'],
                    "url": space['main_website_url'],
                    "status": space['status'],
                    "logo": space['logo_image_url']
                }
            })
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
    return redirect('/space_detail')



def starting(request):
    return render(request, 'main/starting.html')


@login_required
def join(request):
    return render(request, 'main/join.html')


@login_required
def join_supporter_step1(request):
    return render(request, 'main/supporter_step1.html')


@login_required
def join_supporter_step2(request):
    # get gocardless client object
    client = gocardless_pro.Client(
        access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
        environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
    )

    # create a redirect_flow, pre-fill the users name and email
    redirect_flow = client.redirect_flows.create(
        params={
            "description" : "Hackspace Foundation Individual Membership",
            "session_token" : request.user.gocardless_session_token,
            "success_redirect_url" : request.build_absolute_uri(reverse('join_supporter_step3', kwargs={'session_token':request.user.gocardless_session_token} )),
            "prefilled_customer": {
                "given_name": request.user.first_name,
                "family_name": request.user.last_name,
                "email": request.user.email
            }
        }
    )

    # store the redirect id
    request.user.gocardless_redirect_flow_id = redirect_flow.id
    request.user.save()

    print(redirect_flow.redirect_url)

    return redirect(redirect_flow.redirect_url)

@login_required
def join_supporter_step3(request, session_token):

    print(session_token)

    return render(request, 'base.html')


class Login(View):
    def get(self, request):
        return render(request, 'main/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/home')
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'main/login.html')


def logout_view(request):
    logout(request)
    return redirect('/')


class SignupView(CreateView):
    form_class = CustomUserCreationForm
    model = User
    template_name = 'main/signup.html'

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
                'email_template_name': 'main/verification.html',
                'subject_template_name': 'main/verification_subject.txt',
                'request': self.request,
            }
            # This form sends the email on save()
            reset_form.save(**opts)

            return redirect('signup-done')
        except Exception as e:
            # boo - most likely error is ConnectionRefused, but could be others
            # best to delete partially formed user object so we don't leave useless entries in the database
            obj.delete()
            messages.error(self.request, "Error emailing verification link: " + str(e), extra_tags='alert-danger')

            return redirect('signup')


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
