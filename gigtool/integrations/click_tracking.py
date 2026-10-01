"""Ticket-link click tracking. NOT BUILT YET: this is the plan.

Every gig has a permanent ID (gigs.id). A tracked link will look like
    https://<her website>/tickets/<gig id>?src=<ad id>
The website logs the click (time, gig, which ad sent it), then redirects
to the gig's ticket page: Gig.effective_ticket_url, which is your override
if you've set one, otherwise the Bandsintown link.

Clicks will go in a new `link_clicks` table (added via db.MIGRATIONS), so
the dashboard can show clicks per gig and, with Meta spend, cost per click.
"""


def tracked_link_for(gig, ad_id: str | None = None) -> str:
    raise NotImplementedError("Click tracking is planned for a later stage.")
