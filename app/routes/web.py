# app/routes/web.py
from flask import Blueprint, render_template, abort
from app.auth import login_required, admin_required
from app.services.dataset_service import DatasetService
from app.services.scenario_service import ScenarioService
from app.services.run_service import RunService
from app.models import Carrier, Run

web_bp = Blueprint('web', __name__)
datasets = DatasetService()
scenarios = ScenarioService()
runs = RunService()


@web_bp.get('/')
@login_required
def index():
    return render_template('index.html',
                          scenarios=scenarios.list_all(),
                          datasets=datasets.list_datasets())


@web_bp.get('/datasets')
@login_required
def dataset_page():
    return render_template('datasets.html', datasets=datasets.list_datasets())


@web_bp.get('/scenarios/<int:sid>')
@admin_required
def scenario_page(sid):
    if sid == 0:
        scenario = type('obj', (object,), {
            'id': 0,
            'name': '',
            'description': '',
            'method': 'topsis'
        })()
    else:
        scenario = scenarios.get(sid)
    return render_template('scenario.html', scenario=scenario)


@web_bp.get('/results/<int:sid>')
@login_required
def results_page(sid):
    return render_template('results.html', scenario=scenarios.get(sid))


@web_bp.get('/runs/<int:rid>')
@login_required
def run_page(rid):
    return render_template('run.html', run=runs.get_run(rid))


@web_bp.get('/carriers')
@login_required
def carriers_page():
    carriers = Carrier.query.order_by(Carrier.company_name.asc()).all()
    return render_template('carriers.html', carriers=carriers)


@web_bp.app_errorhandler(403)
def forbidden(_):
    return render_template('403.html'), 403

@web_bp.get('/scenarios/<int:sid>/history')
@login_required
def scenario_history(sid):
    scenario = scenarios.get(sid)
    runs = Run.query.filter_by(scenario_id=sid).order_by(Run.id.desc()).all()
    return render_template('history.html', scenario=scenario, runs=runs)