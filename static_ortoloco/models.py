from django.db import models
from tinymce import models as tinymce_models


# Create your models here.

class StaticContent(models.Model):
    """
    All the static contents for the normal webpage
    
    TODO add constants for different types, e.g.
    - HomeUnterMenu
    - Willkommen
    - IntranetHome
    """
    name = models.CharField("Name", max_length=100)
    content = tinymce_models.HTMLField("Html-Inhalt", max_length=10000, default="", blank=True)

    @staticmethod
    def getByName(name, is_staff=False):
        contents = StaticContent.objects.all().filter(name=name)
        if contents.__len__() > 0:
            content = contents[0].content
            edit_link = '/admin/static_ortoloco/staticcontent/' + str(contents[0].id)
        else:
            content = ''
            edit_link = '/admin/static_ortoloco/staticcontent/add'
            
        if is_staff:
            content = '<div class="admin_editable">' + content
            content += '(<a class="admin_edit_link" href="' + edit_link + '">Diesen Text editieren</a>)</div>'
            
        return content

    def __unicode__(self):
        return u"%s" % (self.name)

    class Meta:
        verbose_name = "Statischer Inhalt"
        verbose_name_plural = "Statische Inhalte"


class Media(models.Model):
    """
    All the medias that mentioned ortoloco
    """
    mediafile = models.FileField("Datei", upload_to='medias')
    name = models.CharField("Titel", max_length=200)
    year = models.CharField("Jahr", max_length=4)


    def __unicode__(self):
        return u"%s" % (self.name)

    class Meta:
        verbose_name = "Media"
        verbose_name_plural = "Medien"


class Download(models.Model):
    """
    All the downloads available on ortoloco.ch
    """
    mediafile = models.FileField("Datei", upload_to='downloads')
    name = models.CharField("Titel", max_length=200)


    def __unicode__(self):
        return u"%s" % (self.name)

    class Meta:
        verbose_name = "Download"
        verbose_name_plural = "Downloads"


class Link(models.Model):
    """
    All the links that are mentioned on ortoloco.ch
    """
    name = models.CharField("Link", max_length=200)
    description = models.CharField("Beschreibung", max_length=400)

    def __unicode__(self):
        return u"%s" % (self.name)

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"


class Politoloco(models.Model):
    email = models.EmailField("E-Mail Adresse")

    def __unicode__(self):
        return u'Politoloco %s' % self.email

    class Meta:
        permissions = (('can_send_newsletter', 'Kann politoloco-Newsletter verschicken'),)