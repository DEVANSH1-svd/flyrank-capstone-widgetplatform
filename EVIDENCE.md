# Evidence

One proof per requirement. Each section shows real command output.

## Widget management: authenticated CRUD, unauthenticated requests rejected

    1. No key (expect 401):            401
    2. Wrong key (expect 401):         401
    3. Invalid body (expect 422):      422
    4. A creates widget (expect 201):  id f4d4d5c2-8f25-4dec-9767-81f443d22609, public_id pfpCt6ZOKX4P
    5. A reads it (expect 200):        200

## Multi-tenant isolation: tenant B cannot touch tenant A's widget

    6. B reads A's widget (expect 404):    404
    7. B updates A's widget (expect 404):  404
    8. B deletes A's widget (expect 404):  404
    9. B lists widgets (expect []):        []

Wrong-tenant access returns 404, not 403, so a widget's existence is not revealed.

## Embed snippet generated per widget

    {"snippet":"<script src=\"http://127.0.0.1:8000/static/widget.v1.js\" data-widget-id=\"pfpCt6ZOKX4P\"></script>"}
## Public submission API: CORS, preflight, validation, size limit, honeypot, idempotency

    1. Valid cross-origin POST:   HTTP/1.1 201 Created, access-control-allow-origin: *
    2. Preflight OPTIONS:         HTTP/1.1 200 OK, access-control-allow-methods: GET, POST,
                                  access-control-allow-headers: ... Content-Type
    3. Replay same idempotency key: 200, same id as test 1 (no second row)
    4. Malformed JSON:            422 {"detail":[{"type":"json_invalid",...}]}
    5. Missing required field:    422 {"detail":[{"field":"email","msg":"This field is required"}]}
    6. Unknown field:             422 {"detail":[{"field":"evil","msg":"Unknown field"}]}
    7. Invalid email:             422 {"detail":[{"field":"email","msg":"Invalid email address"}]}
    8. Unknown widget:            404 {"detail":"Widget not found"}
    9. Oversized payload (20 KB): 413 {"detail":"Payload too large"}
   10. Honeypot filled:           201 (fake id), nothing stored

    Rows in database after all ten requests: exactly 1 (the valid one, idempotency_key key-001)

Preflight returns 200 (Starlette's CORS middleware), not the 204 in the design doc; both are valid.
## Abuse protection, enrichment and safe side effects (pytest, 13 passed)

    tests/test_submissions.py::test_valid_cross_origin_submission_is_stored PASSED
    tests/test_submissions.py::test_preflight_is_answered PASSED
    tests/test_submissions.py::test_repeated_idempotency_key_stores_once PASSED
    tests/test_submissions.py::test_malformed_json_is_422 PASSED
    tests/test_submissions.py::test_invalid_email_is_422 PASSED
    tests/test_submissions.py::test_oversized_payload_is_413 PASSED
    tests/test_submissions.py::test_burst_gets_429_then_service_recovers PASSED
    tests/test_submissions.py::test_per_widget_limit PASSED
    tests/test_submissions.py::test_provider_a_answers PASSED
    tests/test_submissions.py::test_provider_b_answers_when_a_is_down PASSED
    tests/test_submissions.py::test_all_providers_down_still_stores PASSED
    tests/test_submissions.py::test_email_failure_does_not_break_submission PASSED
    tests/test_submissions.py::test_honeypot_is_dropped_silently PASSED
    13 passed in 3.77s

Mapping to requirements:
- Rate limiting returns 429 under a burst and the service keeps serving others: test_burst_gets_429_then_service_recovers, test_per_widget_limit
- Spam control blocks a bot: test_honeypot_is_dropped_silently
- Provider A down, provider B answers: test_provider_b_answers_when_a_is_down
- All providers down, submission still stored: test_all_providers_down_still_stores
- Failing email does not block the submission: test_email_failure_does_not_break_submission
## Widget delivery: cached config and versioned bundle (pytest, 19 passed in total)

    tests/test_delivery_dashboard.py::test_script_is_served_with_long_immutable_cache PASSED
        Cache-Control: public, max-age=31536000, immutable on /static/widget.v1.js
    tests/test_delivery_dashboard.py::test_only_versioned_scripts_are_served PASSED
        /static/widget.js and path-traversal attempts return 404
    tests/test_delivery_dashboard.py::test_config_is_cached_briefly_and_supports_etag PASSED
        Cache-Control: max-age=60, ETag, 304 on If-None-Match, CORS header present, no tenant_id leaked
    tests/test_delivery_dashboard.py::test_config_for_unknown_widget_is_404 PASSED

## Owner dashboard: authenticated, own data only, basic analytics

    tests/test_delivery_dashboard.py::test_dashboard_requires_api_key PASSED
    tests/test_delivery_dashboard.py::test_dashboard_shows_own_submissions_and_stats_only PASSED
        Tenant A sees its 2 submissions and stats (total, per widget, per country); tenant B sees none.

    19 passed in 5.19s
## Widget renders on a page served from a different origin (probe 1)

The customer site (test-site/index.html) is served by `python -m http.server 5500`; the API runs on port 8000, so these are two different origins. The page loads the one-line embed (widget.v1.js with data-widget-id), the script fetches the widget config, renders the form, and submits. The page showed "Thank you! We received your submission."

The submission then appeared in the owner dashboard, authenticated with the tenant's API key (email replaced with a placeholder here):

    GET /dashboard/submissions
    [{"id":"4f854bfe-c2be-40ce-8a5a-adbcb9a54776","widget_id":"cbe83d67-e863-4a06-95b1-39bc92b5bd9d","data":{"name":"DEVANSH","email":"visitor@example.com"},"country":null,"city":null,"geo_provider":null,"created_at":"2026-10-22T06:35:50.763692Z"}]

    GET /dashboard/stats
    {"days":30,"total":1,"per_widget":[{"widget_id":"cbe83d67-e863-4a06-95b1-39bc92b5bd9d","title":"Join the Acme newsletter","count":1}],"per_day":[{"day":"2026-10-22","count":1}],"per_country":[{"country":"Unknown","count":1}]}

Country is Unknown because 127.0.0.1 cannot be geolocated; the geo fallback chain itself is proven by the pytest cases above.