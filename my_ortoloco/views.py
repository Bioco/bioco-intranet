# -*- coding: utf-8 -*-

from datetime import date
from StringIO import StringIO
import string
import random
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.core.management import call_command

from my_ortoloco.models import *
from my_ortoloco.forms import *
from my_ortoloco.helpers import *
from my_ortoloco.filters import Filter
from my_ortoloco.mailer import *

import hashlib
from static_ortoloco.models import Politoloco

from decorators import primary_loco_of_abo


def password_generator(size=8, chars=string.ascii_uppercase + string.digits): return ''.join(random.choice(chars) for x in range(size))


def getBohnenDict(request):
    loco = request.user.loco
    next_jobs = set()
    if loco.abo is not None:
        allebohnen = Boehnli.objects.filter(loco=loco)
        userbohnen = []

        for bohne in allebohnen:
            if bohne.job.time.year == date.today().year and bohne.job.time < datetime.datetime.now():
                userbohnen.append(bohne)
        bohnenrange = range(0, max(userbohnen.__len__(), loco.abo.groesse * 10 / loco.abo.locos.count()))

        for bohne in Boehnli.objects.all().filter(loco=loco).order_by("job__time"):
            if bohne.job.time > datetime.datetime.now():
                next_jobs.add(bohne.job)
    else:
        bohnenrange = None
        userbohnen = []
        next_jobs = set()

    return {
        'user': request.user,
        'bohnenrange': bohnenrange,
        'userbohnen': len(userbohnen),
        'next_jobs': next_jobs,
        'staff_user': request.user.is_staff,
        'politoloco': request.user.has_perm('static_ortoloco.can_send_newsletter')
    }


@login_required
def my_home(request):
    """
    Overview on myortoloco
    """

    jobs = get_current_jobs()
    renderdict = getBohnenDict(request)
    renderdict.update({
        'jobs': jobs[:7],
        'teams': Taetigkeitsbereich.objects.filter(hidden=False),
        'no_abo': request.user.loco.abo is None
    })

    return render(request, "myhome.html", renderdict)


@login_required
def my_job(request, job_id):
    """
    Details for a job
    """
    loco = request.user.loco
    job = get_object_or_404(Job, id=int(job_id))

    def check_int(s):
        if s[0] in ('-', '+'):
            return s[1:].isdigit()
        return s.isdigit()

    error = None
    if request.method == 'POST':
        num = request.POST.get("jobs")
        my_bohnen = job.boehnli_set.all().filter(loco=loco)
        if check_int(num) and 0 < int(num) <= job.freie_plaetze():
            # adding participants
            add = int(num)
            for i in range(add):
                bohne = Boehnli.objects.create(loco=loco, job=job)
        else:
            error = "Ungueltige Anzahl Einschreibungen"

    participants = []
    for bohne in Boehnli.objects.filter(job_id=job.id):
        if bohne.loco is not None:
            participants.append(bohne.loco)

    renderdict = getBohnenDict(request)
    renderdict.update({
        'participants': participants,
        'job': job,
        'slotrange': range(0, job.slots),
        'error': error
    });
    return render(request, "job.html", renderdict)


@login_required
def my_depot(request, depot_id):
    """
    Details for a Depot
    """
    depot = get_object_or_404(Depot, id=int(depot_id))

    renderdict = getBohnenDict(request)
    renderdict.update({
        'depot': depot
    });
    return render(request, "depot.html", renderdict)


@login_required
def my_participation(request):
    """
    Details for all areas a loco can participate
    """
    loco = request.user.loco
    my_areas = []
    success = False
    if request.method == 'POST':
        old_areas = set(loco.areas.all())
        new_areas = set(area for area in Taetigkeitsbereich.objects.filter(hidden=False)
                        if request.POST.get("area" + str(area.id)))
        if old_areas != new_areas:
            loco.areas = new_areas
            loco.save()
            for area in new_areas - old_areas:
                send_new_loco_in_taetigkeitsbereich_to_bg(area, loco)

        success = True

    for area in Taetigkeitsbereich.objects.filter(hidden=False):
        if area.hidden:
            continue
        my_areas.append({
            'name': area.name,
            'checked': loco in area.locos.all(),
            'id': area.id,
            'core': area.core,
            'coordinator': area.coordinator
        })

    renderdict = getBohnenDict(request)
    renderdict.update({
        'areas': my_areas,
        'success': success
    })
    return render(request, "participation.html", renderdict)


@login_required
def my_pastjobs(request):
    """
    All past jobs of current user
    """
    loco = request.user.loco

    allebohnen = Boehnli.objects.filter(loco=loco)
    past_bohnen = []

    for bohne in allebohnen:
        if bohne.job.time < datetime.datetime.now():
            past_bohnen.append(bohne)

    renderdict = getBohnenDict(request)
    renderdict.update({
        'bohnen': past_bohnen
    })
    return render(request, "my_pastjobs.html", renderdict)


@permission_required('static_ortoloco.can_send_newsletter')
def send_politoloco(request):
    """
    Send politoloco newsletter
    """
    sent = 0
    if request.method == 'POST':
        emails = set()
        if request.POST.get("allpolitoloco"):
            for loco in Politoloco.objects.all():
                emails.add(loco.email)

        if request.POST.get("allortolocos"):
            for loco in Loco.objects.all():
                emails.add(loco.email)

        if request.POST.get("allsingleemail"):
            emails.add(request.POST.get("singleemail"))

        send_politoloco_mail(request.POST.get("subject"), request.POST.get("message"), request.POST.get("textMessage"), emails, request.META["HTTP_HOST"])
        sent = len(emails)
    renderdict = getBohnenDict(request)
    renderdict.update({
        'politolocos': Politoloco.objects.count(),
        'ortolocos': Loco.objects.count(),
        'sent': sent
    })
    return render(request, 'mail_sender_politoloco.html', renderdict)


@login_required
def my_abo(request):
    """
    Details for an abo of a loco
    """
    renderdict = getBohnenDict(request)
    if request.user.loco.abo:
        renderdict.update({
            'zusatzabos': request.user.loco.abo.extra_abos.all(),
            'mitabonnenten': request.user.loco.abo.bezieher_locos().exclude(email=request.user.loco.abo.primary_loco.email),
            'primary': request.user.loco.abo.primary_loco.email == request.user.loco.email
        })
    renderdict.update({
        'loco': request.user.loco,
        'scheine': request.user.loco.anteilschein_set.count(),
        'scheine_unpaid': request.user.loco.anteilschein_set.filter(paid=False).count(),
    })
    return render(request, "my_abo.html", renderdict)


@primary_loco_of_abo
def my_abo_change(request, abo_id):
    """
    Ein Abo ändern
    """
    month = int(time.strftime("%m"))
    if month >= 7:
        next_extra = datetime.date(day=1, month=1, year=datetime.date.today().year + 1)
    else:
        next_extra = datetime.date(day=1, month=7, year=datetime.date.today().year)
    renderdict = getBohnenDict(request)
    renderdict.update({
        'loco': request.user.loco,
        'change_size': month <= 10,
        'change_extra': month != 6 and month != 12,
        'next_extra_abo_date': next_extra,
        'next_size_date': datetime.date(day=1, month=1, year=datetime.date.today().year + 1)
    })
    return render(request, "my_abo_change.html", renderdict)


@primary_loco_of_abo
def my_depot_change(request, abo_id):
    """
    Ein Abo-Depot ändern
    """
    saved = False
    if request.method == "POST":
        request.user.loco.abo.depot = get_object_or_404(Depot, id=int(request.POST.get("depot")))
        request.user.loco.abo.save()
        saved = True
    renderdict = getBohnenDict(request)
    renderdict.update({
        'saved': saved,
        'loco': request.user.loco,
        "depots": Depot.objects.all()
    })
    return render(request, "my_depot_change.html", renderdict)

@primary_loco_of_abo
def my_size_change(request, abo_id):
    """
    Eine Abo-Grösse ändern
    """
    saved = False
    if request.method == "POST":
        request.user.loco.abo.groesse = int(request.POST.get("abo"))
        request.user.loco.abo.save()
        saved = True
    renderdict = getBohnenDict(request)
    renderdict.update({
        'saved': saved,
        'groesse': request.user.loco.abo.groesse
    })
    return render(request, "my_size_change.html", renderdict)


@primary_loco_of_abo
def my_extra_change(request, abo_id):
    """
    Ein Extra-Abos ändern
    """
    saved = False
    if request.method == "POST":
        for extra_abo in ExtraAboType.objects.all():
            if request.POST.get("abo" + str(extra_abo.id)) == str(extra_abo.id):
                request.user.loco.abo.extra_abos.add(extra_abo)
                extra_abo.abo_set.add(request.user.loco.abo)
            else:
                request.user.loco.abo.extra_abos.remove(extra_abo)
                extra_abo.abo_set.remove(request.user.loco.abo)

            request.user.loco.abo.save()
            extra_abo.save()

        saved = True

    abos = []
    for abo in ExtraAboType.objects.all():
        if abo in request.user.loco.abo.extra_abos.all():
            abos.append({
                'id': abo.id,
                'name': abo.name,
                'selected': True
            })
        else:
            abos.append({
                'id': abo.id,
                'name': abo.name
            })
    renderdict = getBohnenDict(request)
    renderdict.update({
        'saved': saved,
        'loco': request.user.loco,
        "extras": abos
    })
    return render(request, "my_extra_change.html", renderdict)


@login_required
def my_team(request, bereich_id):
    """
    Details for a team
    """

    job_types = JobTyp.objects.all().filter(bereich=bereich_id)

    jobs = get_current_jobs().filter(typ=job_types)

    renderdict = getBohnenDict(request)
    renderdict.update({
        'team': get_object_or_404(Taetigkeitsbereich, id=int(bereich_id)),
        'jobs': jobs,
    })
    return render(request, "team.html", renderdict)


@login_required
def my_einsaetze(request):
    """
    All jobs to be sorted etc.
    """
    renderdict = getBohnenDict(request)

    jobs = get_current_jobs();
    renderdict.update({
        'jobs': jobs,
        'show_all': True
    })

    return render(request, "jobs.html", renderdict)


@login_required
def my_einsaetze_all(request):
    """
    All jobs to be sorted etc.
    """
    renderdict = getBohnenDict(request)
    jobs = Job.objects.all().order_by("time")
    renderdict.update({
        'jobs': jobs,
    })

    return render(request, "jobs.html", renderdict)


def my_signup(request):
    """
    Become a member of ortoloco
    """
    success = False
    agberror = False
    agbchecked = False
    userexists = False
    if request.method == 'POST':
        agbchecked = request.POST.get("agb") == "on"

        locoform = ProfileLocoForm(request.POST)
        if not agbchecked:
            agberror = True
        else:
            if locoform.is_valid():
                #check if user already exists
                if User.objects.filter(email=locoform.cleaned_data['email']).__len__() > 0:
                    userexists = True
                else:
                    #set all fields of user
                    #email is also username... we do not use it
                    password = password_generator()

                    loco = Loco.objects.create(first_name=locoform.cleaned_data['first_name'], last_name=locoform.cleaned_data['last_name'], email=locoform.cleaned_data['email'])
                    loco.addr_street = locoform.cleaned_data['addr_street']
                    loco.addr_zipcode = locoform.cleaned_data['addr_zipcode']
                    loco.addr_location = locoform.cleaned_data['addr_location']
                    loco.phone = locoform.cleaned_data['phone']
                    loco.mobile_phone = locoform.cleaned_data['mobile_phone']
                    loco.save()

                    loco.user.set_password(password)
                    loco.user.save()

                    #log in to allow him to make changes to the abo
                    loggedin_user = authenticate(username=loco.user.username, password=password)
                    login(request, loggedin_user)
                    success = True
                    return redirect("/my/aboerstellen")
    else:
        locoform = ProfileLocoForm()

    renderdict = {
        'locoform': locoform,
        'success': success,
        'agberror': agberror,
        'agbchecked': agbchecked,
        'userexists': userexists
    }
    return render(request, "signup.html", renderdict)


@login_required
def my_add_loco(request, abo_id):
    scheineerror = False
    scheine = 1
    userexists = False
    if request.method == 'POST':
        locoform = ProfileLocoForm(request.POST)
        if User.objects.filter(email=request.POST.get('email')).__len__() > 0:
            userexists = True
        try:
            scheine = int(request.POST.get("anteilscheine"))
            scheineerror = scheine < 0
        except TypeError:
            scheineerror = True
        except  ValueError:
            scheineerror = True
        if locoform.is_valid() and scheineerror is False and userexists is False:
            username = make_username(locoform.cleaned_data['first_name'],
                                     locoform.cleaned_data['last_name'],
                                     locoform.cleaned_data['email'])
            pw = password_generator()
            loco = Loco.objects.create(first_name=locoform.cleaned_data['first_name'], last_name=locoform.cleaned_data['last_name'], email=locoform.cleaned_data['email'])
            loco.first_name = locoform.cleaned_data['first_name']
            loco.last_name = locoform.cleaned_data['last_name']
            loco.email = locoform.cleaned_data['email']
            loco.addr_street = locoform.cleaned_data['addr_street']
            loco.addr_zipcode = locoform.cleaned_data['addr_zipcode']
            loco.addr_location = locoform.cleaned_data['addr_location']
            loco.phone = locoform.cleaned_data['phone']
            loco.mobile_phone = locoform.cleaned_data['mobile_phone']
            loco.confirmed = False
            loco.abo_id = abo_id
            loco.save()

            loco.user.set_password(pw)
            loco.user.save()

            for num in range(0, scheine):
                anteilschein = Anteilschein(loco=loco, paid=False)
                anteilschein.save()

            send_been_added_to_abo(loco.email, pw, loco.get_name(), scheine, hashlib.sha1(locoform.cleaned_data['email'] + str(abo_id)).hexdigest(), request.META["HTTP_HOST"])

            loco.save()
            if request.GET.get("return"):
                return redirect(request.GET.get("return"))
            return redirect('/my/aboerstellen')

    else:
        loco = request.user.loco
        initial = {"addr_street": loco.addr_street,
                   "addr_zipcode": loco.addr_zipcode,
                   "addr_location": loco.addr_location,
                   "phone": loco.phone,
        }
        locoform = ProfileLocoForm(initial=initial)
    renderdict = {
        'scheine': scheine,
        'userexists': userexists,
        'scheineerror': scheineerror,
        'locoform': locoform,
        "loco": request.user.loco,
        "depots": Depot.objects.all()
    }
    return render(request, "add_loco.html", renderdict)


@login_required
def my_createabo(request):
    """
    Abo erstellen
    """
    loco = request.user.loco
    scheineerror = False
    if loco.abo is None or loco.abo.groesse is 1:
        selectedabo = "small"
    elif loco.abo.groesse is 2:
        selectedabo = "big"
    else:
        selectedabo = "house"

    loco_scheine = 0
    if loco.abo is not None:
        for abo_loco in loco.abo.bezieher_locos().exclude(email=request.user.loco.email):
            loco_scheine += abo_loco.anteilschein_set.all().__len__()

    if request.method == "POST":
        scheine = int(request.POST.get("scheine"))
        selectedabo = request.POST.get("abo")

        scheine += loco_scheine
        if (scheine < 4 and request.POST.get("abo") == "big") or (scheine < 20 and request.POST.get("abo") == "house") or (scheine < 2 and request.POST.get("abo") == "small" ) or (scheine == 0):
            scheineerror = True
        else:
            depot = Depot.objects.all().filter(id=request.POST.get("depot"))[0]
            groesse = 1
            if request.POST.get("abo") == "house":
                groesse = 10
            elif request.POST.get("abo") == "big":
                groesse = 2
            else:
                groesse = 1
            if loco.abo is None:
                loco.abo = Abo.objects.create(groesse=groesse, primary_loco=loco, depot=depot)
            else:
                loco.abo.groesse = groesse
                loco.abo.depot = depot
            loco.abo.save()
            loco.save()

            if loco.anteilschein_set.count() < int(request.POST.get("scheine")):
                toadd = int(request.POST.get("scheine")) - loco.anteilschein_set.count()
                for num in range(0, toadd):
                    anteilschein = Anteilschein(loco=loco, paid=False)
                    anteilschein.save()

            if request.POST.get("add_loco"):
                return redirect("/my/abonnent/" + str(loco.abo_id))
            else:
                password = password_generator()

                request.user.set_password(password)
                request.user.save()

                #user did it all => send confirmation mail
                send_welcome_mail(loco.email, password, request.META["HTTP_HOST"])
                send_welcome_mail("lea@ortoloco.ch", "<geheim>", request.META["HTTP_HOST"])

                return redirect("/my/willkommen")

    selected_depot = None
    mit_locos = []
    if request.user.loco.abo is not None:
        selected_depot = request.user.loco.abo.depot
        mit_locos = request.user.loco.abo.bezieher_locos().exclude(email=request.user.loco.email)

    renderdict = {
        'loco_scheine': loco_scheine,
        "loco": request.user.loco,
        "depots": Depot.objects.all(),
        'selected_depot': selected_depot,
        "selected_abo": selectedabo,
        "scheineerror": scheineerror,
        "mit_locos": mit_locos
    }
    return render(request, "createabo.html", renderdict)


@login_required
def my_welcome(request):
    """
    Willkommen
    """

    renderdict = getBohnenDict(request)
    renderdict.update({
        'jobs': get_current_jobs()[:7],
        'teams': Taetigkeitsbereich.objects.filter(hidden=False),
        'no_abo': request.user.loco.abo is None
    })

    return render(request, "welcome.html", renderdict)


def my_confirm(request, hash):
    """
    Confirm from a user that has been added as a Mitabonnent
    """

    for loco in Loco.objects.all():
        if hash == hashlib.sha1(loco.email + str(loco.abo_id)).hexdigest():
            loco.confirmed = True
            loco.save()

    return redirect("/my/home")


@login_required
def my_contact(request):
    """
    Kontaktformular
    """
    loco = request.user.loco

    if request.method == "POST":
        # send mail to bg
        send_contact_form(request.POST.get("subject"), request.POST.get("message"), loco, request.POST.get("copy"))

    renderdict = getBohnenDict(request)
    renderdict.update({
        'usernameAndEmail': loco.first_name + " " + loco.last_name + "<" + loco.email + ">"
    })
    return render(request, "my_contact.html", renderdict)


@login_required
def my_profile(request):
    success = False
    loco = request.user.loco
    if request.method == 'POST':
        locoform = ProfileLocoForm(request.POST, instance=loco)
        if locoform.is_valid():
            #set all fields of user
            loco.first_name = locoform.cleaned_data['first_name']
            loco.last_name = locoform.cleaned_data['last_name']
            loco.email = locoform.cleaned_data['email']
            loco.addr_street = locoform.cleaned_data['addr_street']
            loco.addr_zipcode = locoform.cleaned_data['addr_zipcode']
            loco.addr_location = locoform.cleaned_data['addr_location']
            loco.phone = locoform.cleaned_data['phone']
            loco.mobile_phone = locoform.cleaned_data['mobile_phone']
            loco.save()

            success = True
    else:
        locoform = ProfileLocoForm(instance=loco)

    renderdict = getBohnenDict(request)
    renderdict.update({
        'locoform': locoform,
        'success': success
    })
    return render(request, "profile.html", renderdict)


@login_required
def my_change_password(request):
    success = False
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['password'])
            request.user.save()
            success = True
    else:
        form = PasswordForm()

    renderdict = getBohnenDict(request)
    renderdict.update({
        'form': form,
        'success': success
    })
    return render(request, 'password.html', renderdict)


def my_new_password(request):
    sent = False
    if request.method == 'POST':
        sent = True
        locos = Loco.objects.filter(email=request.POST.get('username'))
        if len(locos) > 0:
            loco = locos[0]
            pw = password_generator()
            loco.user.set_password(pw)
            loco.user.save()
            send_mail_password_reset(loco.email, pw, request.META["HTTP_HOST"])

    renderdict = {
        'sent': sent
    }
    return render(request, 'my_newpassword.html', renderdict)


@staff_member_required
def my_mails(request):
    sent = 0
    if request.method == 'POST':
        emails = set()
        if request.POST.get("allabo") == "on":
            for loco in Loco.objects.exclude(abo=None):
                emails.add(loco.email)
        if request.POST.get("allanteilsschein") == "on":
            for loco in Loco.objects.all():
                if loco.anteilschein_set.count() > 0:
                    emails.add(loco.email)
        if request.POST.get("all") == "on":
            for loco in Loco.objects.all():
                emails.add(loco.email)
        if len(emails) > 0:
            send_filtered_mail(request.POST.get("subject"), request.POST.get("message"), request.POST.get("textMessage"), emails, request.META["HTTP_HOST"])
            sent = len(emails)
    renderdict = getBohnenDict(request)
    renderdict.update({
        'sent': sent
    })
    return render(request, 'mail_sender.html', renderdict)


@staff_member_required
def my_filters(request):
    renderdict = getBohnenDict(request)
    renderdict.update({
        'locos': Loco.objects.all()
    })
    return render(request, 'filters.html', renderdict)


@staff_member_required
def my_depotlisten(request):
    return alldepots_list(request, "")


def logout_view(request):
    auth.logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect("/aktuelles")


def alldepots_list(request, name):
    """
    Printable list of all depots to check on get gemüse
    """
    if name == "":
        depots = Depot.objects.all().order_by("code")
    else:
        depots = [get_object_or_404(Depot, code__iexact=name)]

    overview = {
        'Dienstag': {
            'small_abo': 0,
            'big_abo': 0,
            'entities': 0,
            'egg4': 0,
            'egg6': 0,
            'cheesefull': 0,
            'cheesehalf': 0,
            'cheesequarter': 0,
            'bigobst': 0,
            'smallobst': 0
        },
        'Donnerstag': {
            'small_abo': 0,
            'big_abo': 0,
            'entities': 0,
            'egg4': 0,
            'egg6': 0,
            'cheesefull': 0,
            'cheesehalf': 0,
            'cheesequarter': 0,
            'bigobst': 0,
            'smallobst': 0
        },
        'all': {
            'small_abo': 0,
            'big_abo': 0,
            'entities': 0,
            'egg4': 0,
            'egg6': 0,
            'cheesefull': 0,
            'cheesehalf': 0,
            'cheesequarter': 0,
            'bigobst': 0,
            'smallobst': 0
        }
    }

    for depot in depots:
        row = overview.get(depot.get_weekday_display())
        all = overview.get('all')
        row['small_abo'] += depot.small_abos()
        row['big_abo'] += depot.big_abos()
        row['entities'] += 2 * depot.big_abos() + depot.small_abos()
        #row['egg4'] += depot.vier_eier()
        #row['egg6'] += depot.sechs_eier()
        #row['cheesefull'] += depot.kaese_ganz()
        #row['cheesehalf'] += depot.kaese_halb()
        #row['cheesequarter'] += depot.kaese_viertel()
        #row['bigobst'] += depot.big_obst()
        #row['smallobst'] += depot.small_obst()
        #all['small_abo'] += depot.small_abos()
        #all['big_abo'] += depot.big_abos()
        #all['entities'] += 2 * depot.big_abos() + depot.small_abos()
        #all['egg4'] += depot.vier_eier()
        #all['egg6'] += depot.sechs_eier()
        #all['cheesefull'] += depot.kaese_ganz()
        #all['cheesehalf'] += depot.kaese_halb()
        #all['cheesequarter'] += depot.kaese_viertel()
        #all['bigobst'] += depot.big_obst()
        #all['smallobst'] += depot.small_obst()

    renderdict = {
        "overview": overview,
        "depots": depots,
        "datum": datetime.datetime.now()
    }

    return render_to_pdf(request, "exports/all_depots.html", renderdict, 'Depotlisten')


def my_createlocoforsuperuserifnotexist(request):
    """
    just a helper to create a loco for superuser
    """
    if request.user.is_superuser and len(Loco.objects.filter(email=request.user.email)) is 0:
        loco = Loco.objects.create(user=request.user, first_name="super", last_name="duper", email=request.user.email, addr_street="superstreet", addr_zipcode="8000",
                                   addr_location="SuperCity", phone="012345678")
        loco.save()
        request.user.loco = loco
        request.user.save()


    # we do just nothing if its not a superuser or he has already a loco
    return redirect("/my/home")


@staff_member_required
def my_startmigration(request):
    f = StringIO()
    with Swapstd(f):
        call_command('clean_db')
        call_command('import_old_db', request.GET.get("username"), request.GET.get("password"))
    return HttpResponse(f.getvalue(), content_type="text/plain")


@staff_member_required
def migrate_apps(request):
    f = StringIO()
    with Swapstd(f):
        call_command('migrate', 'my_ortoloco')
        call_command('migrate', 'static_ortoloco')
    return HttpResponse(f.getvalue(), content_type="text/plain")


@staff_member_required
def pip_install(request):
    command = "pip install -r requirements.txt"
    res = run_in_shell(request, command)
    return res


def test_filters(request):
    lst = Filter.get_all()
    res = []
    for name in Filter.get_names():
        res.append("<br><br>%s:" % name)
        tmp = Filter.execute([name], "OR")
        data = Filter.format_data(tmp, unicode)
        res.extend(data)
    return HttpResponse("<br>".join(res))


def test_filters_post(request):
    # TODO: extract filter params from post request
    # the full list of filters is obtained by Filter.get_names()
    filters = ["Zusatzabo Eier", "Depot GZ Oerlikon"]
    op = "AND"
    res = ["Eier AND Oerlikon:<br>"]
    locos = Filter.execute(filters, op)
    data = Filter.format_data(locos, lambda loco: "%s! (email: %s)" % (loco, loco.email))
    res.extend(data)
    return HttpResponse("<br>".join(res))




