#!/usr/bin/env python
# encoding: utf-8

import sys
if sys.version_info.major < 3:
    print('ERROR! This script requires Python3. Exiting...')
    sys.exit(0)

import os
import urllib.request
import gzip
import xml.etree.ElementTree as ET
import pickle

from game import GameWord


def download_file(url_base, filename):
    full_url = url_base + filename
    with urllib.request.urlopen(full_url) as response:
        with open(filename, 'wb') as local:
            local.write(response.read())


def parse_file(dict_filename, cache_filename):
    # FIXME ElementTree always resolves entitites, so no 'n', 'adj-i'...
    # TODO Are all these categories actually valid?
    pos_nouns = [
        "adjectival nouns or quasi-adjectives (keiyodoshi)",
        "'nouns which may take the genitive case particle `no'",
        "pre-noun adjectival (rentaishi)",
        "noun or verb acting prenominally",
        "idiomatic expression",
        "noun (common) (futsuumeishi)",
        "adverbial noun (fukushitekimeishi)",
        "noun, used as a suffix",
        "noun, used as a prefix",
        "noun (temporal) (jisoumeishi)",
        "onomatopoeic or mimetic word",
        #"noun or participle which takes the aux. verb suru",
    ]
    words = []

    with gzip.open(dict_filename) as contents:
        print('Parsing XML (this may take a while)')
        parser = ET.XMLParser()
        root = ET.parse(contents, parser=parser).getroot()
        # NOTE see DTD for file structure
        for element in root.findall('entry'):
            # Kanji elements
            kebs = []
            k_priorities = []
            for k_ele in element.findall('k_ele'):
                keb = k_ele.find('keb')
                kebs.append(keb.text)
                for ke_pri in k_ele.findall('ke_pri'):
                    k_priorities.append(ke_pri.text)
            # Reading elements
            rebs = []
            r_priorities = []
            for r_ele in element.findall('r_ele'):
                reb = r_ele.find('reb')
                rebs.append(reb.text)
                for re_pri in r_ele.findall('re_pri'):
                    r_priorities.append(ke_pri.text)
            # Use only the most common words, i.e. nfXX
            combined = set(k_priorities).union(set(r_priorities))
            keep = False
            rank = None
            for p in combined:
                if 'nf' in p:
                    keep = True
                    rank = int(p[2:])
            if not keep:
                continue
            # Sense elements
            is_noun = False
            for sense in element.findall('sense'):
                for pos in sense.findall('pos'):
                    if pos.text in pos_nouns:
                        is_noun = True
                        break
            # Keep only the first element of each entry
            gw = GameWord(kanji=kebs[0] if kebs else '', kana=rebs[0],
                          rank=rank, is_noun=is_noun)
            words.append(gw)
    return words


def get_data():
    url_base = 'http://ftp.monash.edu.au/pub/nihongo/'
    dict_name = 'JMdict_e.gz'
    cache_name = 'cache.pickle'
    words = []
    # Get cache file if not already there
    if not os.path.exists(cache_name):
        print('Cache file not found')
        # Get dictionary file if not already there
        if not os.path.exists(dict_name):
            print('Downloading {} from {}'.format(dict_name, url_base))
            download_file(url_base, dict_name)
        else:
            print('{} exists, reusing local copy'.format(dict_name))
        # File exists, parse it and write to cache
        words = parse_file(dict_name, cache_name)
        with open(cache_name, 'wb') as f:
            pickle.dump(words, f)
    else:
        print('Cache file exists')
        with open(cache_name, 'rb') as f:
            words = pickle.load(f)
    return words

if __name__ == '__main__':
    words = get_data()
    print('INFO total words: {}, valid nouns: {}'.format(len(words),
          len([w for w in words if w.is_noun])))
