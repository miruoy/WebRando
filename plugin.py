###
# WebRando — random content from web sources, safe for unregistered users.
#
#   urbandict [term]   Random (or specific) Urban Dictionary definition.
#   reddit <pool>       Random IMAGE from a pool of subreddits (config: pools.json).
#
# All network access goes through urllib with a timeout and a real User-Agent;
# no shell is ever spawned, so unregistered users can use it safely.
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
    """Load pools.json from the plugin directory. Returns dict or {}."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'pools.json')
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        # normaliseer: pool -> lijst van subreddit-namen
        pools = {}
        for name, val in data.items():
            if isinstance(val, dict) and 'subreddits' in val:
                subs = val['subreddits']
            else:
                subs = val  # ook accepteren als platte lijst
            if isinstance(subs, (list, tuple)):
                pools[name] = [str(s).strip().lstrip('r/').strip('/') for s in subs if s]
        return pools
    except (OSError, ValueError) as e:
        return {'__error__': str(e)}


class WebRando(callbacks.Plugin):
    """Random web content: Urban Dictionary definitions and Reddit images."""

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

        # Eerste (top) definitie; val terug op een willekeurige als die leeg is
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

    # -------------------------------------------------------------------- reddit
    @internationalizeDocstring
    def reddit(self, irc, msg, args, pool):
        """<pool>

        Posts a random IMAGE from a configured pool of subreddits. Pools are
        defined in pools.json (in the plugin directory). Example: a pool
        "cat" might contain aww, cats, catpictures — `reddit cat` posts a
        random image from one of those.
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

        subs = pools[pool]
        # shuffle zodat niet altijd de eerste subreddit gekozen wordt
        import random
        random.shuffle(subs)

        IMAGE_RE = re.compile(r'\.(jpg|jpeg|png|gif)$', re.I)
        found = None
        for sub in subs:
            # Reddit's /random.json geeft een willekeurige post uit de sub
            url = 'https://www.reddit.com/r/%s/random.json?limit=1' % sub
            (data, err) = _get_json(url)
            if err or not data:
                continue
            posts = data[0].get('data', {}).get('children', []) if isinstance(data, list) else []
            for p in posts:
                post = p.get('data', {})
                img = post.get('url', '')
                # accepteer i.redd.it / imgur directe images
                if IMAGE_RE.search(img) or 'i.redd.it' in img or 'i.imgur.com' in img:
                    found = img
                    break
            if found:
                break

        if not found:
            irc.error(_('No image found in pool %s. Reddit often blocks '
                        'datacenter IPs (HTTP 403) - if the bot runs on a '
                        'server, this may fail; try from a residential IP or '
                        'add Reddit OAuth later.') % pool, Raise=True)
        irc.reply(found)

    reddit = wrap(reddit, [additional('something')])


Class = WebRando

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
