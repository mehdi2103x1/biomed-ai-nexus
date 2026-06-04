"""
Page modules for BioMed AI Nexus.

Each module exposes a single ``render(ctx)`` function. ``app.py`` builds a small
``ctx`` dict (model manager, dataset, theme flag) and routes the sidebar choice
to the matching ``render``. This keeps a single, fully-styled sidebar while
still satisfying the required ``pages/`` package layout.
"""
