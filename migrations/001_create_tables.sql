CREATE TABLE tenants (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name          text NOT NULL,
    api_key_hash  text NOT NULL UNIQUE,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE widgets (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    public_id       text NOT NULL UNIQUE,
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    type            text NOT NULL CHECK (type IN ('signup_form', 'contact_form')),
    title           text NOT NULL,
    description     text,
    fields          jsonb NOT NULL DEFAULT '[]',
    button_text     text NOT NULL,
    config_version  integer NOT NULL DEFAULT 1,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_widgets_tenant ON widgets (tenant_id);

CREATE TABLE submissions (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    widget_id        uuid NOT NULL REFERENCES widgets(id) ON DELETE CASCADE,
    tenant_id        uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    data             jsonb NOT NULL,
    ip_address       inet,
    country          text,
    city             text,
    geo_provider     text,
    idempotency_key  text,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_submissions_dashboard ON submissions (tenant_id, widget_id, created_at);
CREATE UNIQUE INDEX uq_submissions_idempotency ON submissions (widget_id, idempotency_key);