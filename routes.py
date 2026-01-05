from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from extensions import limiter, cache
from models import db, ScriptHistory
from graph import build_graph
from forms import GenerateForm, SearchForm
import io
import threading

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/generate', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per minute")
def generate():
    if current_user.role != 'developer':
        flash('Access denied. Developers only.', 'danger')
        return redirect(url_for('main.home'))

    form = GenerateForm()
    if form.validate_on_submit():
        requirement = form.requirement.data.strip()
        browser = form.browser.data
        if not requirement:
            flash('Please enter a valid requirement.', 'danger')
            return redirect(url_for('main.generate'))

        try:
            # Run graph execution synchronously
            graph = build_graph()
            state = graph.invoke({"requirement": requirement, "browser": browser})

            playwright_script = state.get("playwright_script", "N/A")
            execution_result = state.get("execution_result", "No result.")
            analysis = state.get("analysis", "")
            test_stats_report = state.get("test_stats_report", "")

            # Save to history
            history = ScriptHistory(
                user_id=current_user.id,
                requirement=requirement,
                script=playwright_script,
                result=execution_result + ("\n\nAnalysis:\n" + analysis if analysis else "") + ("\n\nStats:\n" + test_stats_report if test_stats_report else "")
            )
            db.session.add(history)
            db.session.commit()

            return render_template('generate.html',
                                 form=form,
                                 playwright_script=playwright_script,
                                 execution_result=execution_result,
                                 analysis=analysis,
                                 test_stats_report=test_stats_report)
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('main.generate'))

    return render_template('generate.html', form=form)

@main.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    if current_user.role not in ['developer', 'qa']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    search_form = SearchForm()
    search_query = request.args.get('search', '')

    query = ScriptHistory.query
    if search_query:
        query = query.filter(
            db.or_(
                ScriptHistory.requirement.contains(search_query),
                ScriptHistory.script.contains(search_query),
                ScriptHistory.result.contains(search_query)
            )
        )

    scripts = query.order_by(ScriptHistory.timestamp.desc()).all()
    return render_template('history.html', scripts=scripts, search_form=search_form, search_query=search_query)

@main.route('/download/<int:script_id>')
@login_required
def download_script(script_id):
    if current_user.role not in ['developer', 'qa']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    script = ScriptHistory.query.get_or_404(script_id)

    # Create a file-like object from the script content
    script_io = io.BytesIO(script.script.encode('utf-8'))
    script_io.seek(0)

    return send_file(
        script_io,
        as_attachment=True,
        download_name=f'test_script_{script_id}.py',
        mimetype='text/x-python'
    )

@main.route('/rerun/<int:script_id>')
@login_required
@limiter.limit("5 per minute")
def rerun_script(script_id):
    if current_user.role not in ['developer', 'qa']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    script = ScriptHistory.query.get_or_404(script_id)

    try:
        graph = build_graph()
        state = graph.invoke({"requirement": script.requirement})

        new_playwright_script = state.get("playwright_script", "N/A")
        new_execution_result = state.get("execution_result", "No result.")
        new_analysis = state.get("analysis", "")

        # Save new run to history
        new_history = ScriptHistory(
            user_id=current_user.id,
            requirement=script.requirement,
            script=new_playwright_script,
            result=new_execution_result + ("\n\nAnalysis:\n" + new_analysis if new_analysis else "")
        )
        db.session.add(new_history)
        db.session.commit()

        flash('Script re-run completed successfully.', 'success')
    except Exception as e:
        flash(f'Re-run failed: {str(e)}', 'danger')

    return redirect(url_for('main.history'))
