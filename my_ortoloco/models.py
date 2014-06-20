# encoding: utf-8

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.db.models import signals
from django.core import validators
from django.core.exceptions import ValidationError
import time
from django.db.models import Q
from datetime import date 

import model_audit
import helpers

from tinymce import models as tinymce_models

class Depot(models.Model):
    """
    Location where stuff is picked up.
    """
    code = models.CharField("Code", max_length=100, validators=[validators.validate_slug], unique=True)
    name = models.CharField("Depot Name", max_length=100, unique=True)
    contact = models.ForeignKey("Loco", on_delete=models.PROTECT)
    weekday = models.PositiveIntegerField("Wochentag", choices=helpers.weekday_choices)
    latitude = models.CharField("Latitude", max_length=100, default="")
    longitude = models.CharField("Longitude", max_length=100, default="")

    addr_street = models.CharField("Strasse", max_length=100)
    addr_zipcode = models.CharField("PLZ", max_length=10)
    addr_location = models.CharField("Ort", max_length=50)

    def __unicode__(self):
        return u"%s %s" % (self.id, self.name)


    def active_abos(self):
        return self.abo_set.filter(active=True)

    def wochentag(self):
        day = "Unbekannt"
        if self.weekday < 8 and self.weekday > 0:
            day = helpers.weekdays[self.weekday]
        return day

    def small_abos(self):
        return len(self.active_abos().filter(Q(groesse=1) | Q(groesse=3)))

    def big_abos(self):
        return len(self.active_abos().filter(Q(groesse=2) | Q(groesse=3) | Q(groesse=4))) + len(self.active_abos().filter(groesse=4))

    def vier_eier(self):
        eier = 0
        for abo in self.active_abos().all():
            eier += len(abo.extra_abos.all().filter(description="Eier 4er Pack"))
        return eier

    def sechs_eier(self):
        eier = 0
        for abo in self.active_abos().all():
            eier += len(abo.extra_abos.all().filter(description="Eier 6er Pack"))
        return eier

    def kaese_ganz(self):
        kaese = 0
        for abo in self.active_abos().all():
            kaese += len(abo.extra_abos.all().filter(description="Käse ganz"))
        return kaese

    def kaese_halb(self):
        kaese = 0
        for abo in self.active_abos().all():
            kaese += len(abo.extra_abos.all().filter(description="Käse halb"))
        return kaese

    def kaese_viertel(self):
        kaese = 0
        for abo in self.active_abos().all():
            kaese += len(abo.extra_abos.all().filter(description="Käse viertel"))
        return kaese

    def big_obst(self):
        obst = 0
        for abo in self.active_abos().all():
            obst += len(abo.extra_abos.all().filter(description="Obst gr. (2kg)"))
        return obst

    def small_obst(self):
        obst = 0
        for abo in self.active_abos().all():
            obst += len(abo.extra_abos.all().filter(description="Obst kl. (1kg)"))
        return obst

    class Meta:
        verbose_name = "Depot"
        verbose_name_plural = "Depots"


class ExtraAboType(models.Model):
    """
    Types of extra abos, e.g. eggs, cheese, fruit
    """
    name = models.CharField("Name", max_length=100, unique=True)
    description = models.TextField("Beschreibung", max_length=1000)

    def __unicode__(self):
        return u"%s %s" % (self.id, self.name)

    class Meta:
        verbose_name = "Zusatz-Abo"
        verbose_name_plural = "Zusatz-Abos"


class Abo(models.Model):
    """
    One Abo that may be shared among several people.
    """
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT)
    groesse = models.PositiveIntegerField(default=1)
    extra_abos = models.ManyToManyField(ExtraAboType, null=True, blank=True)
    primary_loco = models.ForeignKey("Loco", related_name="abo_primary", null=True, blank=True,
                                     on_delete=models.PROTECT)
    active = models.BooleanField(default=False)

    def __unicode__(self):
        namelist = ["1 Einheit" if self.groesse == 1 else "%d Einheiten" % self.groesse]
        namelist.extend(extra.name for extra in self.extra_abos.all())
        return u"Abo (%s) %s" % (" + ".join(namelist), self.id)

    def bezieher(self):
        locos = self.locos.all()
        return ", ".join(unicode(loco) for loco in locos)

    def andere_bezieher(self):
        locos = self.bezieher_locos().exclude(email=self.primary_loco.email)
        return ", ".join(unicode(loco) for loco in locos)

    def bezieher_locos(self):
        return self.locos.all()

    def verantwortlicher_bezieher(self):
        loco = self.primary_loco
        return unicode(loco) if loco is not None else ""

    def haus_abos(self):
        return int(self.groesse / 10)

    def grosse_abos(self):
        return int((self.groesse % 10) / 2)

    def groesse_name(self):
        if self.groesse == 1:
            return "Kleines Abo"
        elif self.groesse == 2:
            return "Grosses Abo"
        elif self.groesse == 10:
            return "Haus Abo"
        elif self.groesse == 3:
            return "Kleines + Grosses Abo"
        elif self.groesse == 4:
            return "2 Grosse Abos"
        else:
            return "Spezialgrösse"

    def kleine_abos(self):
        return self.groesse % 2

    def vier_eier(self):
        return len(self.extra_abos.all().filter(description="Eier 4er Pack")) > 0

    def sechs_eier(self):
        return len(self.extra_abos.all().filter(description="Eier 6er Pack")) > 0

    def ganze_kaese(self):
        return len(self.extra_abos.all().filter(description="Käse ganz")) > 0

    def halbe_kaese(self):
        return len(self.extra_abos.all().filter(description="Käse halb")) > 0

    def viertel_kaese(self):
        return len(self.extra_abos.all().filter(description="Käse viertel")) > 0

    def gross_obst(self):
        return len(self.extra_abos.all().filter(description="Obst gr. (2kg)")) > 0

    def klein_obst(self):
        return len(self.extra_abos.all().filter(description="Obst kl. (1kg)")) > 0

    class Meta:
        verbose_name = "Abo"
        verbose_name_plural = "Abos"


class Loco(models.Model):
    """
    Additional fields for Django's default user class.
    """

    # user class is only used for logins, permissions, and other builtin django stuff
    # all user information should be stored in the Loco model
    user = models.OneToOneField(User, related_name='loco', null=True, blank=True)

    first_name = models.CharField("Vorname", max_length=30)
    last_name = models.CharField("Nachname", max_length=30)
    email = models.EmailField(unique=True)

    addr_street = models.CharField("Strasse", max_length=100)
    addr_zipcode = models.CharField("PLZ", max_length=10)
    addr_location = models.CharField("Ort", max_length=50)
    birthday = models.DateField("Geburtsdatum", null=True, blank=True)
    phone = models.CharField("Telefonnr", max_length=50)
    mobile_phone = models.CharField("Mobile", max_length=50, null=True, blank=True)

    abo = models.ForeignKey(Abo, related_name="locos", null=True, blank=True,
                            on_delete=models.SET_NULL)

    confirmed = models.BooleanField("bestätigt", default=True)

    def get_taetigkeitsbereiche(self):
        tbs = []
        for tb in Taetigkeitsbereich.objects.all():
            if tb.locos.all().filter(id=self.id).__len__() > 0:
                tbs.append(tb)
        return tbs

    def __unicode__(self):
        return self.get_name()

    @classmethod
    def create(cls, sender, instance, created, **kdws):
        """
        Callback to create corresponding loco when new user is created.
        """
        if created:
            username = helpers.make_username(instance.first_name, instance.last_name, instance.email)
            user = User(username=username)
            user.save()
            user = User.objects.get(username=username)
            instance.user = user
            instance.save()

    @classmethod
    def post_delete(cls, sender, instance, **kwds):
        instance.user.delete()


    class Meta:
        verbose_name = "Mitglied (Loco)"
        verbose_name_plural = "Mitglieder (Locos)"

    def get_name(self):
        return u"%s %s" % (self.first_name, self.last_name)

    def get_phone(self):
        if self.mobile_phone != "":
            return self.mobile_phone
        return self.phone


class Anteilschein(models.Model):
    loco = models.ForeignKey(Loco, null=True, blank=True, on_delete=models.SET_NULL)
    paid = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)

    def __unicode__(self):
        return u"Anteilschein #%s" % (self.id)

    class Meta:
        verbose_name = "Anteilschein"
        verbose_name_plural = "Anteilscheine"


class Taetigkeitsbereich(models.Model):
    name = models.CharField("Name", max_length=100, unique=True)
    description = models.TextField("Beschreibung", max_length=1000, default="")
    core = models.BooleanField("Kernbereich", default=False)
    hidden = models.BooleanField("versteckt", default=False)
    coordinator = models.ForeignKey(Loco, on_delete=models.PROTECT)
    locos = models.ManyToManyField(Loco, related_name="areas", blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Tätigkeitsbereich'
        verbose_name_plural = 'Tätigkeitsbereiche'


class JobTyp(models.Model):
    """
    Recurring type of job.
    """
    name = models.CharField("Name", max_length=100, unique=True)
    displayed_name = models.CharField("Angezeigter Name", max_length=100, blank=True, null=True)
    description = tinymce_models.HTMLField("Beschreibung", max_length=1000, default="")
    bereich = models.ForeignKey(Taetigkeitsbereich, on_delete=models.PROTECT)
    duration = models.PositiveIntegerField("Dauer in Stunden")
    location = models.CharField("Ort", max_length=100, default="")
    car_needed = models.BooleanField("Auto benötigt", default=False)

    def __unicode__(self):
        return u'%s - %s' % (self.bereich, self.get_name())

    def get_name(self):
        if self.displayed_name is not None:
            return self.displayed_name
        return self.name

    class Meta:
        verbose_name = 'Jobart'
        verbose_name_plural = 'Jobarten'


class Job(models.Model):
    typ = models.ForeignKey(JobTyp, on_delete=models.PROTECT)
    slots = models.PositiveIntegerField("Plaetze")
    time = models.DateTimeField()
    reminder_sent = models.BooleanField("Reminder verschickt", default=False)

    def __unicode__(self):
        return u'Job #%s' % (self.id)

    def wochentag(self):
        weekday = helpers.weekdays[self.time.isoweekday()]
        return weekday[:2]

    def time_stamp(self):
        return int(time.mktime(self.time.timetuple()) * 1000)

    def freie_plaetze(self):
        return self.slots - self.besetzte_plaetze()

    def end_time(self):
        return self.time + datetime.timedelta(hours=self.typ.duration)

    def besetzte_plaetze(self):
        return self.boehnli_set.count()
    
    def needs_car(self):
        return self.typ.car_needed
    
    def status_class(self):
        boehnlis = Boehnli.objects.filter(job_id=self.id)
        participants = boehnlis.count()
        if participants >= self.slots:
            return 'full'
        to_be_filled = self.slots - participants
        time_left = self.time - date.today()
        days_left = time_left.days
        if days_left <= to_be_filled:
            return 'urgent'
        return ''
        
    def get_car_status(self):
        text = self.get_car_status_text()
        needed = self.typ.car_needed
        if needed:
            available = Boehnli.objects.filter(job_id=self.id,with_car=True)
            if available.count():
                return '<img src="/static/img/auto_green.png" width="32" title="%s" />' % text
            else:
                return '<img src="/static/img/auto_red.png" width="32" title="%s" />' % text
        else:
            return '<img src="/static/img/auto_grey.png" width="32" title="%s" />' % text
        
    def get_car_status_text(self):
        needed = self.typ.car_needed
        if needed:
            available = Boehnli.objects.filter(job_id=self.id,with_car=True)
            if available.count():
                return 'Ein Auto ist bereits verfügbar'
            else:
                return 'Ein Auto wird noch benötigt'
        else:
            return 'Kein Auto benötigt'
        
    def get_status_bohne_bar(self):
        boehnlis = Boehnli.objects.filter(job_id=self.id)
        participants = boehnlis.count()
        pctfull = participants * 100 / self.slots
        status = self.get_status_bohne_text()
        
        result = ''
        for i in range(self.slots):
            if participants > i:
                result += '<img title="{status}" src="/static/img/erbse_voll.png"/>'.format(status=status)
            else:
                result += '<img title="{status}" src="/static/img/erbse_leer.png"/>'.format(status=status)
        return result
    
    def get_status_bohne_text(self):
        boehnlis = Boehnli.objects.filter(job_id=self.id)
        participants = boehnlis.count()
        return "%d von %d gebucht" % (participants, self.slots)
        
    def get_status_bohne(self):
        boehnlis = Boehnli.objects.filter(job_id=self.id)
        participants = boehnlis.count()
        pctfull = participants * 100 / self.slots
        if pctfull >= 100:
            return "erbse_voll.png"
        elif pctfull >= 75:
            return "erbse_fast_voll.png"
        elif pctfull >= 50:
            return "erbse_halb.png"
        else:
            return "erbse_fast_leer.png"

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'


class Boehnli(models.Model):
    """
    Single boehnli (work unit).
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    loco = models.ForeignKey(Loco, on_delete=models.PROTECT)
    with_car = models.BooleanField("Auto verfügbar", default=False)

    def __unicode__(self):
        return u'Einsatz #%s' % self.id

    def zeit(self):
        return self.job.time

    class Meta:
        verbose_name = 'Einsatz'
        verbose_name_plural = 'Einsätze'


#model_audit.m2m(Abo.users)
model_audit.m2m(Abo.extra_abos)
model_audit.fk(Abo.depot)
model_audit.fk(Anteilschein.loco)

signals.post_save.connect(Loco.create, sender=Loco)
signals.post_delete.connect(Loco.post_delete, sender=Loco)

