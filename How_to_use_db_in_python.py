import pymysql

timeout = 10
connection = pymysql.connect(
  charset="utf8mb4",
  connect_timeout=timeout,
  cursorclass=pymysql.cursors.DictCursor,
  db="phicareers",
  host="mysql-phicareers-phicareers.a.aivencloud.com",
  password="AVNS__MjBOcYMMK0yhk0J52T",
  read_timeout=timeout,
  port=27509,
  user="avnadmin",
  write_timeout=timeout,
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM jobs")  # Imports the jobs table
result_all = cursor.fetchall()  # Fetches complete table
first_result = result_all[0]
print(type(cursor))
print(type(result_all))
print(type(first_result))
print(result_all[0]['location'])
connection.close()