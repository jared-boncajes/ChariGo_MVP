# ChariGo Figma audit and implementation map

Source: uploaded `CHARIGO_High Fidelity (1).fig`, exported October 31, 2026. Decoded its complete Kiwi schema and 1,109 nodes, inspected all 25 application frames, 8 component/legend boards, 2 standalone cards and 40 symbols (including nested variants). `figma-inventory.json` preserves the actual frame names, IDs and text. The supplied updated specification in `specification.md` governs functionality.

## Visual system

Inter; primary #F77492, primary-soft #FEB5C6, success #03541C, black text, muted #535353, gray #D9D9D9, white surface. 8-point spacing with 4px details. H1 28/34 bold, H2 20/24 bold, section 16/20 semibold, body 14/20, caption 11/16. Pink outlined white cards, soft pink summary panels, pill buttons, circular initials and icons. Goer navigation: home, explore, profile; organization: home/current fundraisers, create, profile. Retain bottom navigation at all sizes, with centered width; wider content and card grids provide responsive adaptation without a new information architecture.

## Application frames

Each row maps the original frame to its implementation. Missing states in the final column are added in the same design language.

| Frame ID / original name | Role | Route | Actions and destination | Models | States / additional UI |
|---|---|---|---|---|---|
| 1:5 Welcome | Guest | / | Sign up → choose role; log in | — | Responsive photo collage; exact original assets |
| 47:39 Log In | All | /login | Authenticate → role home | User | Invalid/inactive login, visible labels; email login only |
| 48:90 Sign Up | Guest | /register | Create account → role home/profile | User, Organization, SystemRecord | Duplicate email, password mismatch; public admin signup forbidden |
| 59:5 Choose ChariGo Usage | Guest | /register/role | Choose goer or organization → register | User | Accessible radio cards |
| 59:6 Home Page | Goer/guest | /home | Search → causes, featured foundation → organization, fundraiser → details | Fundraiser, Organization | Search results and no active campaigns |
| 59:8 Search | Goer/guest | /causes | Search, category/organization/volunteer filters → detail | Fundraiser, Organization, VolunteerOpportunity | No results/reset; all public organizations are verified |
| 98:492 Organization Information | All | /organizations/id | About, campaigns, contact tabs; save charity; donate → campaign | Organization, Fundraiser, SavedCharity | No campaigns, no contact supplied |
| 98:531 Charity Information | All | /fundraisers/id | Donate → donation; volunteer → opportunity | Fundraiser, Donation, Organization | Completed/unavailable/moderated state |
| 98:559 Donation Payment | Goer | /fundraisers/id/donate | Amount, method, anonymous → review | Donation, Fundraiser | Simulated one-time payment only; no card data; custom amount validation |
| 59:14 Donation Confirmation | Goer | /donations/id | Real persisted receipt, home/history navigation | Donation | Added pre-submit /donation/review; replay protection |
| 59:16 Volunteering Details | Goer | /opportunities/id | Details, message → review → submit | VolunteerOpportunity, VolunteerApplication | Capacity, duplicate, closed states; profile info |
| 140:504 Volunteer Verification | Goer | /applications/id/success | Application saved → history/home | VolunteerApplication | Pending status; no claim of email delivery |
| 59:15 Volunteer Profile Page | Goer | /profile | Impact, saved charities, histories, edit | User, Donation, VolunteerApplication, SavedCharity | Real counts; added /profile/edit |
| 147:260 Donation History | Goer | /history/donations | Receipt/details, browse | Donation | Empty history |
| 147:277 Volunteer History | Goer | /history/volunteering | Pending/accepted/rejected and completed event history | VolunteerApplication | Empty history; dynamic statuses |
| 148:382 Organization Registration | Organization | /organization/profile | Logo, official details, portfolio → submit | Organization | Replace Figma field-label placeholders with meaningful labels; private PDF portfolio |
| 148:423 Volunteer Verification (registration sent) | Organization | /organization | View submitted status/profile | Organization | Confirmation flash and pending panel |
| 148:438 Volunteer Verification (please wait) | Organization | /organization | Check verification; edit profile | Organization | Pending/rejected/inactive; in-app status instead of unconfigured email |
| 151:472 Organizer Profile | Organization | /organization | Overview, management, create, edit info | Organization, Fundraiser, Donation, VolunteerApplication | Verification gating, real statistics |
| 151:511 Create Fundraiser | Verified organization | /organization/fundraisers/new | Image, details, dates, volunteer listing → create | Fundraiser, VolunteerOpportunity | Real labeled fields; invalid goals/dates/uploads |
| 151:530 Current Fundraisers | Organization | /organization/fundraisers | Open/manage fundraiser | Fundraiser | Active/past tabs and empty states |
| 152:796 Manage Fundraiser | Owner | /organization/fundraisers/id | Edit, complete, deactivate, volunteer requests | Fundraiser, Donation, VolunteerOpportunity | Confirmation before soft deletion; preserve history |
| 152:832 Volunteer Requests | Owner | /organization/fundraisers/id/applications | Filter status, open applicant | VolunteerApplication | No pending applications |
| 154:1229 Volunteer Applicant Profile | Owner | /organization/applications/id | Review personal info, skills, prior activity, accept/reject | User, VolunteerApplication | Confirm decision; accepted capacity check; private owner-only access |
| 155:1488 Past Fundraisers | Organization | /organization/fundraisers?status=past | History → manage/details | Fundraiser | Completed/expired/deactivated records |

## Components and alternate states

- 111:111 Component 1: default/home/search/profile bottom navigation variants. Same routes with active indication.
- 111:265 Component 2: one-time/monthly payment toggle. One-time implemented; recurring billing explicitly excluded because payments are simulated. No inert recurring control.
- 111:291 Donation Amount Grid: all six amount selection variants; native radio choices and custom input.
- 144:120 Group 9: three goer/organization role selection variants; keyboard accessible radio cards.
- 151:700 Group 11: organization bottom navigation variants; current/create/profile.
- 153:1204 Volunteer Request 1: pending/accepted card states; also add rejected and empty states.
- 151:628 Group 12: fundraiser card; live progress and original cover.
- 155:1550 Past Fundraiser 1: closed fundraiser/progress/view action; live historical data.
- 166:402 Legend/Button and 166:403 ChariGo Design Legend: default/hover/disabled/focus styles and exact typography/color tokens applied globally.
- Nested history cards, registration fields, text areas, action rows and circular back buttons reused rather than separate routes. Internal-only canvas holds supporting metadata, not extra user screens.

No meaningful application frame is excluded. Google/Facebook OAuth, phone-number login, automated email/password-reset delivery and recurring/real payments are outside this local demo MVP and explicitly documented, rather than exposing fake controls. Organization portfolios support safely served PDF files, plus a text portfolio; legacy DOC/DOCX is excluded to avoid unvalidated executable document content. No identity documents are requested.

## Missing required screens

Administrator has no original Figma screens. Add /admin (summary), /admin/users (search/role/status), /admin/users/id (detail and confirmed deactivate/reactivate), /admin/organizations (search/status), /admin/organizations/id (registration review, approve/reject/deactivate/reactivate), /admin/opportunities (fundraisers and volunteer opportunities with search/type/status), /admin/opportunities/type/id (detail, confirmed status action), and /admin/records (searchable audit trail). Reuse soft pink stats, outlined lists, pills and top section tabs; no generic sidebar. Also add profile editing, donation and volunteer review, permission/not-found errors, confirmations and empty states.

## Schema finalized before feature implementation

- User: name, unique normalized email, password hash, role, account_status; phone/location/availability/skills/experience, avatar, timestamps.
- Organization: unique owner → User, name/about/mission/contact/location/portfolio text/private portfolio file/logo, verification_status, rejection_reason, registered_at.
- Fundraiser: owner → Organization, title/description/impact/category/location/cover, integer goal centavos, start/end dates, status and separate moderation_status. Raised amount is derived from persisted Donation rows to avoid inconsistent totals.
- Donation: user → User, fundraiser → Fundraiser, integer amount centavos, simulated method, anonymity, timestamp, unique submission token. Receipt and progress use the same row.
- VolunteerOpportunity: unique fundraiser → Fundraiser, title/description/requirements/slots/event date/location/status. One editable opportunity per campaign suffices for this MVP.
- VolunteerApplication: user → User, opportunity → VolunteerOpportunity, message/status/timestamps; unique (user, opportunity).
- SavedCharity: unique (user, organization) for the profile's saved charities.
- SystemRecord: actor → User, action, target type/id, plain description/reason and timestamp. No passwords or payment credentials.

Statuses: users active/inactive; organizations pending/verified/rejected/inactive; campaigns active/completed/inactive (owner) and active/inactive/removed (moderation); opportunities active/inactive/removed; applications pending/accepted/rejected. Expired campaigns are treated as closed. Administrative reactivation never overrides campaign completion or an owner's deactivation. Every request rechecks account, organization and ownership permissions. CSRF, integer money, safe uploads, SQLite foreign keys and transaction rollback protect writes.

Implementation sequence: foundation/auth → goer donation/volunteer/history → organization campaign/applicant management → admin review/moderation/audit → automated workflow/security tests → browser interactions and eight responsive widths.
