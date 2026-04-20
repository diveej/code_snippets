"""Flask app for the admin portal.

Run:
    python -m game_content_system.web

Routes:
    GET  /                  -- list drafts / published / pick game type
    GET  /new               -- pick a game type
    GET  /new/<game_type>   -- blank edit form for a game type
    GET  /edit/<id>         -- edit form for existing content
    POST /edit/<id>         -- save / validate / publish (based on button)
"""

from flask import Flask, flash, redirect, render_template, request, url_for

from game_content_system import GameType, Status, registry
from game_content_system.core.validation import ValidationError
from game_content_system.web import forms as form_specs
from game_content_system.web.store import ContentStore


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "dev-only-not-for-prod"
    app.config["STORE"] = ContentStore()

    def _store() -> ContentStore:
        return app.config["STORE"]

    @app.route("/")
    def index():
        contents = _store().list()
        return render_template(
            "index.html",
            contents=contents,
            game_types=registry.list(),
            Status=Status,
        )

    @app.route("/new")
    def new_pick():
        return render_template("pick_type.html", game_types=registry.list())

    @app.route("/new/<game_type>")
    def new_draft(game_type: str):
        gt = GameType(game_type)
        spec = form_specs.spec_for(gt)
        draft = spec.defaults()
        _store().save(draft)
        return redirect(url_for("edit", content_id=draft.id))

    @app.route("/edit/<content_id>", methods=["GET", "POST"])
    def edit(content_id: str):
        draft = _store().get(content_id)
        if draft is None:
            flash("Content not found", "error")
            return redirect(url_for("index"))

        spec = form_specs.spec_for(draft.game_type)
        errors: list = []
        warnings: list = []

        if request.method == "POST":
            action = request.form.get("action", "save")
            try:
                spec.apply(draft, request.form)
            except (ValueError, KeyError) as e:
                errors.append(f"Form parse error: {e}")

            if not errors:
                result = draft.validate()
                errors = list(result.errors)
                warnings = list(result.warnings)

                if action == "publish":
                    try:
                        registry.publish(draft)
                        flash("Published", "success")
                        return redirect(url_for("index"))
                    except ValidationError:
                        flash("Fix validation errors before publishing", "error")
                elif action == "validate":
                    flash("Validation run — see results below", "info")
                else:
                    _store().save(draft)
                    flash("Draft saved", "success")

            _store().save(draft)

            # Re-render with the submitted values so admin sees what they typed.
            values = {k: request.form.get(k, "") for k in request.form}
            return render_template(
                "edit.html",
                draft=draft,
                spec=spec,
                values=values,
                errors=errors,
                warnings=warnings,
                Status=Status,
            )

        values = form_specs.form_values_for(draft)
        # Include sensible defaults for any JSON fields that don't have a
        # real value yet (fresh drafts).
        for jf in spec.json_fields:
            values.setdefault(jf.name, "")
        return render_template(
            "edit.html",
            draft=draft,
            spec=spec,
            values=values,
            errors=errors,
            warnings=warnings,
            Status=Status,
        )

    @app.route("/delete/<content_id>", methods=["POST"])
    def delete(content_id: str):
        _store().delete(content_id)
        flash("Deleted", "info")
        return redirect(url_for("index"))

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=5050, debug=False)


if __name__ == "__main__":
    main()
