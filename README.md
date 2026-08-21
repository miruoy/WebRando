# WebRando

A Limnoria plugin that posts random content from web sources, safe for
**unregistered** users (no shell, no capability needed).

## Commands

| Command | Description |
| --- | --- |
| `urbandict` | A random Urban Dictionary definition. |
| `urbandict <term>` | The definition of `<term>` from Urban Dictionary. |
| `image <pool>` | A random image from a configured pool (config: `pools.json`). |

## How it works

- All network access goes through `urllib` with a timeout and a browser-like
  User-Agent. **No shell is spawned**, so there is no command-injection risk
  and unregistered users can use it safely.
- `urbandict` calls the public Urban Dictionary API
  (`api.urbandictionary.com/v0/random` and `/define?term=`).
- `image` reads `pools.json` (in this directory), fetches a random image from
  the requested pool's source, and replies with the image URL.

## Configuration: pools.json

Each pool has a `type` (which source to use) and a `url`. The plugin directory
ships with a sample `pools.json`:

```json
{
  "cat":    { "type": "thecatapi", "url": "https://api.thecatapi.com/v1/images/search" },
  "dog":    { "type": "dogceo",    "url": "https://dog.ceo/api/breeds/image/random" },
  "woof":   { "type": "randomdog", "url": "https://random.dog/woof.json" },
  "cataas": { "type": "cataas",    "url": "https://cataas.com/cat?json=true" }
}
```

### Supported pool types

| type | source | notes |
| --- | --- | --- |
| `thecatapi` | thecatapi.com | random cat picture (keyless) |
| `dogceo` | dog.ceo | random dog picture (keyless) |
| `randomdog` | random.dog | random dog (jpg/gif/mp4) (keyless) |
| `cataas` | cataas.com | random cat (jpg/gif) (keyless) |
| `direct` | the `url` itself is the image | for static/known image URLs |

To add your own pool, edit `pools.json` and create an alias in the bot:

```
alias add cat  "image cat"
alias add dog  "image dog"
alias add woof "image woof"
```

Now `@cat`, `@dog`, `@woof` post a random image from their respective source.

> Note: pool names are case-insensitive.

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

## Troubleshooting

- **`Unknown pool X. Available: ...`** — the pool name is not in `pools.json`.
  Add it, or check the spelling (case-insensitive).
- **`Failed to load pools.json: ...`** — the JSON file is missing or invalid.
  Fix `pools.json` in the plugin directory.
- **`Could not fetch image: ...`** — network issue, the source is down, or the
  API response changed. Urban Dictionary and the image APIs above are
  keyless and generally not IP-blocked; if a specific source fails, try another.

## License

Licensed under the GNU General Public License v2 (GPL-2.0). See the
`LICENSE` file for the full text.

