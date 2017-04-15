from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from .models import Space
import requests
import markdown
from urllib.parse import urljoin
from main.models import User
from dealer.git import git
from django.conf import settings
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy


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
    fields = ['email', 'first_name', 'last_name', 'space']
    success_url = '/home'

    def get_object(self, queryset=None):
        return self.request.user

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


@login_required
def space_detail(request):
    return render(request, 'main/space_detail.html', {'spaces': Space.objects.all()})


def valueOrBlank(obj, attr, d):
    if attr in obj:
        return obj[attr]
    else:
        return d


@login_required
def import_spaces(request):
    json_data = open('main/static/data.json')
    data = json.load(json_data)

    for s in data:

        # see if record already exists
        q = Space.objects.filter(name=s['name'])
        if len(q) == 0:
            srecord = Space(
                name=valueOrBlank(s, 'name', ''),
                longname=valueOrBlank(s, 'longname', ''),
                town=valueOrBlank(s, 'town', ''),
                country=valueOrBlank(s, 'country', ''),
                region=valueOrBlank(s, 'region', ''),
                have_premises=valueOrBlank(s, 'havePremises', 'No') == 'Yes',
                town_not_in_name=valueOrBlank(s, 'townNotInName', 'No') == 'Yes',
                address_first_line=valueOrBlank(s, 'addressFirstLine', ''),
                postcode=valueOrBlank(s, 'postcode', ''),
                lat=valueOrBlank(s, 'lat', 0.0),
                lng=valueOrBlank(s, 'lng', 0.0),
                main_website_url=valueOrBlank(s, 'mainWebsiteUrl', ''),
                logo_image_url=valueOrBlank(s, 'logoImageUrl', ''),
                status=valueOrBlank(s, 'status', ''),
                classification=valueOrBlank(s, 'classification', '')
            )
            srecord.save()
        # else
            # existing record, do nothing for now
    return redirect('/space_detail')


def starting(request):
    return render(request, 'main/starting.html')


def join(request):
    return render(request, 'main/join.html')


def join_supporter(request):
    return render(request, 'main/supporter.html')


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


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email','first_name','last_name','space',)


class SignupView(CreateView):
    form_class = CustomUserCreationForm
    model = User
    template_name = 'main/signup.html'
    success_url = "/home"

    def form_valid(self, form):
        res = super().form_valid(form)
        user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password1'])
        if user is not None:
            if user.is_active:
                login(self.request, user)
        return res


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
