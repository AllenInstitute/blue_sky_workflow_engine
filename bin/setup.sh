source activate /conda_envs/py_37
export DEBUG_LOG=/home/blue_sky_user/work/logs/management.log
python -m workflow_engine.management.manage migrate
python -m workflow_engine.management.manage collectstatic --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('blue_sky_user', 'no@example.com', 'blue_sky_user')" | python -m workflow_engine.management.manage shell
python -m workflow_engine.management.manage import_workflows /home/blue_sky_user/work/workflow_config.yml
restart_workers.sh blue_sky /home/blue_sky_user/work