from nicegui import ui


APP_THEME_CSS = '''
    :root {
        --app-bg: #f4f7ff;
        --app-bg-soft: #eef7ff;
        --app-surface: #ffffff;
        --app-surface-muted: #f0f6ff;
        --app-border: #cfe0f5;
        --app-text: #172033;
        --app-muted: #607089;
        --app-primary: #2563eb;
        --app-primary-strong: #1d4ed8;
        --app-teal: #0f9f8f;
        --app-coral: #f9735b;
        --app-amber: #f59e0b;
        --app-violet: #8b5cf6;
        --app-pink: #ec4899;
        --app-green: #16a34a;
        --app-danger: #dc2626;
        --app-shadow: 0 14px 34px rgba(37, 99, 235, 0.10);
        --app-soft-shadow: 0 8px 20px rgba(31, 42, 55, 0.08);
        --app-accent-band: linear-gradient(135deg, #2563eb 0%, #0f9f8f 70%, #f59e0b 100%);
        --app-brand: linear-gradient(135deg, #2563eb 0%, #0f9f8f 100%);
        --app-happy: linear-gradient(135deg, #dbeafe 0%, #e0f7f4 58%, #fff7d6 100%);
    }

    body.body--dark {
        --app-bg: #08111f;
        --app-bg-soft: #101c31;
        --app-surface: #111c2e;
        --app-surface-muted: #18263d;
        --app-border: #29405f;
        --app-text: #f2f7ff;
        --app-muted: #b5c5dd;
        --app-primary: #60a5fa;
        --app-primary-strong: #93c5fd;
        --app-teal: #5eead4;
        --app-coral: #fb8b78;
        --app-amber: #fbbf24;
        --app-violet: #c4b5fd;
        --app-pink: #f9a8d4;
        --app-green: #86efac;
        --app-danger: #f87171;
        --app-shadow: 0 16px 36px rgba(0, 0, 0, 0.32);
        --app-soft-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
        --app-accent-band: linear-gradient(135deg, #60a5fa 0%, #5eead4 72%, #fbbf24 100%);
        --app-brand: linear-gradient(135deg, #60a5fa 0%, #5eead4 100%);
        --app-happy: linear-gradient(135deg, rgba(96, 165, 250, 0.20), rgba(94, 234, 212, 0.14), rgba(251, 191, 36, 0.10));
    }

    body, .q-layout, .q-page-container {
        background:
            linear-gradient(180deg, var(--app-bg-soft) 0%, var(--app-bg) 28rem),
            var(--app-bg) !important;
        color: var(--app-text) !important;
    }

    .app-header {
        background: color-mix(in srgb, var(--app-surface) 92%, transparent) !important;
        color: var(--app-text) !important;
        border-bottom: 1px solid var(--app-border);
        box-shadow: var(--app-soft-shadow) !important;
        backdrop-filter: blur(12px);
    }

    .app-drawer {
        background: var(--app-surface) !important;
        color: var(--app-text) !important;
        border-right: 1px solid var(--app-border);
    }

    .q-card, .nicegui-card, .app-card, .app-toolbar {
        background: var(--app-surface) !important;
        color: var(--app-text) !important;
        border: 1px solid var(--app-border);
        border-radius: 8px !important;
        box-shadow: var(--app-soft-shadow);
    }

    .app-card-colorful {
        background: var(--app-happy) !important;
        color: var(--app-text) !important;
        border: 1px solid var(--app-border);
        border-radius: 8px !important;
        box-shadow: var(--app-shadow);
    }

    .app-muted {
        color: var(--app-muted) !important;
    }

    .app-page-title {
        color: var(--app-text) !important;
        font-size: 2.15rem;
        line-height: 1.1;
        font-weight: 900;
    }

    .brand-badge, .emoji-badge {
        background: var(--app-brand);
        color: white !important;
        border-radius: 8px;
        box-shadow: var(--app-soft-shadow);
    }

    .emoji-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.5rem;
        height: 2.5rem;
        font-size: 1.35rem;
    }

    .menu-link {
        align-self: stretch;
        color: var(--app-text) !important;
        border-radius: 8px !important;
        cursor: pointer;
        display: flex !important;
        align-items: center;
        justify-content: flex-start !important;
        min-height: 2.55rem;
        padding: 0.35rem 0 !important;
        text-align: left !important;
        width: 100% !important;
        transition: background-color 160ms ease, color 160ms ease, transform 160ms ease;
    }

    .menu-link-icon {
        color: var(--app-primary) !important;
        display: inline-flex !important;
        flex: 0 0 1.75rem;
        font-size: 1.35rem !important;
        justify-content: center;
        width: 1.75rem;
    }

    .menu-link-text {
        color: var(--app-primary) !important;
        font-size: 0.9rem;
        font-weight: 800;
        line-height: 1.15;
        min-width: 0;
        overflow: hidden;
        text-align: left !important;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .menu-link:hover {
        background: var(--app-surface-muted) !important;
        color: var(--app-primary-strong) !important;
        transform: translateX(2px);
    }

    .q-field--outlined .q-field__control:before {
        border-color: var(--app-border) !important;
    }

    .q-field__native, .q-field__label, .q-field__marginal, .q-field__control {
        color: var(--app-text) !important;
    }

    .q-btn {
        border-radius: 8px !important;
        font-weight: 700;
    }

    .q-badge {
        border-radius: 8px !important;
        font-weight: 800;
    }

    .app-pill, .student-pill {
        background: color-mix(in srgb, var(--app-primary) 14%, transparent);
        color: var(--app-primary-strong) !important;
        border: 1px solid color-mix(in srgb, var(--app-primary) 24%, transparent);
        border-radius: 999px;
    }

    .tone-blue { color: var(--app-primary) !important; }
    .tone-teal { color: var(--app-teal) !important; }
    .tone-coral { color: var(--app-coral) !important; }
    .tone-amber { color: var(--app-amber) !important; }
    .tone-violet { color: var(--app-violet) !important; }
    .tone-pink { color: var(--app-pink) !important; }
    .tone-green { color: var(--app-green) !important; }

    .soft-blue { background: color-mix(in srgb, var(--app-primary) 14%, transparent) !important; }
    .soft-teal { background: color-mix(in srgb, var(--app-teal) 15%, transparent) !important; }
    .soft-coral { background: color-mix(in srgb, var(--app-coral) 16%, transparent) !important; }
    .soft-amber { background: color-mix(in srgb, var(--app-amber) 18%, transparent) !important; }
    .soft-violet { background: color-mix(in srgb, var(--app-violet) 16%, transparent) !important; }
    .soft-pink { background: color-mix(in srgb, var(--app-pink) 14%, transparent) !important; }
    .soft-green { background: color-mix(in srgb, var(--app-green) 14%, transparent) !important; }
'''


def add_app_theme() -> None:
    ui.add_css(APP_THEME_CSS)
    ui.colors(primary='#2563eb', secondary='#0f9f8f', accent='#8b5cf6', positive='#16a34a')
