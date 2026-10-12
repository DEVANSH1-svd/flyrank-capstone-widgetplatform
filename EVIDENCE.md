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