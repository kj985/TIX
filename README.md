# TIX: gig promotion tool for Sarah McLeod

A small app that runs on your Mac. It shows all of Sarah's gigs in one dashboard:

- **Imports** upcoming gigs from her Bandsintown page.
- **Tags** each gig with its project (Sarah McLeod, Sarah & Mick, The Superjesus). It detects the project automatically, and you can change it.
- **Lists** date, days to go, project, venue, city and ticket link, with a filter by project and Upcoming / Past / All.
- **Stores your own details** for each gig: ad budget (AUD), notes, tickets sold, and an optional ticket link override.
- **Keeps everything on your computer** in one file (`data/gigs.db`). Re-importing never overwrites what you've typed.

This is stage 1. Later stages will add Meta (Facebook/Instagram) ads and ticket-click tracking (see [Later stages](#later-stages)).

---

## Why this tech

| Piece | Why |
|---|---|
| **Python** | Free, one installer on Mac, very widely used. Meta's official ads library is Python too, so stage 2 fits in. |
| **Flask** | A small, popular way to make a web page from Python. The dashboard runs in your browser, but only on your Mac. |
| **SQLite** | A database that is just one file. No server to install. Back it up by copying `data/gigs.db`. |

No accounts, no cloud hosting, no monthly costs.

---

## Setup (one time, about 15 minutes)

You'll type a few commands into **Terminal**, the Mac's built-in command window. To open it, press `Cmd + Space`, type **Terminal**, and press Enter. When a step shows a command, copy it, paste it into Terminal, and press Enter.

### Step 1: Install Python

1. Go to **https://www.python.org/downloads/** and click the big yellow **Download Python 3.x** button.
2. Open the downloaded file and click through the installer (the defaults are fine).
3. When it finishes, a Finder window opens. Double-click **Install Certificates.command** in it. This lets Python make secure web connections.
4. Check it worked. **Close Terminal completely (Cmd + Q) and reopen it**, then run:
   ```
   python3 --version
   ```
   You should see `Python 3.11` or higher (e.g. `Python 3.13.1`).
   If you see `3.9`, or a pop-up asks to install "command line developer tools", you're still running Apple's old built-in Python. Make sure the python.org installer finished, then quit and reopen Terminal.

### Step 2: Download this tool

1. On GitHub, open this repository and switch to the branch the code is on (until it's merged, that's `claude/sarah-mcleod-gig-tool-2wxl4o`).
2. Click the green **Code** button, then **Download ZIP**.
3. Unzip it and move the folder somewhere easy to find, e.g. your **Documents** folder. Rename the folder to `TIX`.

### Step 3: Start it and try the sample gigs

In Terminal, go to the folder and start the tool. (If you put it elsewhere, change the path. You can also type `cd `, with a space, then drag the folder onto the Terminal window.)

```
cd ~/Documents/TIX
./start.sh
```

The first time, it takes a minute or two to set itself up. Then your browser opens at **http://localhost:5050**.

- Click **Load sample gigs**. You'll see 13 made-up gigs, marked SAMPLE, so you can try everything: filter by project, change a project, click **Edit** to add a budget, notes or tickets sold. Two of them are in the past (click **Past**) so you can practise entering tickets sold.
- When you're done, click **Delete sample gigs**.

Leave the Terminal window open while you use the dashboard. To stop the tool, click the Terminal window and press `Ctrl + C`.

> If you see `permission denied: ./start.sh`, run `chmod +x start.sh` once, then try again.
> If a security pop-up says Python wants to accept network connections, click **Deny**. The tool doesn't need it.

### Step 4: Get your Bandsintown API key and add it

Bandsintown calls its API key an **app_id**. Only someone who manages Sarah's artist page can get one.

1. Log in to **Bandsintown for Artists** (https://artists.bandsintown.com) with the account that manages Sarah's page.
2. Go to **Settings** (under her artist profile), then **General**, then click **Get API Key**. If one already exists, click **Copy API Key**.
   (Bandsintown's help page: https://help.artists.bandsintown.com/en/articles/7053475-api-and-app-id)
3. In the `TIX` folder, make a copy of **config.example.toml** and name the copy **config.toml**.
   Finder may hide the ending, so it's easiest in Terminal:
   ```
   cp config.example.toml config.toml
   open -e config.toml
   ```
4. In the file that opens (TextEdit), paste the key between the quotes:
   ```
   app_id = "paste-your-key-here"
   ```
   Check that `artist_name = "Sarah McLeod"` is spelled exactly as on Bandsintown. Then save and close.
5. Back in the dashboard, reload the page and click **Import from Bandsintown**.

Keep the key private: `config.toml` is set up never to be uploaded to GitHub. Bandsintown keys only work for the artist they belong to.

---

## Everyday use

```
cd ~/Documents/TIX
./start.sh
```

Click **Import from Bandsintown** whenever you want fresh gigs. Run it as often as you like.

You can also run these instead of `./start.sh`:

| Command | What it does |
|---|---|
| `./start.sh import` | Import from Bandsintown without opening the dashboard |
| `./start.sh import --sample` | Load the sample gigs |
| `./start.sh clear-sample` | Delete the sample gigs |

### How importing treats your data

- Each gig is matched by its Bandsintown ID, so re-importing **updates** it rather than duplicating it.
- Only Bandsintown's own details are refreshed: date, time, venue, city, ticket link, title, lineup and description.
- **Ad budget, notes, tickets sold and the ticket link override are never touched.**
- Projects you set by hand are never changed. Projects marked **Auto:** are re-detected on each import, so improving your keywords fixes them all at once.
- Gigs are never deleted. If an upcoming gig disappears from Bandsintown (often a cancellation), it's flagged **"No longer on Bandsintown: cancelled?"**. Past gigs stay so you can fill in tickets sold.

### How project detection works

`config.toml` lists each project with some keywords. For each gig, the tool looks for those keywords in:

1. the **title** (strongest),
2. the **lineup**,
3. the **description** (weakest).

The project with the strongest match wins. If nothing matches, the gig gets the `fallback_project` (Sarah McLeod solo). Hover over a project dropdown to see why it was chosen.

To correct one gig, pick a project from its dropdown. It's then marked as set by hand and stays that way. To go back to automatic, choose **Auto-detect**.

To improve detection for all gigs, edit the keywords in `config.toml`, save, and click **Import** again. A good one to add is Mick's full name under "Sarah & Mick", if it appears in lineups. Don't use plain "Sarah McLeod" as a keyword, because it's in every lineup.

### Dates and times

Gig times are shown as Bandsintown lists them (the venue's local time). "Days until" is counted using the `timezone` in `config.toml` (default `Australia/Sydney`). Gigs within 14 days are highlighted in red, as a reminder that ads should already be running.

### Backing up

All your data is in **`data/gigs.db`**. Copy that file somewhere safe now and then.

### Updating to a newer version of this tool

Download the new ZIP. Then copy **`config.toml`** and the **`data`** folder from your old `TIX` folder into the new one before you start it.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python3: command not found`, or it says 3.9 | Redo step 1, then quit and reopen Terminal. |
| `Import failed: ... rejected the app_id` | Re-copy the key from Bandsintown for Artists into `config.toml`. Check for missing quotes or extra spaces. |
| `Import failed: Couldn't reach Bandsintown` | Check your internet. If it mentions `SSLError`, run step 1.3 (Install Certificates.command). |
| `Settings problem: ...` on the page | There's a typo in `config.toml`. The message says which line. Fix it, save, reload. |
| `Address already in use` | The tool is already running in another Terminal window. Use that one, or change `port` in `config.toml`. |
| Page won't load | Make sure the Terminal window running `./start.sh` is still open. |

---

## Later stages

The code is set out so these can be added without changing what's already there:

- **Meta ads** (`gigtool/integrations/meta_ads.py`): create a campaign per gig from its ad budget and target people near the venue. Daily spend and results will go in a new table linked to each gig.
- **Click tracking** (`gigtool/integrations/click_tracking.py`): each gig has a permanent ID, so Sarah's website can host links like `/tickets/<gig id>` that count clicks (and which ad sent them) before redirecting to the ticket seller.
- **Cost per ticket over time**: ad spend ÷ the tickets sold you enter after each show.

### For developers

```
gigtool/
  __main__.py          command line (run / import / clear-sample)
  config.py            reads config.toml
  db.py                SQLite schema; add tables by appending to MIGRATIONS
  sources/             where gigs come from (bandsintown.py, sample.py)
  importer.py          merges events into the db without touching manual fields
  projects.py          keyword-based project detection
  gigs.py              read/update gigs (use this from new code)
  web.py, templates/   the dashboard
  integrations/        Meta ads + click tracking (planned)
sample_data/           fake Bandsintown API responses for testing
tests/                 python -m unittest discover -s tests -t .
```
