# spark-k8s-playground
PySpark on k8s using Airflow.

## Why k8s?

* Don't rely on EMR versions, bootstrap, packages, etc.
* Don't have to pay the EMR management fee.
* Don't have to wait 10 minutes for EMR to spin up.
* Don't need to worry about cluster size - just specify the executor memory, number of executors, and driver memory.
* Autoscaling. EKS should be able to add and remove physical nodes as required.

## Process
Set up a fresh k8s with `minikube`:

    minikube start

Next, install Helm. This tool is used to install `spark-on-k8s-operator` on the k8s cluster:

    # from https://helm.sh/docs/intro/install/
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
    chmod 700 get_helm.sh
    ./get_helm.sh
    rm ./get_helm.sh

Next, install `spark-on-k8s-operator` on the k8s cluster using:

    helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
    helm install my-release spark-operator/spark-operator --namespace default

Now, create a service account and give it permissions:

    kubectl create serviceaccount spark
    kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark --namespace=default

Now you can start the `minikube` dashboard with:

    minikube dashboard

Next, I installed Apache Airflow locally:

    # follow this quick start:
    https://airflow.apache.org/docs/apache-airflow/stable/start.html

    mkdir -p ~/airflow/dags ~/airflow/plugins

Next, grab `roitvt`'s Spark k8s operator, hook, and k8s hook. This has been merged into Airflow 2.0.0,
but as of right now I'm using airflow 1.14.

    cd ~/airflow/plugins
    mkdir operators
    cd operators
    touch __init__.py
    wget https://raw.githubusercontent.com/roitvt/airflow-spark-on-k8s-operator/master/operators/kubernetes_hook.py
    wget https://raw.githubusercontent.com/roitvt/airflow-spark-on-k8s-operator/master/operators/spark_kubernetes_operator.py
    wget https://raw.githubusercontent.com/roitvt/airflow-spark-on-k8s-operator/master/operators/spark_kubernetes_sensor.py

Now, copy in the DAG:

    cp dag.py ~/airflow/dags/

Fire up the Airflow webserver and scheduler:

    airflow webserver -p 8080
    airflow scheduler

Give it a few minutes to find the DAG, then trigger it. You should be able to see the application running in k8s!
The logs will show an approximation of the value of Pi.

## Other Notes
### Questions
* How can I access the Spark UI?
* Want to build a custom image with a longer-running process.
* Want to try this on EKS or some other managed k8s, not just `minikube`.

### Building a custom Docker image:

Run the following from inside `SPARK_HOME`:

    eval $(minikube docker-env) # makes the built image accessible from docker inside minikube
    ./bin/docker-image-tool.sh -r s8 -t latest build
    ./bin/docker-image-tool.sh -r s8 -t latest -p ./kubernetes/dockerfiles/spark/bindings/python/Dockerfile build

## Resources
* https://minikube.sigs.k8s.io/docs/start/
* https://issues.apache.org/jira/browse/AIRFLOW-6542
* https://github.com/roitvt/airflow-spark-on-k8s-operator
* https://github.com/GoogleCloudPlatform/spark-on-k8s-operator/blob/master/docs/quick-start-guide.md
* https://spark.apache.org/docs/latest/running-on-kubernetes.html#docker-images
