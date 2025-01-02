import psycopg2

class PostgresConnectionSingleton:
    _instance = None
    _conn = None

    @staticmethod
    def get_instance():
        if PostgresConnectionSingleton._instance is None:
            PostgresConnectionSingleton._instance = PostgresConnectionSingleton()
        return PostgresConnectionSingleton._instance

    def __init__(self):
        if PostgresConnectionSingleton._conn is None:
            try:
                PostgresConnectionSingleton._conn = psycopg2.connect(
                    host="db.logologee.com",
                    port=5555,
                    database="shop01",
                    user="postgres",
                    password="logologi"
                )
                print("Kết nối thành công tới PostgreSQL")
            except Exception as e:
                print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
                exit(1)

    def execute_query(self, query, params):
        try:
            with PostgresConnectionSingleton._conn.cursor() as cur:  # Use context manager for cursor
                cur.execute(query, params)
                return cur.fetchall()  # Return only the query result
        except Exception as e:
            print(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}")
            return None

    def close(self, cursor=None):
        if cursor:
            cursor.close()
        if PostgresConnectionSingleton._conn:
            PostgresConnectionSingleton._conn.close()
            print("Đã đóng kết nối tới cơ sở dữ liệu.")
            
    @staticmethod        
    def test_db_connection(db_instance):
        try:
            # Thực hiện một truy vấn đơn giản để kiểm tra kết nối
            query = "SELECT 1"
            result = db_instance.execute_query(query, ())  # Không cần tham số vì query chỉ kiểm tra kết nối
            if result:
                print("Kết nối cơ sở dữ liệu thành công!")
                return True
            else:
                print("Kết nối cơ sở dữ liệu không thành công.")
                return False
        except Exception as e:
            print(f"Lỗi khi kiểm tra kết nối cơ sở dữ liệu: {e}")
            return False
