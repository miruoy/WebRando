# WebRando

A Limnoria plugin that posts random content from web sources, safe for
**unregistered** users (no shell, no capability needed).

## Commands

| Command | Description |
| --- | --- |
| `urbandict` | A random Urban Dictionary definition. |
| `urbandict <term>` | The definition of `<term>` from Urban Dictionary. |
| `reddit <pool>` | A random IMAGE from a configured pool of subreddits. |

## How it works

- All network access goes through `urllib` with a timeout and a browser-like
  User-Agent. **No shell is spawned**, so there is no command-injection risk
  and unregistered users can use it safely.
- `urbandict` calls the public Urban Dictionary API
  (`api.urbandictionary.com/v0/random` and `/define?term=`).
- `reddit` reads `pools.json` (in this directory), picks a random subreddit
  from the requested pool, fetches a random post, and replies with the image
  URL if it is a direct image (i.redd.it / i.imgur.com / `*.jpg|png|gif`).
  Only images are posted — no text/link posts.

## Configuration: pools.json

Pools map a name to a list of subreddits. The plugin directory contains a
sample `pools.json`:

```json
{
  "cat":  { "subreddits": ["aww", "cats", "catpictures", "MEOW_IRL"] },
  "art":  { "subreddits": ["Art", "Painting", "DigitalArt", "Illustration"] },
  "food": { "subreddits": ["FoodPorn", "Pizza", "steak", "Cooking"] },
  "car":  { "subreddits": ["cars", "Autos", "industrial_design"] }
}
```

Edit it to add your own pools, then create aliases in the bot:

```
alias add cat  "reddit cat"
alias add art  "reddit art"
alias add food "reddit food"
```

Now `@cat`, `@art`, `@food` post a random image from their respective pool.

> Note: pool names are case-insensitive. Subreddit names are normalised
> (leading `r/` or `/` is stripped).

## Installation

Copy the plugin directory into your bot's plugin path, then load it:

```bash
cp -r WebRando /path/to/your/bot/plugins/
rm -rf /path/to/your/bot/plugins/WebRando/__pycache__
# in the bot:
load WebRando
```

If you are replacing a previously loaded copy and the bot keeps running old
code, remove the `__pycache__` directory and `touch` the `.py` files (or
unload, delete, re-copy under a new name, then load) before reloading — a
stale `.pyc` will keep the old code live.

## Known limitation: Reddit 403 on datacenter IPs

Reddit blocks most non-OAuth requests originating from datacenter/server IPs
(including Hetzner/YouServer ranges). If the bot runs on such a host, the
`reddit` command may fail with a `403 Blocked` error from Reddit. This is an
environment restriction, not a plugin bug:

- Urban Dictionary works from anywhere (it does not block datacenter IPs).
- Reddit may work if the bot runs from a residential IP, or if you later add
  Reddit OAuth (client_id + secret) to the fetch logic.

The plugin reports a clear message when Reddit blocks the request, so it fails
gracefully rather than crashing.

## Troubleshooting

- **`Unknown pool X. Available: ...`** — the pool name is not in `pools.json`.
  Add it, or check the spelling (case-insensitive).
- **`Failed to load pools.json: ...`** — the JSON file is missing or invalid.
  Fix `pools.json` in the plugin directory.
- **`No image found in pool X. Reddit often blocks datacenter IPs...`** — see
  the known limitation above; try later or from a different host.
- **`Urban Dictionary request failed: ...`** — network issue or API down.
