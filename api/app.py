from flask import Flask, request, jsonify
from flask_cors import CORS
from clickhouse_driver import Client

app = Flask(__name__)
CORS(app)

# Подключение к ClickHouse
client = Client(host='clickhouse', port=9000, user='clickhouse', password='clickpass')

@app.route('/get_products', methods=['GET'])
def get_products():
    try:
        query = "SELECT DISTINCT toString(product_id) FROM fact_sales"
        result = client.execute(query)
        products = [row[0] for row in result]
        return jsonify(products)
    except Exception as e:
        app.logger.error(f"Error in get_products: {str(e)}")
        return jsonify({"error": f"Failed to fetch products: {str(e)}"}), 500

@app.route('/get_date_range', methods=['GET'])
def get_date_range():
    try:
        query = "SELECT min(sale_date), max(sale_date) FROM fact_sales"
        result = client.execute(query)
        if not result:
            return jsonify({"min_date": "2023-01-01", "max_date": "2023-12-31"})
        min_date, max_date = result[0]
        return jsonify({"min_date": str(min_date), "max_date": str(max_date)})
    except Exception as e:
        app.logger.error(f"Error in get_date_range: {str(e)}")
        return jsonify({"error": f"Failed to fetch date range: {str(e)}"}), 500

@app.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        query = "SELECT DISTINCT category FROM dim_products"
        result = client.execute(query)
        categories = [row[0] for row in result]
        return jsonify(categories)
    except Exception as e:
        app.logger.error(f"Error in get_categories: {str(e)}")
        return jsonify({"error": f"Failed to fetch categories: {str(e)}"}), 500

@app.route('/get_aggregate', methods=['GET'])
def get_aggregate():
    product_id = request.args.get('product_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    aggregate_type = request.args.get('aggregate_type')
    group_by = request.args.get('group_by')

    if not all([product_id, start_date, end_date, aggregate_type, group_by]):
        return jsonify({"error": "Missing parameters"}), 400

    # Маппинг русских строк на английские
    group_by_map = {
        'день': 'day',
        'неделя': 'week',
        'месяц': 'month',
        'day': 'day',
        'week': 'week',
        'month': 'month'
    }
    group_by = group_by_map.get(group_by.lower(), None)
    if not group_by:
        return jsonify({"error": "Invalid group_by parameter. Use 'day', 'week', 'month', 'день', 'неделя', or 'месяц'"}), 400

    if group_by == 'day':
        group_field = 'toDate(sale_date)'
    elif group_by == 'week':
        group_field = 'toStartOfWeek(sale_date)'
    elif group_by == 'month':
        group_field = 'toStartOfMonth(sale_date)'

    if aggregate_type == 'count':
        agg_func = 'count(*)'
    elif aggregate_type == 'sum':
        agg_func = 'sum(total_amount)'
    else:
        return jsonify({"error": "Invalid aggregate_type parameter. Use 'count' or 'sum'"}), 400

    query = f"""
    SELECT {group_field} as time, {agg_func} as value
    FROM fact_sales
    WHERE product_id = toUInt64(%(product_id)s)
    AND sale_date BETWEEN %(start_date)s AND %(end_date)s
    GROUP BY time
    ORDER BY time
    """

    try:
        result = client.execute(query, {'product_id': product_id, 'start_date': start_date, 'end_date': end_date})
        formatted_result = [{"time": str(row[0]), "value": float(row[1])} for row in result]
        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error in get_aggregate: {str(e)}")
        return jsonify({"error": f"Query failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)