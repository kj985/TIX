"""Meta (Facebook / Instagram) ads. NOT BUILT YET: this is the plan.

Stage 2 will:
1. For each upcoming gig with an ad budget, create a campaign through the
   Meta Marketing API (official Python library: facebook-business), targeting
   people near the venue's city who like the gig's project.
2. Point the ad at the gig's tracked ticket link (see click_tracking.py),
   so ticket clicks can be counted per ad.
3. Pull spend and results back each day and store them in a new
   `ad_campaigns` table linked to gigs.id. Add the table as a new entry in
   db.MIGRATIONS so existing data is kept.
4. Cost per ticket = total spend / gigs.tickets_sold, shown over time.

Use gigtool.gigs.list_gigs / get_gig to read gigs; don't write SQL here.
"""


def create_campaign_for_gig(gig, daily_budget_cents: int):
    raise NotImplementedError("Meta ads integration is planned for stage 2.")


def sync_campaign_results():
    raise NotImplementedError("Meta ads integration is planned for stage 2.")
