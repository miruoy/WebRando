###
# WebRando — random content from web sources, safe for unregistered users.
#
#   urbandict [term]   Random (or specific) Urban Dictionary definition.
#   image <pool>       Random image from a configured pool (config: pools.json).
#
# All network access goes through urllib with a timeout and a browser-like
# User-Agent; no shell is ever spawned, so unregistered users can use it safely.
###
import os
import re
import json
import urllib.request
import urllib.parse
import urllib.error

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring
_ = PluginInternationalization('WebRando')


def _get_json(url, timeout=10):
    """Fetch a URL and parse JSON. Returns (data, error). No shell."""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return (json.loads(resp.read().decode('utf-8')), None)
    except (urllib.error.URLError, ValueError, OSError) as e:
        return (None, str(e))


def _load_pools():
    """Load pools.json from the plugin directory. Returns dict or {'__error__': ...}."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'pools.json')
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        pools = {}
        for name, val in data.items():
            if isinstance(val, dict) and 'type' in val and 'url' in val:
                pools[name] = val
        return pools
    except (OSError, ValueError) as e:
        return {'__error__': str(e)}


def _image_from_pool(pool):
    """Fetch a random image URL from a pool definition. Returns (url, error)."""
    ptype = pool.get('type')
    url = pool.get('url')
    if not url:
        return (None, 'pool has no url')
    (data, err) = _get_json(url)
    if err:
        return (None, err)
    if not data:
        return (None, 'empty response')

    try:
        if ptype == 'thecatapi':
            # [{"url": "https://cdn2.thecatapi.com/images/xxx.jpg"}]
            return (data[0]['url'], None)
        elif ptype == 'dogceo':
            # {"message": "https://images.dog.ceo/breeds/xxx.jpg", "status": "success"}
            return (data['message'], None)
        elif ptype == 'randomdog':
            # {"url": "https://random.dog/xxxx.mp4"}  (jpg/gif/mp4)
            return (data['url'], None)
        elif ptype == 'cataas':
            # {"url": "https://cataas.com/cat/xxx"} (dict) of [{"url": "..."}] (list)
            if isinstance(data, list):
                img = data[0]['url'] if data else ''
            else:
                img = data.get('url', '')
            if img.startswith('/'):
                img = 'https://cataas.com' + img
            return (img, None)
        elif ptype == 'direct':
            # de url zelf is al een image
            return (url, None)
        else:
            return (None, 'unknown pool type: %s' % ptype)
    except (KeyError, IndexError, TypeError) as e:
        return (None, 'failed to parse response: %s' % e)


class WebRando(callbacks.Plugin):
    """Random web content: Urban Dictionary definitions and random images."""

    threaded = True
    priority = 100

    # ------------------------------------------------------------------ urbandict
    @internationalizeDocstring
    def urbandict(self, irc, msg, args, term):
        """[term]

        Returns a definition from Urban Dictionary. If <term> is given, the
        definition of that word is shown; if no term is given, a random
        definition is returned.
        """
        if term:
            term = str(term).strip()
            url = 'https://api.urbandictionary.com/v0/define?term=%s' % \
                  urllib.parse.quote(term)
        else:
            url = 'https://api.urbandictionary.com/v0/random'

        (data, err) = _get_json(url)
        if err:
            irc.error(_('Urban Dictionary request failed: %s') % err, Raise=True)
        if not data or not data.get('list'):
            irc.error(_('No definition found.'), Raise=True)

        entry = data['list'][0]
        definition = (entry.get('definition') or '').strip()
        word = (entry.get('word') or term or '').strip()
        example = (entry.get('example') or '').strip()
        if not definition:
            irc.error(_('Definition was empty.'), Raise=True)

        lines = ['%s: %s' % (word, definition)]
        if example:
            lines.append('example: %s' % example)
        irc.replies(lines, joiner=' | ')
    urbandict = wrap(urbandict, [additional('something')])

    # --------------------------------------------------------------------- image
    @internationalizeDocstring
    def image(self, irc, msg, args, pool):
        """<pool>

        Posts a random image from a configured pool. Pools are defined in
        pools.json (in the plugin directory). Example: a pool "cat" might use
        thecatapi.com — `image cat` posts a random cat picture.

        Supported pool types: thecatapi, dogceo, randomdog, cataas, direct.
        """
        if not pool:
            irc.error(_('You must specify a pool name (see pools.json).'), Raise=True)
        pool = str(pool).strip().lower()

        pools = _load_pools()
        if '__error__' in pools:
            irc.error(_('Failed to load pools.json: %s') % pools['__error__'], Raise=True)
        if pool not in pools:
            avail = ', '.join(sorted(pools.keys())) or '(none)'
            irc.error(format(_('Unknown pool %s. Available: %s'), pool, avail), Raise=True)

        (img, err) = _image_from_pool(pools[pool])
        if err:
            irc.error(_('Could not fetch image: %s') % err, Raise=True)
        irc.reply(img)

    image = wrap(image, [additional('something')])


Class = WebRando

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
