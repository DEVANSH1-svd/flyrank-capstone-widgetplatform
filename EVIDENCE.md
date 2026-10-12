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