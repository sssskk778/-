# app/routes/web.py
import logging
from flask import Blueprint, render_template, abort
from app.auth import login_required, admin_required
from app.services.data.dataset_service import DatasetService
from app.services.core.scenario_service import ScenarioService
from app.services.core.run_service import RunService
from app.models import Carrier, Run

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)
datasets = DatasetService()
scenarios = ScenarioService()
runs = RunService()


@web_bp.get('/')
@login_required
def index():
    try:
        return render_template('index.html',
                               scenarios=scenarios.list_all(),
                               datasets=datasets.list_datasets())
    except Exception:
        logger.exception('Ошибка на главной странице')
        abort(500)


@web_bp.get('/datasets')
@login_required
def dataset_page():
    try:
        return render_template('datasets.html', datasets=datasets.list_datasets())
    except Exception:
        logger.exception('Ошибка на странице датасетов')
        abort(500)


@web_bp.get('/scenarios/<int:sid>')
@admin_required
def scenario_page(sid):
    try:
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
    except Exception:
        logger.exception('Ошибка на странице сценария sid=%s', sid)
        abort(500)


@web_bp.get('/results/<int:sid>')
@login_required
def results_page(sid):
    try:
        return render_template('results.html', scenario=scenarios.get(sid))
    except Exception:
        logger.exception('Ошибка на странице результатов sid=%s', sid)
        abort(500)


@web_bp.get('/runs/<int:rid>')
@login_required
def run_page(rid):
    try:
        return render_template('run.html', run=runs.get_run(rid))
    except Exception:
        logger.exception('Ошибка на странице запуска rid=%s', rid)
        abort(500)


@web_bp.get('/carriers')
@login_required
def carriers_page():
    try:
        carriers = Carrier.query.order_by(Carrier.company_name.asc()).all()
        return render_template('carriers.html', carriers=carriers)
    except Exception:
        logger.exception('Ошибка на странице перевозчиков')
        abort(500)


@web_bp.get('/scenarios/<int:sid>/history')
@login_required
def scenario_history(sid):
    try:
        scenario = scenarios.get(sid)
        run_list = Run.query.filter_by(scenario_id=sid).order_by(Run.id.desc()).all()
        return render_template('history.html', scenario=scenario, runs=run_list)
    except Exception:
        logger.exception('Ошибка на странице истории sid=%s', sid)
        abort(500)


@web_bp.app_errorhandler(403)
def forbidden(_):
    return render_template('403.html'), 403