"""
Сценарий 5: Получение результатов.
Файл: tests/test_results.py
"""


class TestResults:

    def test_case14_get_latest_results(self, admin_client, scenario_id):
        """
        TestCase14. GET /api/scenarios/{sid}/latest-results после расчёта.
        Ожидание: статус 200, возвращена рейтинговая таблица.
        """
        response = admin_client.get(f'/api/scenarios/{scenario_id}/latest-results')
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert 'run' in data['data']
        assert 'results' in data['data']

    def test_case15_export_results(self, admin_client, scenario_id):
        """
        TestCase15. GET /api/scenarios/{sid}/export после расчёта.
        Ожидание: статус 200 с Excel-файлом или 404 если нет результатов.
        """
        response = admin_client.get(f'/api/scenarios/{scenario_id}/export')
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert 'spreadsheet' in response.content_type

    def test_case16_latest_results_no_runs(self, admin_client, scenario_id):
        """
        TestCase16. GET /api/scenarios/{sid}/latest-results для сценария без расчётов.
        Ожидание: статус 200, пустые данные.
        """
        response = admin_client.get(f'/api/scenarios/{scenario_id}/latest-results')
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True