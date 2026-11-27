"""Gold mart grains and exact output schemas for the Direct Lake semantic model."""
METRICS = '''trip_count BIGINT, revenue_trip_count BIGINT, known_revenue_usd DECIMAL(28,2),
distance_trip_count BIGINT, total_km DECIMAL(28,6), revenue_coverage DOUBLE, distance_coverage DOUBLE'''
SCHEMAS = {
    'mart_daily_summary': 'trip_date DATE, ' + METRICS + ', gold_load_id STRING',
    'mart_area_demand_daily': 'trip_date DATE, area_role STRING, area_key INT, area_id INT, is_unknown BOOLEAN, '
                              + METRICS + ', gold_load_id STRING',
    'mart_company_payment_daily': 'trip_date DATE, company_key STRING, company_name STRING, payment_type_key STRING, '
                                  'payment_type STRING, ' + METRICS + ', gold_load_id STRING',
}
KEYS = {
    'mart_daily_summary': ['trip_date'],
    'mart_area_demand_daily': ['trip_date', 'area_role', 'area_key'],
    'mart_company_payment_daily': ['trip_date', 'company_key', 'payment_type_key'],
}
