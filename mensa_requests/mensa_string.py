#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import html, etree
import requests
import datetime
from datetime import timedelta
import time
import json
import hashlib
import sys

def to_node(type, message):
	# convert to json and print (node helper will read from stdout)
	try:
		print(json.dumps({type: message}))
	except Exception:
		pass
	# stdout has to be flushed manually to prevent delays in the node helper communication
	sys.stdout.flush()


day_name = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
ign_types = ['Beilagen', 'Salate']
ign_names = ['T?glich wechselndes Dessertangebot.', 'T?glich wechselnde Dessertvariationen.',
             'Pommes frites, wahlweise mit Majon?se oder Ketchup', 'Verschiedene Pastasorten mit So?e',
             'Verschiedene Pastasorten mit So?e und Toppings nach Wahl', 'Hausgemachte Milchshakes',
             'Pommes-Spezialit?t']

url = 'http://www.studierendenwerk-bielefeld.de/essen-trinken/essen-und-trinken-in-mensen/bielefeld/mensa-gebaeude-x.html'

offset = 0



for v in sys.argv[1:]:
    if v[0]:
        offset = int(v[0])

def parse_menu_week(tree):
    menu_week = tree.findall(".//div[@id='c1367']/div[@class='mensa plan']/div/table/tbody")
    menu_dates = tree.findall(".//div[@id='c1367']/h2")
    menu_dates = [d.text.strip().split(' ')[1] for d in menu_dates]
    menu_dates = [datetime.datetime.strptime(d, '%d.%m.%Y').date() for d in menu_dates]
    mensa_menus_week = list()
    for index, day in enumerate(menu_week):
        day_plan = dict()
        day_plan['date'] = menu_dates[index].isoformat()
        day_menus = day.findall("tr/td[@class='first']")
        for day_menu in day_menus:
            menu_type = day_menu.find("h3/strong").text.strip()
            itm = day_menu.find("p[2]")
            name = ''.join(itm.xpath("./text()")).strip()
            tags = itm.xpath("sup/text()")
            if tags:
                tags = ','.join(tags).split(',')
                tags = [i.replace('(', '') for i in tags]
                tags = [i.replace(')', '') for i in tags]
                tags = set(tags)
            itm = day_menu.find("p[4]")
            menu_sides = ['']
            if (itm is not None): # and (menu_type not in ['Mensa vital']):
                menu_sides = ''.join(itm.xpath("./text()"))
                menu_sides = menu_sides.replace(' oder', ',')
                menu_sides = menu_sides.replace(' und', ',')
                menu_sides = [_i.strip() for _i in menu_sides.split(',')]
                if menu_sides in [['auch zum Mitnehmen!']]:
                    menu_sides = ['']
           # if not all([menu_type, name]) or menu_type in ign_types or any(sub in name for sub in ign_names):
           #     continue
            type_list = day_plan.get(menu_type, list())
            type_list.append(dict({'name': name, 'tags': tags, 'sides': menu_sides}))
            day_plan.update(dict({menu_type: type_list}))
        mensa_menus_week.insert(index, day_plan)
    return mensa_menus_week

page = requests.get(url)
tree = html.fromstring(page.content)
mensa_week = parse_menu_week(tree)

next_url = tree.find(".//div[@id='c1367']/div/a[2]")
if next_url is not None:
    next_url = 'http://www.studierendenwerk-bielefeld.de' + next_url.attrib['href']
    next_page = requests.get(next_url)
    next_tree = html.fromstring(next_page.content)
    mensa_week += parse_menu_week(next_tree)

# print output
order = [u'Tagesmenü', u'Menü vegetarisch', u'Eintopf', u'Eintopf / Suppe', u'Mensa vital', u'Mensa kulinarisch', u'Aktions-Theke']
menus = list()
menu_ind = None
return_dict = []
menu_date = str((datetime.datetime.now() + timedelta(hours=offset)).strftime("%Y-%m-%d"))

# select current date
for ind, d in enumerate(mensa_week):
    if d['date'] == menu_date:
        menus = d.copy()
        menu_ind = ind
        break
if(len(menus) is 0):
    return_dict.append({"name": "NO MENSA!", "value": " "})
    to_node('MensaPlan', [menu_date, return_dict])
    quit()

for i in range(len(order)):
    t = order[i]
    for d in menus.pop(t, []):
        if t in [u'Menü vegetarisch']:
            t = 'Vegetarisch'

        if t in ['Eintopf'] and d['sides']:
            extra = ' (' + ', '.join(d['sides']) + ')'

        return_dict.append({ "name" : t , "value" : d['name']})

# rest
dessert = []
for d in menus.pop('Dessertbuffet', []):
    dessert.append(d['name'])

if (dessert is not []):
    return_dict.append({"name" : 'Dessertbuffet', "value" : ', '.join(dessert)});


# sides
sides = []
for i in mensa_week[menu_ind].get(u'Tagesmenü', []):
    sides += i.get('sides')
     #for i in mensa_week[menu_ind].get(u'Menü vegetarisch', []):
#    sides += i.get('sides', '')
if sides != []:
    return_dict.append({"name": "Sides", "value": ', '.join(sides)})
    #print('*{:s}:* _{:s}_'.format(u'Beilagen', ', '.join(set(sides)).encode('utf-8')))


to_node('MensaPlan',[menu_date, return_dict] )