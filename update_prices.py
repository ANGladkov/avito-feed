# -*- coding: utf-8 -*-
"""Обновляет ТОЛЬКО цены и наличие в avito.xml из свежего YML сайта. Обложки/описания/категории НЕ трогает.
Запускается роботом GitHub Actions ежедневно (в репозитории avito-feed, avito.xml в текущей папке).
Локальный тест: python3 update_prices.py --dry ~/Downloads/avito-upload/avito.xml
Цена Авито = round(price_сайта * 0.95). Распроданное (available=false или нет в YML) удаляется из фида."""
import re, sys, os, urllib.request

YML_URL='https://magazin-sportlife.ru/export/yml.php'
AVITO=os.environ.get('AVITO_PATH','avito.xml')
dry='--dry' in sys.argv
args=[a for a in sys.argv[1:] if not a.startswith('--')]
if args: AVITO=args[0]

data=urllib.request.urlopen(YML_URL, timeout=90).read().decode('utf-8')
offers=re.findall(r'<offer id="(\d+)"[^>]*available="(\w+)"[^>]*>(.*?)</offer>', data, re.S)
# защита: если YML не скачался/битый — НЕ трогаем фид
if len(offers) < 500:
    print(f'ОТМЕНА: в YML только {len(offers)} товаров (ждём >=500) — фид не меняю'); sys.exit(0)

info={}
for oid, av, body in offers:
    m=re.search(r'<price>(.*?)</price>', body)
    info[oid]=(int(m.group(1)) if m and m.group(1).isdigit() else None, av=='true')

xml=open(AVITO, encoding='utf-8').read()
ads=re.findall(r'  <Ad>.*?  </Ad>', xml, re.S)
out=[]; changed=0; removed=[]
for a in ads:
    idm=re.search(r'<Id>SL(\d+)</Id>', a)
    oid=idm.group(1) if idm else None
    price, avail = info.get(oid, (None, True))   # неизвестных (не SL/нет в YML) не трогаем по цене, но проверим наличие
    if oid in info and not avail:
        removed.append(oid); continue            # распродан — убрать из фида
    if price:
        a2=re.sub(r'<Price>\d+</Price>', f'<Price>{round(price*0.95)}</Price>', a, count=1)
        if a2 != a: changed+=1
        a=a2
    out.append(a)

new='<?xml version="1.0" encoding="UTF-8"?>\n<Ads formatVersion="3" target="Avito.ru">\n'+'\n'.join(out)+'\n</Ads>\n'
print(f'обновлено цен: {changed} | убрано распроданных: {len(removed)} {removed} | осталось объявлений: {len(out)}')
if dry:
    print('(--dry: файл не записан)')
else:
    open(AVITO,'w',encoding='utf-8').write(new)
    print('avito.xml записан')
