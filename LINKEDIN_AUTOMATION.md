# EazyDataFix daily LinkedIn publisher

This workflow publishes one **curated text post** per India-local day from the
personal LinkedIn account authorized through a LinkedIn developer application.
The first 14 captions are in `linkedin_posts.json` and are grounded in the
repository's README. Edit or append captions there before the queue runs out;
used IDs must never be reused. No AI service or API key is required to write posts.

## Schedule and controls

- GitHub Actions runs at **9:17 AM Asia/Kolkata**, daily. GitHub may delay or
  drop an individual scheduled run; the workflow records at most one post per
  local day, but cannot guarantee that every day has a post.
- The workflow is dormant until repository variable `LINKEDIN_ENABLED` is
  exactly `true`. Keep it unset during setup.
- `workflow_dispatch` with `publish=false` previews the next caption without
  credentials or network writes. Setting `publish=true` publishes the next post.
- `linkedin_published.json` records each reservation and the returned post ID.
  The workflow commits a reservation before contacting LinkedIn. If a request
  fails or the response is uncertain, the reservation stays in place and later
  runs stop. Check the LinkedIn activity page and reconcile the ledger manually
  before resuming. Never blindly rerun the publish step.
- GitHub Actions needs permission to write repository contents. Branch rules
  must permit its ledger commits to the default branch.

## LinkedIn setup

1. Create a LinkedIn developer application tied to the intended account and
   add **Share on LinkedIn**, which grants `w_member_social`.
2. Complete LinkedIn's member OAuth authorization code flow with that scope.
   Store the resulting access token in the repository Actions secret
   `LINKEDIN_ACCESS_TOKEN`; do not commit or paste it into an issue or chat.
3. Determine the authenticated member's Person URN, for example via LinkedIn
   OpenID Connect `userinfo` with the appropriate sign-in permission. Store
   `urn:li:person:<member-id>` as repository Actions secret
   `LINKEDIN_PERSON_URN`. It must match the member who authorized the token.
4. Preview the workflow manually, confirm the caption and identity, then set
   repository Actions variable `LINKEDIN_ENABLED=true`. A manual publish run
   can validate the first live post before the daily schedule starts.

LinkedIn's normal access tokens expire after about 60 days. Programmatic
refresh tokens are available to approved Marketing Developer Platform partners;
otherwise reauthorize and replace the secret before expiry. A failed action
should be reviewed promptly. Do not place client secrets or refresh tokens in
the repository.

## Editorial rules

Captions should be useful, specific, and verifiable against current EazyDataFix
behavior. Do not imply that ML Ready trains a model or that Power BI Ready
creates dashboards. Add new captions with unique stable IDs and run
`python linkedin_publisher.py preview` to inspect the next one. The queue
intentionally stops when empty instead of recycling old posts.

Official references:

- LinkedIn Share on LinkedIn: https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin
- LinkedIn API access: https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- LinkedIn refresh tokens: https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens
- GitHub scheduled workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
