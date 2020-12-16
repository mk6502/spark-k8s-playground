from datetime import timedelta

from airflow import DAG
from airflow.utils.dates import days_ago
from operators.spark_kubernetes_operator import SparkKubernetesOperator
from operators.spark_kubernetes_sensor import SparkKubernetesSensor
import yaml


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
}


spark_application_yaml = """
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: will_be_replaced
  namespace: default
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: "gcr.io/spark-operator/spark-py:v3.0.0"
  imagePullPolicy: Always
  mainApplicationFile: local:///opt/spark/examples/src/main/python/pi.py
  sparkVersion: 3.0.0
  restartPolicy:
    type: Never
  driver:
    cores: 1
    memory: 1g
    labels:
      version: 3.0.0
    serviceAccount: spark
  executor:
    cores: 1
    instances: 2
    memory: "512m"
    labels:
      version: 3.0.0
"""
spark_application_dict = yaml.safe_load(spark_application_yaml)
spark_application_name = "pyspark-pi3-{{ ds }}-{{ task_instance.try_number }}"
spark_application_dict['metadata']['name'] = spark_application_name

dag = DAG(
    'spark_pi',
    default_args=default_args,
    description='pyspark-pi kubernetes',
    schedule_interval=None,
)

t1 = SparkKubernetesOperator(
    task_id='spark_pi_submit',
    namespace="default",
    sparkapplication_object=spark_application_dict,
    dag=dag,
)

t2 = SparkKubernetesSensor(
    task_id='spark_pi_monitor',
    namespace="default",
    sparkapplication_name=spark_application_name,
    dag=dag
)
t1 >> t2
