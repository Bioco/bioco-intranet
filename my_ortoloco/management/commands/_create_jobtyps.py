# -*- coding: utf-8 -*-
from my_ortoloco.models import *

jobtyps = [ 
{
'name':            u'Ernten vor Verteilfahrt',
'displayed_name':  None,
'duration':        4,
'bereich':         u'Ernten und Verpacken',
'location':        u'Geisshof',
'description':     u'''Wir ernten unser Gemüse und erledigen sonstige Arbeiten. Gute Schuhe und wetterfeste Kleidung anziehen.''',
},

{
'name':            u'Verteilfahrt Dienstag',
'displayed_name':  None,
'duration':        4,
'bereich':         u'Verteilfahrten',
'location':        u'Geisshof und unterwegs',
'description':     u'Fahren oder Mitfahren (entsprechendes Feld ankreuzen), mindestens eine Person bringt ein Auto mit und fährt damit zu den Depots. Du informierst dich über die <a href="http://bioco.ch/intranet/touren_bioco_dienstag/">Route zu den Depots und den Verteilplan</a>.',
},

{
'name':            u'Verteilfahrt Freitag',
'displayed_name':  None,
'duration':        4,
'bereich':         u'Verteilfahrten',
'location':        u'Geisshof und unterwegs',
'description':     u'Fahren oder Mitfahren (entsprechendes Feld ankreuzen), mindestens eine Person bringt ein Auto mit und fährt damit zu den Depots. Du informierst dich über die <a href="http://bioco.ch/intranet/touren_bioco_freitag/">Route zu den Depots und den Verteilplan</a>.',
},


{
'name':            u'Aktionstag',
'displayed_name':  None,
'duration':        8,
'bereich':         u'Events',
'location':        u'Geisshof',
'description':     u'Gartengenuss am Wochenende: Von 9 bis 17 Uhr arbeiten wir auf Hof und Feld. Du bist auch willkommen, wenn du nicht den ganzen Tag bleiben kannst. Findet bei jedem Wetter statt. Fürs Zmittag ist gesorgt.',
},


{
'name':            u'Feierabendjäten',
'displayed_name':  None,
'duration':        3,
'bereich':         u'Ernten und Verpacken',
'location':        u'Geisshof',
'description':     u'Nach einem Tag am Schreibtisch lockt die Abendsonne noch einmal raus aufs Feld. Dann ist es Zeit fürs Feierabendjäten mit kühlem Bier und Sirup. 18-21 Uhr.',
},


]

"""
TODO Adjust for bioco
{
'name':            u'Abpackkoordination',
'displayed_name':  None,
'duration':        5,
'bereich':         u'abpacken',
'location':        u'Abpackraum',
'description':     u'Du bist bereits ein alter Hase beim Abpacken. Du kommst um 8.30, bereitest vor, koordinierst das Abpacken anhand der Checkliste und kommunizierst mit der Betriebsgruppe.',
},



{
'name':            u'Gmües abpacken',
'displayed_name':  None,
'duration':        4,
'bereich':         u'abpacken',
'location':        u'Abpackraum',
'description':     u'Wir waschen, rüsten und verpacken das Gemüse für die Verteilung. Von 9-12h. Bei kaltem Wetter warme Kleider und Handschuhe mitbringen.',
},




{
'name':            u'Ernteverteilung+F',
'displayed_name':  None,
'duration':        4,
'bereich':         u'verteilen',
'location':        u'Zürcherstr. 43, Dietikon',
'description':     u'Fahren (mit Führerschein): Du bringst zusammen mit einer/m MitfahrerIn die Gemüsetaschen in die Depots. Das Auto steht an der Zürcherstr. 43 in Dietikon.',
},




{
'name':            u'Freitagsaktionstag',
'displayed_name':  None,
'duration':        8,
'bereich':         u'rand',
'location':        u'Fondli-Hof',
'description':     u'',
},



{
'name':            u'Kochen am Aktionstag',
'displayed_name':  None,
'duration':        5,
'bereich':         u'rand',
'location':        u'Fondli-Hof',
'description':     u'Du bist für einmal KöchIn und verwöhnst das Aktionstag-Team um ca. 12:30 Uhr mit einem feinen Zmittag. Diverses Gemüse gibts im Kühlraum (angeschrieben). Risotto, Pasta, Couscous, Olivenöl, Kaffee etc. gibts von der Foodcoop El Comedor an Lager im Abpackraum.',
},



{
'name':            u'Tageseinsatz',
'displayed_name':  None,
'duration':        8,
'bereich':         u'garten',
'location':        u'Acker',
'description':     u'Du stehst den GärtnerInnen tatkräftig zur Seite bei allen anstehenden Arbeiten. Von 8-17h. Fürs Zmittag ist gesorgt. Man kann auch nur einen halben Tag kommen.',
},



{
'name':            u'Fyrobigjäte',
'displayed_name':  None,
'duration':        3,
'bereich':         u'garten',
'location':        u'Fondli-Hof',
'description':     u'Nach einem Tag am Schreibtisch lockt die Abendsonne noch einmal raus aufs Feld. Dann ist es Zeit fürs Fyrobigjäte mit kühlem Bier und Sirup. 18-21 Uhr.',
},



{
'name':            u'Beeren ernten',
'displayed_name':  None,
'duration':        1,
'bereich':         u'beeren',
'location':        u'Fondli-Hof',
'description':     u'Reife Himbeeren ablesen und einfrieren. Zeit am vereinbarten Tag frei wählbar, dauert ca. 1 Stunde. Bei Fragen melde dich frühzeitig bei François: 079 723 02 61',
},
"""


def create_jobtyps():
    print '***************************************************************'
    print 'Creating JobTypes'
    print '***************************************************************'
        
    for d in jobtyps:
        print (u'adding %s to bereich %s:' % (d["name"], d["bereich"])).encode('utf-8')
        d["bereich"] = Taetigkeitsbereich.objects.get(name=d["bereich"])
        obj = JobTyp(**d)
        obj.save()
