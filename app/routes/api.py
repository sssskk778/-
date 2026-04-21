# app/routes/api.py
import csv
import io
import json
from flask import Blueprint, jsonify, request, make_response
from app import db
from app.auth import login_required, admin_required, current_user
from app.models import Criterion, Carrier, RunResult, Dataset, ScenarioCriterion, Run, Scenario
from app.services.dataset_service import DatasetService
from app.services.scenario_service import ScenarioService
from app.services.run_service import RunService
from app.services.swara import SwaraService

api_bp = Blueprint('api', __name__, url_prefix='/api')
datasets = DatasetService()
scenarios = ScenarioService()
runs = RunService()


@api_bp.get('/auth/me')
@login_required
def me():
    u = current_user()
    return jsonify({
        'id': u.id,
        'username': u.username,
        'full_name': u.full_name,
        'role': u.role
    })


@api_bp.get('/datasets')
@login_required
def dataset_list():
    rows = datasets.list_datasets()
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'records_count': d.records_count,
        'created_at': d.created_at.isoformat() if d.created_at else None
    } for d in rows])


@api_bp.post('/datasets/upload')
@admin_required
def upload_dataset():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не передан.'}), 400
    file = request.files['file']
    name = request.form.get('name') or file.filename
    description = request.form.get('description') or ''
    ds = datasets.import_csv(file, name=name, description=description)
    return jsonify({
        'id': ds.id,
        'name': ds.name,
        'records_count': ds.records_count
    })


@api_bp.delete('/datasets/<int:did>')
@admin_required
def delete_dataset(did):
    try:
        datasets.delete_dataset(did)
        return jsonify({'status': 'ok', 'message': 'Dataset deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_bp.get('/criteria')
@login_required
def criteria():
    rows = Criterion.query.order_by(Criterion.order_no.asc()).all()
    return jsonify([{
        'id': c.id,
        'code': c.code,
        'name': c.name,
        'kind': c.kind
    } for c in rows])


@api_bp.get('/carriers')
@login_required
def carriers():
    rows = Carrier.query.order_by(Carrier.name.asc()).all()
    out = []
    for r in rows:
        out.append({
            'id': r.carrier_id,
            'carrier_id': r.carrier_id,
            'name': r.name,
            'inn': r.inn,
            'region': r.region,
            'fleet_type': r.fleet_type
        })
    return jsonify(out)


@api_bp.get('/scenarios')
@login_required
def scenario_list():
    rows = scenarios.list_all()
    out = []
    for s in rows:
        selected = ScenarioCriterion.query.filter_by(scenario_id=s.id).order_by(ScenarioCriterion.order_no.asc()).all()
        criteria = [Criterion.query.get(x.criterion_id) for x in selected]
        out.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'method': s.method,
            'status': s.status,
            'weight_mode': s.weight_mode,
            'criterion_ids': [c.id for c in criteria if c],
            'criteria': [{'id': c.id, 'code': c.code, 'name': c.name, 'kind': c.kind} for c in criteria if c]
        })
    return jsonify(out)


@api_bp.get('/scenarios/<int:sid>')
@login_required
def scenario_get(sid):
    s = scenarios.get(sid)
    selected = ScenarioCriterion.query.filter_by(scenario_id=s.id).order_by(ScenarioCriterion.order_no.asc()).all()
    criteria = [Criterion.query.get(x.criterion_id) for x in selected]
    return jsonify({
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'method': s.method,
        'status': s.status,
        'weight_mode': s.weight_mode,
        'criterion_ids': [c.id for c in criteria if c],
        'criteria': [{'id': c.id, 'code': c.code, 'name': c.name, 'kind': c.kind, 'is_enabled': True} for c in criteria if c]
    })


@api_bp.post('/scenarios')
@admin_required
def scenario_create():
    payload = request.get_json(force=True)
    s = scenarios.create(payload, current_user().id)
    return jsonify({'id': s.id, 'name': s.name}), 201


@api_bp.put('/scenarios/<int:sid>')
@admin_required
def scenario_update(sid):
    payload = request.get_json(force=True)
    s = scenarios.update(sid, payload)
    return jsonify({'id': s.id, 'name': s.name})


@api_bp.delete('/scenarios/<int:sid>')
@admin_required
def scenario_delete(sid):
    scenarios.delete(sid)
    return jsonify({'status': 'deleted'})


# =============================================================================
# SWARA WEIGHTS
# =============================================================================

@api_bp.put('/scenarios/<int:sid>/weights/swara')
@admin_required
def scenario_set_swara_weights(sid):
    """Сохраняет настройки SWARA для сценария."""
    payload = request.get_json(force=True)
    ranking = payload.get('ranking', [])
    s_values = payload.get('s_values', [])

    if not ranking or not s_values:
        return jsonify({'error': 'ranking и s_values обязательны'}), 400

    if len(s_values) != len(ranking) - 1:
        return jsonify({'error': f'Ожидается {len(ranking) - 1} значений s_values'}), 400

    if not SwaraService.validate_s_values(s_values):
        return jsonify({'error': 's_values должны быть >= 0'}), 400

    scenario = Scenario.query.get_or_404(sid)
    scenario.weight_mode = 'swara'
    scenario.set_swara_config(ranking, s_values)
    db.session.commit()

    weights = SwaraService.compute(ranking, s_values)
    return jsonify({
        'id': scenario.id,
        'weight_mode': scenario.weight_mode,
        'swara_config': scenario.get_swara_config(),
        'weights': weights
    })


@api_bp.get('/scenarios/<int:sid>/weights/swara')
@login_required
def scenario_get_swara_weights(sid):
    """Возвращает настройки SWARA для сценария."""
    scenario = Scenario.query.get_or_404(sid)
    config = scenario.get_swara_config()

    if not config:
        return jsonify({'ranking': [], 's_values': [], 'weights': {}})

    weights = SwaraService.compute(config['ranking'], config['s_values'])
    return jsonify({
        'ranking': config['ranking'],
        's_values': config['s_values'],
        'weights': weights
    })


@api_bp.post('/scenarios/<int:sid>/weights/swara/preview')
@login_required
def scenario_preview_swara_weights(sid):
    """Предварительный расчёт весов SWARA (без сохранения)."""
    payload = request.get_json(force=True)
    ranking = payload.get('ranking', [])
    s_values = payload.get('s_values', [])

    if not ranking or not s_values:
        return jsonify({'error': 'ranking и s_values обязательны'}), 400

    if len(s_values) != len(ranking) - 1:
        return jsonify({'error': f'Ожидается {len(ranking) - 1} значений s_values'}), 400

    weights = SwaraService.preview_weights(ranking, s_values)
    return jsonify({'weights': weights})


# =============================================================================
# RUNS
# =============================================================================

@api_bp.post('/scenarios/<int:sid>/run')
@admin_required
def scenario_run(sid):
    run = runs.execute(sid, current_user().id)
    return jsonify({'run_id': run.id, 'status': run.status}), 201


@api_bp.get('/scenarios/<int:sid>/runs')
@login_required
def scenario_runs(sid):
    rows = Run.query.filter_by(scenario_id=sid).order_by(Run.id.desc()).all()
    return jsonify([{
        'id': r.id,
        'status': r.status,
        'started_at': r.started_at.isoformat() if r.started_at else None,
        'finished_at': r.finished_at.isoformat() if r.finished_at else None
    } for r in rows])


@api_bp.get('/scenarios/<int:sid>/latest-results')
@login_required
def latest_results(sid):
    run, results = runs.latest_results(sid)
    if not run:
        return jsonify({'run': None, 'results': [], 'meta': None})
    meta = json.loads(run.meta_json or '{}')
    out = []
    for r in results:
        out.append({
            'id': r.id,
            'rank': r.rank,
            'score': r.score,
            'company_name': r.company_name,
            'carrier_id': r.carrier_id,
            'details': json.loads(r.details_json or '{}')
        })
    return jsonify({'run': {'id': run.id, 'status': run.status}, 'results': out, 'meta': meta})


@api_bp.get('/runs/<int:rid>')
@login_required
def run_detail(rid):
    run = runs.get_run(rid)
    results = RunResult.query.filter_by(run_id=run.id).order_by(RunResult.rank.asc()).all()
    return jsonify({
        'run': {'id': run.id, 'status': run.status},
        'meta': json.loads(run.meta_json or '{}'),
        'results': [{
            'company_name': r.company_name,
            'rank': r.rank,
            'score': r.score,
            'details': json.loads(r.details_json or '{}')
        } for r in results]
    })


@api_bp.get('/scenarios/<int:sid>/export')
@login_required
def export_csv(sid):
    run, results = runs.latest_results(sid)
    if not run:
        return jsonify({'error': 'Нет результатов'}), 404
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['rank', 'company_name', 'score'])
    for r in results:
        writer.writerow([r.rank, r.company_name, r.score])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=scenario_{sid}_results.csv'
    return response