# wait-for-it.sh
#!/bin/bash
# wait-for-it.sh

set -e

host="$1"
shift
cmd="$@"

until mysql -h"$host" -P3306 -uroot -p"$MYSQL_PASSWORD" -e 'SELECT 1;' > /dev/null 2>&1; do
  echo "MySQL is unavailable - sleeping"
  sleep 1
done

echo "MySQL is up - executing command"
exec $cmd